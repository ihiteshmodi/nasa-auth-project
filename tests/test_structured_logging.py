import json
import logging

from fastapi.testclient import TestClient

from app.infrastructure.logging import JsonLogFormatter, clear_request_id, set_request_id
from app.interfaces.main import create_app


def test_json_formatter_emits_structured_payload_and_redacts_sensitive_fields() -> None:
    formatter = JsonLogFormatter(service_name="nasa-auth-project", environment="test")
    set_request_id("req-123")

    record = logging.LogRecord(
        name="tests.structured",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="sample_event",
        args=(),
        exc_info=None,
    )
    record.password = "super-secret"
    record.metadata = {"api_key": "DEMO", "attempt": 1}

    try:
        payload = json.loads(formatter.format(record))
    finally:
        clear_request_id()

    assert payload["message"] == "sample_event"
    assert payload["service"] == "nasa-auth-project"
    assert payload["environment"] == "test"
    assert payload["request_id"] == "req-123"
    assert payload["password"] == "[REDACTED]"
    assert payload["metadata"]["api_key"] == "[REDACTED]"
    assert payload["metadata"]["attempt"] == 1


def test_request_middleware_adds_request_id_and_logs_lifecycle(caplog) -> None:
    app = create_app()

    with caplog.at_level(logging.INFO):
        with TestClient(app) as client:
            response = client.get("/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers

    messages = [record.msg for record in caplog.records]
    assert "request_start" in messages
    assert "request_complete" in messages
