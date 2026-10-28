import os
import sys
import time
import uuid
from pathlib import Path

import requests
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from api import main

BASE_URL = os.getenv("MINIPAY_API_URL", "http://localhost:8080")
API_KEY = os.getenv("MINIPAY_API_KEY", "dev-api-key")
HEADERS = {"X-API-Key": API_KEY}


def create_customer():
    response = requests.post(
        f"{BASE_URL}/api/customers",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"customer_ref": f"TEST-{uuid.uuid4().hex[:16]}", "name": "API Test Customer"},
        timeout=5,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_health_is_fast_and_reports_database():
    started = time.perf_counter()
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert time.perf_counter() - started < 2.0


def test_customer_requires_key_and_duplicate_ref_conflicts():
    payload = {"customer_ref": f"TEST-{uuid.uuid4().hex[:16]}", "name": "API Test"}
    assert requests.post(f"{BASE_URL}/api/customers", json=payload, timeout=5).status_code == 401
    created = requests.post(f"{BASE_URL}/api/customers", headers=HEADERS, json=payload, timeout=5)
    assert created.status_code == 201
    assert requests.post(f"{BASE_URL}/api/customers", headers=HEADERS, json=payload, timeout=5).status_code == 409


def test_validation_and_unknown_resources():
    invalid = requests.post(
        f"{BASE_URL}/api/payments",
        headers={**HEADERS, "Idempotency-Key": "invalid-payload"},
        json={"customer_id": 1}, timeout=5,
    )
    assert invalid.status_code == 422
    unknown_customer = requests.post(
        f"{BASE_URL}/api/payments",
        headers={**HEADERS, "Idempotency-Key": "missing-customer"},
        json={"customer_id": 99999999, "amount": "1.00"}, timeout=5,
    )
    assert unknown_customer.status_code == 404
    assert requests.get(f"{BASE_URL}/api/payments/TXN-DOES-NOT-EXIST", timeout=5).status_code == 404


def test_payment_idempotency_lookup_and_customer_history():
    customer = create_customer()
    key = f"api-test-{uuid.uuid4().hex}"
    headers = {**HEADERS, "Idempotency-Key": key}
    payload = {"customer_id": customer["id"], "amount": "12.50"}
    first = requests.post(f"{BASE_URL}/api/payments", headers=headers, json=payload, timeout=5)
    retry = requests.post(f"{BASE_URL}/api/payments", headers=headers, json=payload, timeout=5)
    assert first.status_code == retry.status_code == 201
    assert first.json()["id"] == retry.json()["id"]
    assert first.json()["transaction_ref"] == retry.json()["transaction_ref"]
    assert first.json()["amount"] == "12.50"
    assert first.json()["status"] == "SUCCESS"

    changed = requests.post(
        f"{BASE_URL}/api/payments", headers=headers,
        json={"customer_id": customer["id"], "amount": "13.50"}, timeout=5,
    )
    assert changed.status_code == 409
    detail = requests.get(f"{BASE_URL}/api/payments/{first.json()['transaction_ref']}", timeout=5)
    assert detail.status_code == 200
    assert detail.json()["callbacks"][0]["status"] == "SUCCESS"
    assert detail.json()["customer"]["customer_ref"] == customer["customer_ref"]
    history = requests.get(f"{BASE_URL}/api/customers/{customer['id']}/payments", timeout=5)
    assert history.status_code == 200
    assert any(item["id"] == first.json()["id"] for item in history.json()["items"])


def test_health_reports_unavailable_database(monkeypatch):
    from fastapi import HTTPException

    def unavailable():
        raise HTTPException(status_code=503, detail="Database unavailable")

    monkeypatch.setattr(main, "connect", unavailable)
    response = TestClient(main.app).get("/health")
    assert response.status_code == 503


class _FakeQueryResult:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class _PendingPaymentConnection:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, _params):
        if "JOIN customers" in query:
            return _FakeQueryResult(row=(
                15, "TXN-INCIDENT-20261028", 1, "1000.00", "PROCESSING",
                "2026-10-28T11:30:00", None, None, "CUST-DEMO-001", "Demo Customer",
            ))
        if "FROM callbacks" in query:
            return _FakeQueryResult(rows=[])
        raise AssertionError(f"Unexpected query: {query}")


def test_processing_payment_lookup_keeps_null_completion_time(monkeypatch):
    monkeypatch.setattr(main, "connect", _PendingPaymentConnection)
    response = TestClient(main.app).get("/api/payments/TXN-INCIDENT-20261028")

    assert response.status_code == 200
    assert response.json()["status"] == "PROCESSING"
    assert response.json()["completed_at"] is None
    assert response.json()["callbacks"] == []

def test_homepage_serves_operator_ui():
    response = TestClient(main.app).get("/")
    assert response.status_code == 200
    assert "MiniPay Operations" in response.text
