"""FastAPI application for Clinical Data Reconciliation Engine."""

import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from .models import DataQualityRequest, DataQualityResponse, ReconcileRequest, ReconcileResponse
from .models.data_quality import IssueDetected, QualityBreakdown

API_KEY_HEADER = APIKeyHeader(name="x-api-key", auto_error=False)


def validate_api_key(api_key: str | None = Depends(API_KEY_HEADER)) -> str:
    """Validate API key against environment variable."""
    expected = os.getenv("API_KEY")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured",
        )
    if not api_key or api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key


@asynccontextmanager
async def lifespan(app):
    """Application lifespan handler."""
    yield


app = FastAPI(
    title="Clinical Data Reconciliation Engine",
    description="EHR integration for medication reconciliation and data quality validation",
    version="0.1.0",
    lifespan=lifespan,
)

router = APIRouter(prefix="/api", tags=["api"])


@router.post(
    "/reconcile/medication",
    response_model=ReconcileResponse,
    summary="Reconcile medication from multiple sources",
)
async def reconcile_medication(
    request: ReconcileRequest,
    _: str = Depends(validate_api_key),
) -> ReconcileResponse:
    """Reconcile medication list from multiple sources (EHR, pharmacy, etc.)."""
    # Mock response for Phase 1
    top_source = max(
        request.sources,
        key=lambda s: (s.source_reliability == "high", s.last_updated),
    )
    return ReconcileResponse(
        reconciled_medication=top_source.medication,
        confidence_score=0.85,
        reasoning="Mock: Selected highest-reliability source with most recent update.",
        recommended_actions=["Verify with patient at next visit"],
        clinical_safety_check="Mock: No drug-disease or drug-allergy conflicts detected.",
    )


@router.post(
    "/validate/data-quality",
    response_model=DataQualityResponse,
    summary="Validate data quality",
)
async def validate_data_quality(
    request: DataQualityRequest,
    _: str = Depends(validate_api_key),
) -> DataQualityResponse:
    """Validate data quality across demographics, medications, allergies, conditions, vitals."""
    # Mock response for Phase 1
    issues: list[IssueDetected] = []
    completeness = 70
    accuracy = 80
    timeliness = 75
    clinical_plausibility = 85

    if request.allergies is not None and len(request.allergies) == 0:
        issues.append(
            IssueDetected(
                field="allergies",
                issue="No allergies documented - likely incomplete",
                severity="medium",
            )
        )
        completeness = 65

    overall = int(
        (completeness * 0.25 + accuracy * 0.25 + timeliness * 0.25 + clinical_plausibility * 0.25)
    )
    return DataQualityResponse(
        overall_score=min(100, overall),
        breakdown=QualityBreakdown(
            completeness=completeness,
            accuracy=accuracy,
            timeliness=timeliness,
            clinical_plausibility=clinical_plausibility,
        ),
        issues_detected=issues,
    )


app.include_router(router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Ensure structured error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
