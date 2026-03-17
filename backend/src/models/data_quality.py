"""Models for data quality validation."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class QualityBreakdown(BaseModel):
    """Breakdown of data quality dimensions."""

    completeness: int = Field(..., ge=0, le=100, description="Completeness score 0–100")
    accuracy: int = Field(..., ge=0, le=100, description="Accuracy score 0–100")
    timeliness: int = Field(..., ge=0, le=100, description="Timeliness score 0–100")
    clinical_plausibility: int = Field(
        ...,
        ge=0,
        le=100,
        description="Clinical plausibility score 0–100",
    )


class IssueDetected(BaseModel):
    """A single data quality issue."""

    field: str = Field(..., description="Field or area where issue was found")
    issue: str = Field(..., description="Description of the issue")
    severity: Literal["low", "medium", "high"] = Field(
        ...,
        description="Severity of the issue",
    )


class DataQualityRequest(BaseModel):
    """Request payload for data quality validation."""

    demographics: Optional[dict[str, Any]] = Field(
        default=None,
        description="Demographic data (age, gender, etc.)",
    )
    medications: Optional[list[Any]] = Field(
        default=None,
        description="Medication list",
    )
    allergies: Optional[list[Any]] = Field(
        default=None,
        description="Allergy list",
    )
    conditions: Optional[list[Any]] = Field(
        default=None,
        description="Conditions/diagnoses",
    )
    vital_signs: Optional[dict[str, Any]] = Field(
        default=None,
        description="Vital signs (BP, HR, etc.)",
    )
    last_updated: Optional[datetime] = Field(
        default=None,
        description="When the data was last updated",
    )


class DataQualityResponse(BaseModel):
    """Response from data quality validation."""

    overall_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall data quality score 0–100",
    )
    breakdown: QualityBreakdown = Field(
        ...,
        description="Scores per dimension",
    )
    issues_detected: list[IssueDetected] = Field(
        default_factory=list,
        description="List of detected issues",
    )
