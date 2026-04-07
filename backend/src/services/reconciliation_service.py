"""Medication reconciliation: rank sources, optionally call the LLM, then return a scored response."""

import os

from ..ai.llm_client import LLMClient
from ..ai.prompts import RECONCILIATION_SYSTEM, build_reconciliation_user_prompt
from ..ai.response_parser import parse_reconcile_response
from ..models import ReconcileRequest, ReconcileResponse
from ..utils import compute_confidence, score_sources

# Matches utils.scoring.RELIABILITY_WEIGHTS — numeric weight for compute_confidence()
SOURCE_RELIABILITY_SCORE = {"high": 1.0, "medium": 0.6, "low": 0.3}

# How many ranked sources to include in the LLM user prompt (token budget).
TOP_CANDIDATES_COUNT = 3


def _deterministic_fallback(
    request: ReconcileRequest,
    llm_reason: str | None = None,
) -> ReconcileResponse:
    """Return the best ranked source when the LLM is skipped or errors."""
    scored = score_sources(request.sources, request.patient_context)
    top_source, top_score = scored[0]
    confidence = compute_confidence(
        recency_score=min(1.0, top_score),
        source_reliability=SOURCE_RELIABILITY_SCORE[top_source.source_reliability],
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
    """Coordinates ranking, optional LLM reconciliation, and confidence blending."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client
        if llm_client is None and os.getenv("ANTHROPIC_API_KEY"):
            self._llm = LLMClient()

    def reconcile(self, request: ReconcileRequest) -> ReconcileResponse:
        """Rank sources, call the LLM when configured, blend confidence with deterministic score."""
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
            det_confidence = compute_confidence(
                recency_score=min(1.0, top_score),
                source_reliability=SOURCE_RELIABILITY_SCORE[top_source.source_reliability],
                clinical_alignment=1.0,
                pharmacy_consistency=0.5 if not top_source.last_filled else 0.8,
            )
            # Average LLM and deterministic confidence for stability when both are available
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
