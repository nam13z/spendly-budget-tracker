"""SQLAlchemy engine and safe connectivity probe."""

from functools import lru_cache

from sqlalchemy import Engine, create_engine, text

from app.core.config import get_settings


def create_database_engine() -> Engine:
    """Create a pooled SQLAlchemy engine using validated local settings."""
    settings = get_settings()
    return create_engine(settings.sqlalchemy_url, pool_pre_ping=True)


@lru_cache
def get_engine() -> Engine:
    """Create the shared engine on first database use."""
    return create_database_engine()


def check_database_connection() -> None:
    """Run a minimal read-only statement to verify database availability."""
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))
