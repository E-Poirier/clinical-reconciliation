"""Rule-based clinical checks for data quality validation.

Per PLAN.md:
- BP: systolic > 250 or diastolic > 150 → high severity
- Heart rate: > 250 or < 20 → high severity
- Age: < 0 or > 130 → invalid
- last_updated > 180 days → stale (medium)
- allergies == [] → incomplete (medium)
"""

from datetime import datetime
from typing import Any

from ..models.data_quality import IssueDetected


def run_clinical_rules(
    demographics: dict[str, Any] | None,
    vital_signs: dict[str, Any] | None,
    allergies: list[Any] | None,
    last_updated: datetime | None,
) -> list[IssueDetected]:
    """Run rule-based checks and return list of detected issues."""
    issues: list[IssueDetected] = []

    # Age: < 0 or > 130 → invalid
    if demographics and "age" in demographics:
        age = demographics["age"]
        if isinstance(age, (int, float)):
            if age < 0 or age > 130:
                issues.append(
                    IssueDetected(
                        field="demographics.age",
                        issue=f"Age {age} is outside valid range (0–130)",
                        severity="high",
                    )
                )

    # BP: systolic > 250 or diastolic > 150 → high severity (e.g. 340/180)
    if vital_signs:
        systolic = vital_signs.get("systolic_bp")
        diastolic = vital_signs.get("diastolic_bp")
        if (
            isinstance(systolic, (int, float))
            and isinstance(diastolic, (int, float))
            and (systolic > 250 or diastolic > 150)
        ):
            issues.append(
                IssueDetected(
                    field="vital_signs.blood_pressure",
                    issue=f"Blood pressure {systolic}/{diastolic} is implausible",
                    severity="high",
                )
            )

        # Heart rate: > 250 or < 20 → high severity
        hr = vital_signs.get("heart_rate")
        if isinstance(hr, (int, float)):
            if hr > 250 or hr < 20:
                issues.append(
                    IssueDetected(
                        field="vital_signs.heart_rate",
                        issue=f"Heart rate {hr} is outside plausible range (20–250 bpm)",
                        severity="high",
                    )
                )

    # last_updated > 180 days → stale (medium)
    if last_updated:
        days_ago = (datetime.now() - last_updated.replace(tzinfo=None)).days
        if days_ago > 180:
            issues.append(
                IssueDetected(
                    field="last_updated",
                    issue=f"Data is 7+ months old ({days_ago} days)",
                    severity="medium",
                )
            )

    # allergies == [] → incomplete (medium)
    if allergies is not None and len(allergies) == 0:
        issues.append(
            IssueDetected(
                field="allergies",
                issue="No allergies documented - likely incomplete",
                severity="medium",
            )
        )

    return issues
