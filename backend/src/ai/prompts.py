"""Prompt templates for clinical reconciliation and data quality.

Prompt engineering approach (document in README):
- System prompt provides role, constraints, and output format
- User prompt contains structured patient/source data
- JSON output requested for parse reliability
- Minimal tokens for data quality: only send flagged fields
"""

import json
from typing import Any

from ..models import MedicationSource, PatientContext
from ..models.data_quality import IssueDetected


# --- Reconciliation ---

RECONCILIATION_SYSTEM = """You are a clinical pharmacist assisting with medication reconciliation. 
Given patient context and medication sources from multiple systems (EHR, pharmacy, etc.), choose the best reconciled medication and provide clinical reasoning.

Output ONLY valid JSON with these exact keys:
- reconciled_medication (string): The final medication name/dose to use
- confidence_score (float 0-1): Your confidence in this choice
- reasoning (string): Brief human-readable explanation
- recommended_actions (array of strings): Follow-up actions (e.g. "Verify with patient at next visit")
- clinical_safety_check (string): Drug-disease, drug-allergy, or dose concerns (or "None identified" if clear)

Do not include markdown or code fences. Output raw JSON only."""


def build_reconciliation_user_prompt(
    patient_context: PatientContext,
    top_candidates: list[tuple[MedicationSource, float]],
) -> str:
    """Build user prompt for medication reconciliation."""
    ctx_lines = [
        f"Age: {patient_context.age}",
        f"Conditions: {', '.join(patient_context.conditions) or 'None'}",
    ]
    if patient_context.recent_labs:
        ctx_lines.append(f"Recent labs: {json.dumps(patient_context.recent_labs)}")

    sources_text = []
    for i, (src, score) in enumerate(top_candidates, 1):
        sources_text.append(
            f"{i}. {src.system}: {src.medication} "
            f"(last_updated: {src.last_updated}, reliability: {src.source_reliability}"
            + (f", last_filled: {src.last_filled}" if src.last_filled else "")
            + f", score: {score:.2f})"
        )

    return f"""Patient context:
{chr(10).join(ctx_lines)}

Medication sources (sorted by score):
{chr(10).join(sources_text)}

Reconcile to a single best medication. Output JSON only."""


# --- Data Quality (Plausibility) ---

DATA_QUALITY_SYSTEM = """You are a clinical data quality analyst. Given a flagged field and its value, assess whether it is clinically plausible for the patient's conditions.

Output ONLY valid JSON with these exact keys:
- plausible (boolean): true if the value seems clinically reasonable, false if implausible
- reasoning (string): Brief explanation
- suggested_severity (string): "low", "medium", or "high" - severity of the issue if implausible

Do not include markdown or code fences. Output raw JSON only."""


def build_data_quality_user_prompt(
    field: str,
    value: Any,
    conditions: list[str],
) -> str:
    """Build minimal user prompt for data quality plausibility check."""
    conditions_str = ", ".join(conditions) if conditions else "no documented conditions"
    return f"""Field: {field}
Value: {json.dumps(value, default=str)}
Patient conditions: {conditions_str}

Is this value clinically plausible? Output JSON only."""


def build_batch_data_quality_prompt(
    flagged_issues: list[IssueDetected],
    conditions: list[str],
) -> str:
    """Build a single prompt for multiple flagged fields (minimize tokens)."""
    items = [
        f"- {i.field}: {i.issue} (current severity: {i.severity})"
        for i in flagged_issues
    ]
    conditions_str = ", ".join(conditions) if conditions else "no documented conditions"
    return f"""Patient conditions: {conditions_str}

Flagged fields for plausibility review:
{chr(10).join(items)}

For each flagged field, is the value clinically plausible? Output a JSON array with one object per field:
[{{"field": "field_name", "plausible": true/false, "reasoning": "...", "suggested_severity": "low|medium|high"}}]

Match the order of fields above. Output raw JSON only."""
