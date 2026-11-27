"""Tests for safe engine disposal and request-scoped session cleanup."""

from collections.abc import Iterator

from fastapi.testclient import TestClient

from app.db import connection
from app.main import create_app


def test_application_lifespan_disposes_cached_engine(monkeypatch) -> None:
    class FakeEngine:
        disposed = False

        def dispose(self) -> None:
            self.disposed = True

    engine = FakeEngine()
    connection.get_session_factory.cache_clear()
    connection.get_engine.cache_clear()
    monkeypatch.setattr(connection, "create_database_engine", lambda: engine)

    assert connection.get_engine() is engine
    connection.get_session_factory()

    with TestClient(create_app()):
        pass

    assert engine.disposed
    assert connection.get_engine.cache_info().currsize == 0
    assert connection.get_session_factory.cache_info().currsize == 0


def test_request_session_dependency_closes_session(monkeypatch) -> None:
    class FakeSession:
        entered = False
        exited = False

        def __enter__(self) -> FakeSession:
            self.entered = True
            return self

        def __exit__(self, *_: object) -> None:
            self.exited = True

    session = FakeSession()
    monkeypatch.setattr(connection, "get_session_factory", lambda: lambda: session)

    dependency: Iterator[object] = connection.get_db_session()
    assert next(dependency) is session
    dependency.close()

    assert session.entered
    assert session.exited


def test_reusable_database_fixture_is_isolated(db_session) -> None:
    from sqlalchemy import text

    assert db_session.execute(text("SELECT 1")).scalar_one() == 1
