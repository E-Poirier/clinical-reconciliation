"""Parse LLM JSON responses with fallback for malformed output.

- Strip markdown code fences if present
- json.loads() with try/except
- Validate against Pydantic model
- Fallback to deterministic result if malformed
"""

import json
import re
from typing import Any

from ..models import ReconcileResponse


def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers."""
    text = text.strip()
    match = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def parse_reconcile_response(
    raw: str,
    fallback_medication: str = "Unknown",
) -> ReconcileResponse:
    """Parse LLM response into ReconcileResponse. Fallback if malformed."""
    try:
        cleaned = _strip_markdown_fences(raw)
        data: dict[str, Any] = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return ReconcileResponse(
            reconciled_medication=fallback_medication,
            confidence_score=0.0,
            reasoning="LLM response was malformed; using fallback.",
            recommended_actions=["Manually verify medication list"],
            clinical_safety_check="Unable to perform safety check due to parse error.",
        )

    try:
        return ReconcileResponse(
            reconciled_medication=data.get("reconciled_medication", fallback_medication),
            confidence_score=float(data.get("confidence_score", 0.0)),
            reasoning=str(data.get("reasoning", "")),
            recommended_actions=list(data.get("recommended_actions", [])),
            clinical_safety_check=str(data.get("clinical_safety_check", "")),
        )
    except (ValueError, TypeError):
        return ReconcileResponse(
            reconciled_medication=fallback_medication,
            confidence_score=0.0,
            reasoning="LLM response validation failed; using fallback.",
            recommended_actions=["Manually verify medication list"],
            clinical_safety_check="Unable to perform safety check due to validation error.",
        )
