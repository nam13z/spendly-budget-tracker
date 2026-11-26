"""Reusable isolated fixtures for API and database foundation tests."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.main import app


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[Settings]:
    """Provide deterministic settings without consulting the developer's .env."""
    values = {
        "APP_ENV": "test",
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "3307",
        "DB_NAME": "spendly_test",
        "DB_USER": "spendly_test",
        "DB_PASSWORD": "synthetic-test-password",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    yield Settings(_env_file=None)


@pytest.fixture
def db_engine() -> Iterator[Engine]:
    """Create a disposable in-memory SQLite engine for isolated persistence tests."""
    engine = create_engine("sqlite+pysqlite:///:memory:", pool_pre_ping=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Iterator[Session]:
    """Yield a test session that always closes and never commits implicitly."""
    factory = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        yield session


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Run the shared application with its lifespan in a test client context."""
    with TestClient(app) as test_client:
        yield test_client
