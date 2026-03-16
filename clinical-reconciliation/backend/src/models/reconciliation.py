"""Models for medication reconciliation."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class MedicationSource(BaseModel):
    """A single medication source (EHR, pharmacy, patient-reported, etc.)."""

    system: str = Field(..., description="Source system identifier (e.g. 'ehr', 'pharmacy')")
    medication: str = Field(..., description="Medication name or description")
    last_updated: datetime = Field(..., description="When this record was last updated")
    source_reliability: Literal["high", "medium", "low"] = Field(
        ..., description="Reliability tier of the source"
    )
    last_filled: Optional[datetime] = Field(
        default=None,
        description="Last pharmacy fill date (for pharmacy sources)",
    )


class PatientContext(BaseModel):
    """Clinical context for the patient (age, conditions, labs)."""

    age: Optional[int] = Field(default=None, description="Patient age in years")
    conditions: list[str] = Field(
        default_factory=list,
        description="Active conditions (e.g. diabetes, CKD)",
    )
    recent_labs: Optional[dict[str, float]] = Field(
        default=None,
        description="Recent lab values, e.g. {'eGFR': 45.0}",
    )


class ReconcileRequest(BaseModel):
    """Request payload for medication reconciliation."""

    patient_context: PatientContext = Field(..., description="Patient clinical context")
    sources: list[MedicationSource] = Field(
        ...,
        description="Medication sources to reconcile",
        min_length=1,
    )


class ReconcileResponse(BaseModel):
    """Response from medication reconciliation."""

    reconciled_medication: str = Field(..., description="Final reconciled medication")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the reconciliation (0–1)",
    )
    reasoning: str = Field(..., description="Human-readable reasoning")
    recommended_actions: list[str] = Field(
        default_factory=list,
        description="Recommended follow-up actions",
    )
    clinical_safety_check: str = Field(
        ...,
        description="Clinical safety assessment",
    )
