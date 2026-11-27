"""Tests for stable API error envelopes and validation-data redaction."""

from fastapi import Query
from fastapi.testclient import TestClient

from app.main import create_app


def test_not_found_uses_api_error_contract() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/missing?private_value=synthetic-private-value")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["details"] == []
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
    assert "synthetic-private-value" not in response.text


def test_validation_error_omits_rejected_values() -> None:
    application = create_app()

    @application.get("/_test/validation")
    def validation_endpoint(count: int = Query(ge=1)) -> dict[str, int]:
        return {"count": count}

    with TestClient(application) as client:
        response = client.get("/_test/validation?count=synthetic-private-value")

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"] == [{"location": ["query", "count"], "code": "int_parsing"}]
    assert error["request_id"] == response.headers["X-Request-ID"]
    assert "synthetic-private-value" not in response.text


def test_internal_error_is_generic_and_does_not_return_exception_text() -> None:
    application = create_app()

    @application.get("/_test/failure")
    def failure_endpoint() -> None:
        raise RuntimeError("synthetic-internal-secret")

    with TestClient(application) as client:
        response = client.get("/_test/failure")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert response.json()["error"]["message"] == "An internal error occurred."
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
    assert "synthetic-internal-secret" not in response.text
