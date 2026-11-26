"""SQLAlchemy engine and safe connectivity probe."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def create_database_engine() -> Engine:
    """Create a pooled SQLAlchemy engine using validated local settings."""
    settings = get_settings()
    return create_engine(settings.sqlalchemy_url, pool_pre_ping=True)


@lru_cache
def get_engine() -> Engine:
    """Create the shared engine on first database use."""
    return create_database_engine()


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Return the shared SQLAlchemy session factory."""
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db_session() -> Iterator[Session]:
    """Yield a request-scoped session and always close it after use.

    This dependency deliberately does not commit. Domain operations own their
    transaction boundaries and must commit or roll back explicitly.
    """
    with get_session_factory()() as session:
        yield session


def check_database_connection() -> None:
    """Run a minimal read-only statement to verify database availability."""
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))


def dispose_database_engine() -> None:
    """Close the shared connection pool and clear cached database factories."""
    engine = get_engine() if get_engine.cache_info().currsize else None
    get_session_factory.cache_clear()
    get_engine.cache_clear()
    if engine is not None:
        engine.dispose()
