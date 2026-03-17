"""Adapter mapping PyHealth Patient/Event data to Pydantic models."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from ..models import (
    DataQualityRequest,
    MedicationSource,
    PatientContext,
    ReconcileRequest,
)

if TYPE_CHECKING:
    from pyhealth.data import Event, Patient


def _get_timestamp(obj: Any) -> datetime:
    """Extract timestamp from Event or dict; fallback to now."""
    if hasattr(obj, "timestamp") and obj.timestamp:
        return obj.timestamp
    if isinstance(obj, dict) and "timestamp" in obj:
        ts = obj["timestamp"]
        return ts if isinstance(ts, datetime) else datetime.now()
    return datetime.now()


def _get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Get attribute from Event.attr_dict or dict."""
    if hasattr(obj, "attr_dict") and isinstance(obj.attr_dict, dict):
        return obj.attr_dict.get(key, default)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def event_to_medication_source(
    event: "Event | dict",
    system: str = "pyhealth",
    source_reliability: str = "medium",
) -> MedicationSource:
    """Map a PyHealth Event (prescription) to MedicationSource."""
    code = event.code if hasattr(event, "code") else event.get("code", "Unknown")
    ts = _get_timestamp(event)
    last_filled = _get_attr(event, "last_filled") or _get_attr(event, "fill_date")
    if last_filled and not isinstance(last_filled, datetime):
        last_filled = None

    return MedicationSource(
        system=system,
        medication=str(code),
        last_updated=ts,
        source_reliability=source_reliability,
        last_filled=last_filled,
    )


def patient_to_context(
    patient: "Patient | dict",
    conditions: Optional[list[str]] = None,
    recent_labs: Optional[dict[str, float]] = None,
) -> PatientContext:
    """Map a PyHealth Patient to PatientContext."""
    age = None
    if hasattr(patient, "attr_dict") and patient.attr_dict:
        age = patient.attr_dict.get("age") or patient.attr_dict.get("birth_year")
    elif isinstance(patient, dict):
        age = patient.get("age") or patient.get("birth_year")

    return PatientContext(
        age=int(age) if age is not None else None,
        conditions=conditions or [],
        recent_labs=recent_labs,
    )


class PyHealthAdapter:
    """
    Adapter for converting PyHealth Patient and Event data to reconciliation models.

    Use with PyHealth datasets (e.g. MIMIC-III, OMOP) or assignment-provided EHR data
    that follows similar structure.
    """

    @staticmethod
    def to_reconcile_request(
        patient: "Patient | dict",
        medication_events: list["Event | dict"],
        conditions: Optional[list[str]] = None,
        recent_labs: Optional[dict[str, float]] = None,
        system: str = "pyhealth",
        source_reliability: str = "medium",
    ) -> ReconcileRequest:
        """Build ReconcileRequest from Patient and medication events."""
        context = patient_to_context(patient, conditions, recent_labs)
        sources = [
            event_to_medication_source(e, system, source_reliability)
            for e in medication_events
        ]
        if not sources:
            raise ValueError("At least one medication source is required")
        return ReconcileRequest(patient_context=context, sources=sources)

    @staticmethod
    def to_data_quality_request(
        patient: "Patient | dict",
        demographics: Optional[dict[str, Any]] = None,
        medications: Optional[list[Any]] = None,
        allergies: Optional[list[Any]] = None,
        conditions: Optional[list[Any]] = None,
        vital_signs: Optional[dict[str, Any]] = None,
        last_updated: Optional[datetime] = None,
    ) -> DataQualityRequest:
        """Build DataQualityRequest from Patient and optional overrides."""
        if demographics is None and hasattr(patient, "attr_dict"):
            demographics = dict(patient.attr_dict) if patient.attr_dict else {}
        elif demographics is None and isinstance(patient, dict):
            demographics = {k: v for k, v in patient.items() if k not in ("events", "visits")}

        return DataQualityRequest(
            demographics=demographics,
            medications=medications,
            allergies=allergies,
            conditions=conditions,
            vital_signs=vital_signs,
            last_updated=last_updated,
        )
