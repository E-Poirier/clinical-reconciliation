"""Data quality pipeline: rule-based checks → LLM on flagged fields → DataQualityResponse."""

import os
from datetime import datetime

from ..ai.llm_client import LLMClient
from ..ai.prompts import (
    DATA_QUALITY_SYSTEM,
    build_batch_data_quality_prompt,
)
from ..ai.response_parser import parse_data_quality_plausibility
from ..models import DataQualityRequest, DataQualityResponse
from ..models.data_quality import IssueDetected, QualityBreakdown
from ..validators import run_clinical_rules


def _compute_breakdown_from_issues(
    issues: list[IssueDetected],
    last_updated: datetime | None,
) -> QualityBreakdown:
    """Compute dimension scores from issues and last_updated.
    Multiple high-severity issues drive the score lower (2+ high = Poor)."""
    completeness = 70
    accuracy = 80
    timeliness = 75
    clinical_plausibility = 85

    high_count = sum(1 for i in issues if i.severity == "high")
    medium_count = sum(1 for i in issues if i.severity == "medium")

    if last_updated:
        days_ago = (datetime.now() - last_updated.replace(tzinfo=None)).days
        if days_ago > 180:
            timeliness = min(timeliness, 50)
        elif days_ago > 90:
            timeliness = min(timeliness, 65)

    for i in issues:
        if i.severity == "high":
            completeness = min(completeness, 50)
            accuracy = min(accuracy, 50)
            clinical_plausibility = min(clinical_plausibility, 50)
        elif i.severity == "medium":
            completeness = min(completeness, 65)
            accuracy = min(accuracy, 70)
            if "last_updated" in i.field:
                timeliness = min(timeliness, 65)
            if "allergies" in i.field:
                completeness = min(completeness, 60)
        elif i.severity == "low":
            completeness = min(completeness, 80)
            accuracy = min(accuracy, 85)

    # 2+ high-severity issues = data is unreliable; cap all dimensions lower
    if high_count >= 2:
        completeness = min(completeness, 35)
        accuracy = min(accuracy, 35)
        timeliness = min(timeliness, 35)
        clinical_plausibility = min(clinical_plausibility, 35)
    elif high_count >= 1:
        completeness = min(completeness, 45)
        accuracy = min(accuracy, 45)
        clinical_plausibility = min(clinical_plausibility, 45)

    return QualityBreakdown(
        completeness=max(0, completeness),
        accuracy=max(0, accuracy),
        timeliness=max(0, timeliness),
        clinical_plausibility=max(0, clinical_plausibility),
    )


class ValidationService:
    """Orchestrates data quality validation with rules and LLM plausibility checks."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client
        if llm_client is None and os.getenv("ANTHROPIC_API_KEY"):
            self._llm = LLMClient()

    def validate(self, request: DataQualityRequest) -> DataQualityResponse:
        """Run rule-based checks, optionally enhance with LLM plausibility."""
        issues = run_clinical_rules(
            demographics=request.demographics,
            vital_signs=request.vital_signs,
            allergies=request.allergies,
            last_updated=request.last_updated,
        )

        # If LLM available and we have flagged issues, ask for plausibility
        if self._llm and issues:
            conditions = []
            if request.conditions:
                conditions = [
                    str(c) if not isinstance(c, dict) else str(c.get("name", c))
                    for c in request.conditions
                ]
            try:
                user_prompt = build_batch_data_quality_prompt(issues, conditions)
                raw = self._llm.complete(
                    system_prompt=DATA_QUALITY_SYSTEM,
                    user_prompt=user_prompt,
                    max_tokens=1024,
                )
                plausibility = parse_data_quality_plausibility(raw)
                # Merge: if LLM says implausible, keep or elevate severity
                for i, p in enumerate(plausibility):
                    if i < len(issues) and not p.get("plausible", True):
                        # LLM confirms implausible - could elevate severity
                        suggested = p.get("suggested_severity", "medium")
                        if suggested in ("high", "medium", "low"):
                            issues[i] = IssueDetected(
                                field=issues[i].field,
                                issue=f"{issues[i].issue} [LLM: {p.get('reasoning', '')}]",
                                severity=suggested,
                            )
            except Exception:
                pass  # Use rule-based issues only

        breakdown = _compute_breakdown_from_issues(
            issues,
            request.last_updated,
        )
        overall = int(
            (
                breakdown.completeness * 0.25
                + breakdown.accuracy * 0.25
                + breakdown.timeliness * 0.25
                + breakdown.clinical_plausibility * 0.25
            )
        )
        overall = min(100, max(0, overall))

        return DataQualityResponse(
            overall_score=overall,
            breakdown=breakdown,
            issues_detected=issues,
        )
