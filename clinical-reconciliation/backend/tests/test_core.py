"""Unit tests for core logic (Phase 2 — assignment: ≥5 tests)."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.ai.response_parser import parse_reconcile_response
from src.app import app
from src.models import MedicationSource, PatientContext
from src.utils import compute_confidence, score_sources
from src.validators import run_clinical_rules


def test_reconciliation_prefers_recent_source() -> None:
    """Scoring prefers newer last_updated."""
    now = datetime.now()
    old = MedicationSource(
        system="ehr",
        medication="Metformin 500mg",
        last_updated=now - timedelta(days=60),
        source_reliability="high",
    )
    recent = MedicationSource(
        system="pharmacy",
        medication="Metformin 500mg BID",
        last_updated=now - timedelta(days=2),
        source_reliability="high",
        last_filled=now - timedelta(days=2),
    )
    ctx = PatientContext(age=65, conditions=[], recent_labs=None)
    scored = score_sources([old, recent], ctx)
    assert scored[0][0].system == "pharmacy"
    assert scored[0][1] > scored[1][1]


def test_implausible_blood_pressure_detected() -> None:
    """340/180 BP → high severity issue."""
    issues = run_clinical_rules(
        demographics=None,
        vital_signs={"systolic_bp": 340, "diastolic_bp": 180, "heart_rate": 88},
        allergies=None,
        last_updated=None,
    )
    bp_issues = [i for i in issues if "blood_pressure" in i.field]
    assert len(bp_issues) >= 1
    assert bp_issues[0].severity == "high"
    assert "340" in bp_issues[0].issue or "180" in bp_issues[0].issue


def test_confidence_score_clamped_to_bounds() -> None:
    """Confidence score stays in [0, 1]."""
    assert compute_confidence(0, 0, 0, 0) == 0.0
    assert compute_confidence(1, 1, 1, 1) == 1.0
    assert compute_confidence(2, 2, 2, 2) == 1.0
    assert compute_confidence(-1, -1, -1, -1) == 0.0
    c = compute_confidence(0.5, 0.5, 0.5, 0.5)
    assert 0 <= c <= 1


def test_missing_allergies_flagged() -> None:
    """Empty allergies → medium severity."""
    issues = run_clinical_rules(
        demographics=None,
        vital_signs=None,
        allergies=[],
        last_updated=None,
    )
    allergy_issues = [i for i in issues if i.field == "allergies"]
    assert len(allergy_issues) == 1
    assert allergy_issues[0].severity == "medium"
    assert "incomplete" in allergy_issues[0].issue.lower()


def test_api_rejects_missing_key() -> None:
    """401 without x-api-key header."""
    client = TestClient(app)
    response = client.post(
        "/api/reconcile/medication",
        json={
            "patient_context": {"age": 65, "conditions": [], "recent_labs": None},
            "sources": [
                {
                    "system": "ehr",
                    "medication": "Metformin",
                    "last_updated": datetime.now().isoformat(),
                    "source_reliability": "high",
                }
            ],
        },
    )
    assert response.status_code == 401


def test_llm_response_parser_handles_malformed_json() -> None:
    """Parser returns fallback when JSON is malformed."""
    result = parse_reconcile_response("not valid json {{{", fallback_medication="Fallback Med")
    assert result.reconciled_medication == "Fallback Med"
    assert result.confidence_score == 0.0
    assert "malformed" in result.reasoning.lower()


def test_reconcile_endpoint_returns_valid_response() -> None:
    """Reconcile endpoint returns valid response with API key (deterministic when no LLM key)."""
    client = TestClient(app)
    response = client.post(
        "/api/reconcile/medication",
        json={
            "patient_context": {"age": 65, "conditions": [], "recent_labs": None},
            "sources": [
                {
                    "system": "ehr",
                    "medication": "Metformin 500mg",
                    "last_updated": datetime.now().isoformat(),
                    "source_reliability": "high",
                }
            ],
        },
        headers={"x-api-key": "test-key-123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "reconciled_medication" in data
    assert "confidence_score" in data
    assert 0 <= data["confidence_score"] <= 1
    assert "reasoning" in data
    assert "clinical_safety_check" in data
