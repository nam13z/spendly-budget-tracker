"""Tests that structured request logs exclude raw request and exception data."""

import json
import logging
from io import StringIO

from fastapi.testclient import TestClient

from app.core.logging_config import JsonLogFormatter, app_logger
from app.main import create_app


def test_json_formatter_uses_only_allowlisted_fields() -> None:
    record = logging.LogRecord(
        name="spendly",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="synthetic-secret-in-message",
        args=(),
        exc_info=None,
    )
    record.event = "request_completed"
    record.request_id = "synthetic-request-id"
    record.route = "/health/live"
    record.status_code = 200

    output = JsonLogFormatter().format(record)
    payload = json.loads(output)

    assert payload["event"] == "request_completed"
    assert payload["request_id"] == "synthetic-request-id"
    assert payload["route"] == "/health/live"
    assert "synthetic-secret-in-message" not in output


def test_request_log_uses_route_template_and_omits_query_values() -> None:
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonLogFormatter())
    app_logger.addHandler(handler)
    try:
        with TestClient(create_app()) as client:
            response = client.get("/health/live?token=synthetic-private-token")
    finally:
        app_logger.removeHandler(handler)
        handler.close()

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    records = [json.loads(line) for line in output.getvalue().splitlines()]
    request_record = next(item for item in records if item["event"] == "request_completed")
    assert request_record["route"] == "/health/live"
    assert request_record["method"] == "GET"
    assert "synthetic-private-token" not in output.getvalue()


def test_request_failure_log_omits_exception_text() -> None:
    output = StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(JsonLogFormatter())
    app_logger.addHandler(handler)
    application = create_app()

    @application.get("/_test/logged-failure")
    def failure_endpoint() -> None:
        raise RuntimeError("synthetic-private-exception")

    try:
        with TestClient(application) as client:
            response = client.get("/_test/logged-failure")
    finally:
        app_logger.removeHandler(handler)
        handler.close()

    assert response.status_code == 500
    assert "synthetic-private-exception" not in output.getvalue()
    assert any(
        json.loads(line)["event"] == "request_failed" for line in output.getvalue().splitlines()
    )
