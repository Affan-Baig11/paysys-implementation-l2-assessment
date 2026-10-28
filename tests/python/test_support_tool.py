import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python"))
from support_tool import (  # noqa: E402
    EXIT_NOT_FOUND,
    EXIT_TRANSPORT,
    EXIT_UPSTREAM,
    MiniPayClient,
    SupportToolError,
    diagnose_transaction,
    format_report,
)


@pytest.fixture
def now():
    return datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)


def tx(**overrides):
    value = {
        "id": 123,
        "transaction_ref": "TXN000123",
        "customer_id": 9,
        "amount": "42.50",
        "status": "SUCCESS",
        "created_at": "2026-10-28T11:30:00",
        "completed_at": "2026-10-28T11:30:02",
        "failure_code": None,
        "customer": {"customer_ref": "CUST000009", "name": "Test Customer"},
        "callbacks": [{"attempt_no": 1, "http_status": 200, "status": "SUCCESS",
                       "attempted_at": "2026-10-28T11:30:02"}],
    }
    value.update(overrides)
    return value


def test_successful_transaction_has_no_anomalies_and_formats_report(now):
    report = diagnose_transaction(tx(), now=now)
    assert report["anomalies"] == []
    assert report["callback_attempt_count"] == 1
    assert report["age_minutes"] == 30.0
    text = format_report(report)
    assert "TXN000123" in text
    assert "Test Customer" in text
    assert "42.50" in text
    assert "successful 1" in text


def test_stale_processing_without_callbacks_recommends_reconciliation(now):
    report = diagnose_transaction(
        tx(status="PROCESSING", completed_at=None, callbacks=[]), now=now
    )
    assert report["age_minutes"] == 30.0
    assert any("15-minute support threshold" in issue for issue in report["anomalies"])
    assert any("No callback attempts" in issue for issue in report["anomalies"])
    assert "Reconcile before any retry" in report["recommended_next_action"]


def test_failed_transaction_includes_failure_code_and_safe_retry_advice(now):
    report = diagnose_transaction(
        tx(status="FAILED", failure_code="DECLINED", completed_at="2026-10-28T11:31:00",
           callbacks=[{"attempt_no": 1, "http_status": 500, "status": "FAILED"}]), now=now
    )
    assert any("DECLINED" in issue for issue in report["anomalies"])
    assert report["failed_callback_count"] == 1
    assert "original idempotency key" in report["recommended_next_action"]


def test_success_without_successful_callback_is_flagged(now):
    report = diagnose_transaction(
        tx(callbacks=[{"attempt_no": 1, "http_status": 500, "status": "FAILED"}]), now=now
    )
    assert any("No successful callback" in issue for issue in report["anomalies"])
    assert "Do not resubmit" in report["recommended_next_action"]


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self.payload = payload

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.call = None

    def get(self, url, **kwargs):
        self.call = (url, kwargs)
        if self.error:
            raise self.error
        return self.response


def test_client_uses_timeout_and_api_key_and_returns_transaction():
    payload = tx()
    session = FakeSession(FakeResponse(200, payload))
    client = MiniPayClient("http://example.test/", api_key="local-test-key", timeout=2, session=session)
    assert client.get_transaction("TXN000123") == payload
    url, kwargs = session.call
    assert url == "http://example.test/api/payments/TXN000123"
    assert kwargs["timeout"] == 2
    assert kwargs["headers"] == {"X-API-Key": "local-test-key"}


def test_client_maps_not_found_timeout_and_server_error():
    with pytest.raises(SupportToolError) as missing:
        MiniPayClient("http://api", session=FakeSession(FakeResponse(404, {}))).get_transaction("TXN404")
    assert missing.value.exit_code == EXIT_NOT_FOUND

    with pytest.raises(SupportToolError) as timed_out:
        MiniPayClient("http://api", session=FakeSession(error=requests.Timeout())).get_transaction("TXN")
    assert timed_out.value.exit_code == EXIT_TRANSPORT

    with pytest.raises(SupportToolError) as upstream:
        MiniPayClient("http://api", session=FakeSession(FakeResponse(503, {}))).get_transaction("TXN")
    assert upstream.value.exit_code == EXIT_UPSTREAM


def test_client_rejects_malformed_api_json():
    response = FakeResponse(200, ValueError("bad json"))
    with pytest.raises(SupportToolError, match="invalid JSON"):
        MiniPayClient("http://api", session=FakeSession(response)).health()


def test_client_rejects_nonpositive_timeout():
    with pytest.raises(ValueError, match="positive"):
        MiniPayClient("http://api", timeout=0)
