"""Tests for liveness and readiness endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api import health


def test_liveness_does_not_require_database(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_returns_ready_when_database_check_succeeds(
    monkeypatch, client: TestClient
) -> None:
    monkeypatch.setattr(health, "check_database_connection", lambda: None)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_returns_generic_unavailable_on_database_error(
    monkeypatch, client: TestClient
) -> None:
    def fail_connection() -> None:
        raise OperationalError("connect", {}, Exception("private detail"))

    monkeypatch.setattr(health, "check_database_connection", fail_connection)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "private detail" not in response.text
