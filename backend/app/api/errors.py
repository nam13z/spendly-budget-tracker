"""Stable API error responses without reflecting untrusted or internal details."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging_config import app_logger


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unavailable")


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    request_id = _request_id(request)
    return JSONResponse(
        status_code=status_code,
        headers={"X-Request-ID": request_id},
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
                "request_id": request_id,
            }
        },
    )


async def validation_error_handler(
    request: Request, exception: RequestValidationError
) -> JSONResponse:
    """Return validation locations and codes, never invalid values or raw messages."""
    details: list[dict[str, Any]] = []
    for error in exception.errors():
        location = [
            part if isinstance(part, (str, int)) else "unknown" for part in error.get("loc", ())
        ]
        details.append({"location": location, "code": str(error.get("type", "invalid"))})
    return _error_response(
        request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="The request could not be processed.",
        details=details,
    )


async def http_error_handler(request: Request, exception: StarletteHTTPException) -> JSONResponse:
    """Map HTTP failures to stable codes without returning exception details."""
    codes = {
        400: ("BAD_REQUEST", "The request could not be processed."),
        401: ("AUTH_REQUIRED", "Authentication is required."),
        403: ("FORBIDDEN", "The requested action is not allowed."),
        404: ("NOT_FOUND", "The requested resource was not found."),
        409: ("CONFLICT", "The request conflicts with the current resource state."),
        422: ("VALIDATION_ERROR", "The request could not be processed."),
    }
    code, message = codes.get(
        exception.status_code,
        ("HTTP_ERROR", "The request could not be processed."),
    )
    return _error_response(
        request,
        status_code=exception.status_code,
        code=code,
        message=message,
    )


async def internal_error_handler(request: Request, exception: Exception) -> JSONResponse:
    """Return a generic server error and log only a safe event and request ID."""
    del exception
    app_logger.error(
        "request_failed",
        extra={"event": "request_failed", "request_id": _request_id(request)},
    )
    return _error_response(
        request,
        status_code=500,
        code="INTERNAL_ERROR",
        message="An internal error occurred.",
    )


def register_error_handlers(application: FastAPI) -> None:
    """Register the API's stable validation, HTTP, and internal error handlers."""
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.add_exception_handler(StarletteHTTPException, http_error_handler)
    application.add_exception_handler(Exception, internal_error_handler)
