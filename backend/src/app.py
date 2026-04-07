"""FastAPI application for the Clinical Data Reconciliation Engine."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from .models import DataQualityRequest, DataQualityResponse, ReconcileRequest, ReconcileResponse
from .services import ReconciliationService, ValidationService

# Same backend/.env as main.py; must run before service singletons below read ANTHROPIC_API_KEY / API_KEY.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

API_KEY_HEADER = APIKeyHeader(name="x-api-key", auto_error=False)


def validate_api_key(api_key: str | None = Depends(API_KEY_HEADER)) -> str:
    """Require a valid ``x-api-key`` matching the ``API_KEY`` environment variable."""
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
async def lifespan(app: FastAPI):
    """Reserved for startup/shutdown hooks (DB pools, etc.); currently a no-op."""
    yield


app = FastAPI(
    title="Clinical Data Reconciliation Engine",
    description="EHR integration for medication reconciliation and data quality validation",
    version="0.1.0",
    lifespan=lifespan,
)

router = APIRouter(prefix="/api", tags=["api"])

reconciliation_service = ReconciliationService()
validation_service = ValidationService()


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
    return reconciliation_service.reconcile(request)


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
    return validation_service.validate(request)


app.include_router(router)


@app.get("/health")
async def health():
    """Health check; no auth. Use to verify API_KEY and ANTHROPIC_API_KEY are loaded in Docker."""
    return {
        "status": "ok",
        "api_key_configured": bool(os.getenv("API_KEY")),
        "anthropic_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Serialize ``HTTPException`` as JSON with a ``detail`` field for consistent clients."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
