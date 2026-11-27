"""Privacy-conscious structured logging for application request events."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

_SAFE_FIELDS = ("request_id", "method", "route", "status_code", "duration_ms")
_SAFE_EVENTS = {"request_completed", "request_failed"}
app_logger = logging.getLogger("spendly")


class JsonLogFormatter(logging.Formatter):
    """Serialize an allowlist of fields; never serialize arbitrary log messages."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname.lower(),
            "logger": record.name,
        }
        event = getattr(record, "event", None)
        payload["event"] = (
            event if isinstance(event, str) and event in _SAFE_EVENTS else "application_event"
        )
        for field in _SAFE_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=True)


def configure_logging() -> None:
    """Configure one JSON stream handler for safe Spendly application events."""
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False
    if any(getattr(handler, "_spendly_json_handler", False) for handler in app_logger.handlers):
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonLogFormatter())
    handler._spendly_json_handler = True  # type: ignore[attr-defined]
    app_logger.addHandler(handler)
