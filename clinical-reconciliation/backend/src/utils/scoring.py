"""Deterministic scoring for medication sources before LLM reconciliation.

Weights (per PLAN.md):
- Recency: 35% — newer data is more trustworthy
- Source reliability: 25% — high/medium/low tier
- Clinical alignment: 25% — e.g. low eGFR flags high Metformin dose
- Pharmacy fill: 15% — recent fill is strong signal
"""

import math
from datetime import datetime
from typing import Literal

from ..models import MedicationSource, PatientContext


# Days considered "fresh" (full score); beyond this, score decays
RECENCY_HALF_LIFE_DAYS = 30

# Source reliability weights
RELIABILITY_WEIGHTS: dict[str, float] = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.3,
}

# eGFR threshold below which Metformin may need dose adjustment (CKD)
EGFR_METFORMIN_THRESHOLD = 30


def _recency_score(last_updated: datetime) -> float:
    """Normalize recency: 0–1 based on days since last_updated."""
    days_ago = (datetime.now() - last_updated.replace(tzinfo=None)).days
    if days_ago <= 0:
        return 1.0
    # Exponential decay: score halves every RECENCY_HALF_LIFE_DAYS
    return max(0.0, min(1.0, math.exp(-0.693 * days_ago / RECENCY_HALF_LIFE_DAYS)))


def _reliability_score(source_reliability: Literal["high", "medium", "low"]) -> float:
    """Map source reliability to 0–1."""
    return RELIABILITY_WEIGHTS.get(source_reliability, 0.3)


def _clinical_alignment_score(
    source: MedicationSource,
    patient_context: PatientContext,
) -> float:
    """Score clinical alignment (e.g. low eGFR + high Metformin dose → lower score)."""
    base = 1.0
    if not patient_context.recent_labs or "eGFR" not in patient_context.recent_labs:
        return base

    egfr = patient_context.recent_labs["eGFR"]
    med_lower = source.medication.lower()

    # Metformin contraindicated or needs dose adjustment when eGFR < 30
    if "metformin" in med_lower and egfr < EGFR_METFORMIN_THRESHOLD:
        # High dose (e.g. 1000mg BID) in low eGFR = poor alignment
        if "1000" in med_lower or "2000" in med_lower:
            return 0.3
        # Lower dose may be acceptable
        return 0.6

    return base


def _pharmacy_fill_score(source: MedicationSource) -> float:
    """Score based on recent pharmacy fill (15% weight)."""
    if not source.last_filled:
        return 0.5  # No fill data = neutral
    days_since_fill = (datetime.now() - source.last_filled.replace(tzinfo=None)).days
    if days_since_fill <= 7:
        return 1.0
    if days_since_fill <= 30:
        return 0.8
    if days_since_fill <= 90:
        return 0.5
    return 0.2


def score_sources(
    sources: list[MedicationSource],
    patient_context: PatientContext,
) -> list[tuple[MedicationSource, float]]:
    """Score each source and return list of (source, score) sorted by score descending."""
    scored: list[tuple[MedicationSource, float]] = []
    for s in sources:
        recency = _recency_score(s.last_updated)
        reliability = _reliability_score(s.source_reliability)
        clinical = _clinical_alignment_score(s, patient_context)
        pharmacy = _pharmacy_fill_score(s)
        raw = recency * 0.35 + reliability * 0.25 + clinical * 0.25 + pharmacy * 0.15
        total = round(min(max(raw, 0.0), 1.0), 2)
        scored.append((s, total))
    return sorted(scored, key=lambda x: x[1], reverse=True)
