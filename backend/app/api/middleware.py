"""Request metadata and safe error boundaries for the HTTP API."""

from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from app.api.errors import internal_error_handler
from app.core.logging_config import app_logger


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) else "unmatched"


async def request_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
    """Set a generated request ID, redact failures, and log safe request metadata."""
    request_id = str(uuid4())
    request.state.request_id = request_id
    started = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exception:
        response = await internal_error_handler(request, exception)
        status_code = response.status_code
    response.headers["X-Request-ID"] = request_id
    app_logger.info(
        "request_completed",
        extra={
            "event": "request_completed",
            "request_id": request_id,
            "method": request.method,
            "route": _route_template(request),
            "status_code": status_code,
            "duration_ms": round((perf_counter() - started) * 1000, 2),
        },
    )
    return response
