"""Service liveness and database readiness routes."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.db.connection import check_database_connection

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def liveness() -> dict[str, str]:
    """Report that the API process can serve requests."""
    return {"status": "ok"}


@router.get("/ready")
def readiness() -> dict[str, str] | JSONResponse:
    """Report readiness only when the configured MySQL server responds."""
    try:
        check_database_connection()
    except (SQLAlchemyError, ValidationError):
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ready"}
