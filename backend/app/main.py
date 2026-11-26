"""Spendly FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import register_error_handlers
from app.api.health import router as health_router
from app.api.middleware import request_middleware
from app.core.logging_config import configure_logging
from app.db.connection import dispose_database_engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Dispose the process-wide SQLAlchemy pool after request handling stops."""
    try:
        yield
    finally:
        dispose_database_engine()


def create_app() -> FastAPI:
    """Build the API with shared error, logging, and resource lifecycle behavior."""
    configure_logging()
    application = FastAPI(title="Spendly API", version="0.1.0", lifespan=lifespan)
    application.middleware("http")(request_middleware)
    register_error_handlers(application)
    application.include_router(health_router)
    return application


app = create_app()
