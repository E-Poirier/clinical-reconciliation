"""Sample test data for development and testing.

Use with PyHealth adapter or direct API calls.
"""

from datetime import datetime, timedelta

# Sample ReconcileRequest for testing POST /api/reconcile/medication
SAMPLE_RECONCILE_REQUEST = {
    "patient_context": {
        "age": 65,
        "conditions": ["Type 2 Diabetes", "Chronic Kidney Disease Stage 3"],
        "recent_labs": {"eGFR": 45.0},
    },
    "sources": [
        {
            "system": "ehr",
            "medication": "Metformin 500mg BID",
            "last_updated": (datetime.now() - timedelta(days=5)).isoformat(),
            "source_reliability": "high",
        },
        {
            "system": "pharmacy",
            "medication": "Metformin 500mg twice daily",
            "last_updated": (datetime.now() - timedelta(days=2)).isoformat(),
            "source_reliability": "high",
            "last_filled": (datetime.now() - timedelta(days=2)).isoformat(),
        },
    ],
}

# Sample DataQualityRequest for testing POST /api/validate/data-quality
SAMPLE_DATA_QUALITY_REQUEST = {
    "demographics": {"age": 72, "gender": "F"},
    "medications": ["Lisinopril 10mg", "Metformin 500mg"],
    "allergies": [],  # Empty - should trigger "incomplete" issue
    "conditions": ["Hypertension", "Type 2 Diabetes"],
    "vital_signs": {"systolic_bp": 340, "diastolic_bp": 180, "heart_rate": 88},
    "last_updated": (datetime.now() - timedelta(days=200)).isoformat(),
}
