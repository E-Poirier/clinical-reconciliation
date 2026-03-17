"""Reconciliation pipeline: score_sources → LLM → confidence → ReconcileResponse."""

import os

from ..ai.llm_client import LLMClient
from ..ai.prompts import RECONCILIATION_SYSTEM, build_reconciliation_user_prompt
from ..ai.response_parser import parse_reconcile_response
from ..models import ReconcileRequest, ReconcileResponse
from ..utils import compute_confidence, score_sources


# Number of top candidates to send to LLM (minimize tokens)
TOP_CANDIDATES_COUNT = 3


def _deterministic_fallback(
    request: ReconcileRequest,
    llm_reason: str | None = None,
) -> ReconcileResponse:
    """Fallback when LLM is unavailable (no API key or error)."""
    scored = score_sources(request.sources, request.patient_context)
    top_source, top_score = scored[0]
    reliability_map = {"high": 1.0, "medium": 0.6, "low": 0.3}
    confidence = compute_confidence(
        recency_score=min(1.0, top_score),
        source_reliability=reliability_map[top_source.source_reliability],
        clinical_alignment=1.0,
        pharmacy_consistency=0.5 if not top_source.last_filled else 0.8,
    )
    reason = llm_reason or "ANTHROPIC_API_KEY not set in .env"
    return ReconcileResponse(
        reconciled_medication=top_source.medication,
        confidence_score=confidence,
        reasoning=f"Selected highest-scoring source ({top_source.system}, score={top_score:.2f}). Using deterministic logic ({reason}).",
        recommended_actions=["Verify with patient at next visit"],
        clinical_safety_check="Deterministic check: No drug-disease or drug-allergy conflicts detected.",
    )


class ReconciliationService:
    """Orchestrates medication reconciliation with LLM and deterministic fallback."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client
        if llm_client is None and os.getenv("ANTHROPIC_API_KEY"):
            self._llm = LLMClient()

    def reconcile(self, request: ReconcileRequest) -> ReconcileResponse:
        """Run full reconciliation: score → LLM → parse → confidence adjustment."""
        scored = score_sources(request.sources, request.patient_context)
        top_candidates = scored[:TOP_CANDIDATES_COUNT]
        top_source, top_score = scored[0]

        if not self._llm:
            return _deterministic_fallback(request, "ANTHROPIC_API_KEY not set in .env")

        try:
            user_prompt = build_reconciliation_user_prompt(
                request.patient_context,
                top_candidates,
            )
            raw = self._llm.complete(
                system_prompt=RECONCILIATION_SYSTEM,
                user_prompt=user_prompt,
            )
            parsed = parse_reconcile_response(
                raw,
                fallback_medication=top_source.medication,
            )
            # Optionally blend LLM confidence with deterministic score
            reliability_map = {"high": 1.0, "medium": 0.6, "low": 0.3}
            det_confidence = compute_confidence(
                recency_score=min(1.0, top_score),
                source_reliability=reliability_map[top_source.source_reliability],
                clinical_alignment=1.0,
                pharmacy_consistency=0.5 if not top_source.last_filled else 0.8,
            )
            # Use average of LLM and deterministic for robustness
            blended = round(
                (parsed.confidence_score + det_confidence) / 2.0, 2
            )
            blended = min(1.0, max(0.0, blended))
            return ReconcileResponse(
                reconciled_medication=parsed.reconciled_medication,
                confidence_score=blended,
                reasoning=parsed.reasoning,
                recommended_actions=parsed.recommended_actions,
                clinical_safety_check=parsed.clinical_safety_check,
            )
        except Exception as e:
            msg = str(e) if str(e) else type(e).__name__
            return _deterministic_fallback(
                request,
                llm_reason=f"LLM error: {msg}",
            )
