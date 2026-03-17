"""Confidence score calculation for reconciliation results.

Weights (per PLAN.md):
- recency: 35%
- source_reliability: 25%
- clinical_alignment: 25%
- pharmacy_consistency: 15%

Rationale: Recency dominates because medication lists change frequently;
source reliability reflects system trust; clinical alignment catches
drug-disease mismatches; pharmacy fill confirms patient adherence.
"""


def compute_confidence(
    recency_score: float,
    source_reliability: float,
    clinical_alignment: float,
    pharmacy_consistency: float,
) -> float:
    """Compute weighted confidence score, clamped to [0, 1].

    Args:
        recency_score: 0–1, how recent the data is
        source_reliability: 0–1, reliability of the source
        clinical_alignment: 0–1, alignment with patient context
        pharmacy_consistency: 0–1, consistency with pharmacy fill data

    Returns:
        Confidence score in [0, 1], rounded to 2 decimal places
    """
    raw = (
        recency_score * 0.35
        + source_reliability * 0.25
        + clinical_alignment * 0.25
        + pharmacy_consistency * 0.15
    )
    return round(min(max(raw, 0.0), 1.0), 2)
