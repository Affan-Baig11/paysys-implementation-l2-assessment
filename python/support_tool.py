#!/usr/bin/env python3
"""MiniPay L2 transaction diagnostic CLI."""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

import requests

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NOT_FOUND = 3
EXIT_TRANSPORT = 4
EXIT_UPSTREAM = 5


class SupportToolError(Exception):
    """Expected operational failure with a stable CLI exit code."""

    def __init__(self, message: str, *, kind: str = "error", exit_code: int = EXIT_ERROR):
        super().__init__(message)
        self.kind = kind
        self.exit_code = exit_code


class MiniPayClient:
    def __init__(self, base_url: str, *, api_key: str | None = None,
                 timeout: float = 5.0, session: Any = requests):
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session
        self.headers = {"X-API-Key": api_key} if api_key else {}

    def _get_json(self, path: str) -> tuple[int, Any]:
        try:
            response = self.session.get(
                f"{self.base_url}{path}", headers=self.headers, timeout=self.timeout
            )
        except requests.Timeout as exc:
            raise SupportToolError(
                f"Request timed out after {self.timeout:g}s", kind="timeout", exit_code=EXIT_TRANSPORT
            ) from exc
        except requests.ConnectionError as exc:
            raise SupportToolError(
                f"Could not connect to MiniPay API at {self.base_url}",
                kind="connection_error", exit_code=EXIT_TRANSPORT
            ) from exc
        except requests.RequestException as exc:
            raise SupportToolError(
                f"API request failed: {exc}", kind="request_error", exit_code=EXIT_TRANSPORT
            ) from exc

        if response.status_code == 404:
            raise SupportToolError("Transaction not found", kind="not_found", exit_code=EXIT_NOT_FOUND)
        if response.status_code >= 500:
            raise SupportToolError(
                f"MiniPay API returned HTTP {response.status_code}",
                kind="upstream_error", exit_code=EXIT_UPSTREAM
            )
        if response.status_code < 200 or response.status_code >= 300:
            raise SupportToolError(
                f"MiniPay API returned HTTP {response.status_code}",
                kind="api_error", exit_code=EXIT_ERROR
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise SupportToolError(
                "MiniPay API returned invalid JSON", kind="invalid_response", exit_code=EXIT_UPSTREAM
            ) from exc
        return response.status_code, payload

    def get_transaction(self, transaction_ref: str) -> dict[str, Any]:
        _, payload = self._get_json(f"/api/payments/{transaction_ref}")
        if not isinstance(payload, dict) or not payload.get("transaction_ref"):
            raise SupportToolError(
                "MiniPay API response is missing transaction details",
                kind="invalid_response", exit_code=EXIT_UPSTREAM
            )
        return payload

    def health(self) -> dict[str, Any]:
        _, payload = self._get_json("/health")
        if not isinstance(payload, dict):
            raise SupportToolError(
                "MiniPay health response is not a JSON object",
                kind="invalid_response", exit_code=EXIT_UPSTREAM
            )
        return payload


def _parse_timestamp(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def diagnose_transaction(transaction: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Create deterministic support findings from the API transaction response."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    status = str(transaction.get("status", "UNKNOWN")).upper()
    callbacks = sorted(transaction.get("callbacks") or [], key=lambda item: item.get("attempt_no", 0))
    customer = transaction.get("customer") or {}
    anomalies: list[str] = []
    created = _parse_timestamp(transaction.get("created_at"))
    completed = _parse_timestamp(transaction.get("completed_at"))
    age_minutes = None
    if created:
        age_minutes = max(0.0, (now - created).total_seconds() / 60)
    elif transaction.get("created_at"):
        anomalies.append("created_at is not a valid timestamp.")

    successful_callbacks = [cb for cb in callbacks if str(cb.get("status", "")).upper() == "SUCCESS"]
    failed_callbacks = [cb for cb in callbacks if str(cb.get("status", "")).upper() == "FAILED"]

    if not customer.get("customer_ref"):
        anomalies.append("Customer reference is missing from the transaction response.")
    if status in {"SUCCESS", "FAILED"} and not completed:
        anomalies.append("Final transaction status has no valid completed_at timestamp.")
    if transaction.get("failure_code"):
        anomalies.append(f"Failure code reported: {transaction['failure_code']}.")

    if status == "PROCESSING":
        if age_minutes is not None and age_minutes >= 15:
            anomalies.append(f"Transaction has remained PROCESSING for {age_minutes:.1f} minutes (15-minute support threshold).")
            next_action = "Check processor/gateway state and callback delivery. Reconcile before any retry; reuse the original idempotency key if a retry is authorized."
        else:
            next_action = "Check processor status and callback delivery, then wait through the normal processing window before escalating."
        if not callbacks:
            anomalies.append("No callback attempts are recorded.")
    elif status == "FAILED":
        if failed_callbacks:
            anomalies.append(f"{len(failed_callbacks)} callback attempt(s) failed.")
        if not callbacks:
            anomalies.append("No callback attempts are recorded.")
        next_action = "Review the failure code and callback history, then confirm ledger/reconciliation state before an authorized retry. Reuse the original idempotency key."
    elif status == "SUCCESS":
        if not successful_callbacks:
            anomalies.append("No successful callback is recorded for a successful transaction.")
            next_action = "Do not resubmit the payment. Reconcile the transaction and investigate callback delivery."
        elif failed_callbacks:
            anomalies.append(f"{len(failed_callbacks)} earlier callback attempt(s) failed before a successful callback.")
            next_action = "Payment completed and a successful callback is recorded; monitor the callback consumer and avoid resubmitting."
        else:
            next_action = "No immediate action. Keep the transaction reference for audit and verify downstream settlement as required."
    else:
        anomalies.append(f"Unrecognized transaction status: {status}.")
        next_action = "Check the API response and database state with the service owner before taking payment action."

    return {
        "transaction": transaction,
        "customer": customer,
        "callbacks": callbacks,
        "callback_attempt_count": len(callbacks),
        "successful_callback_count": len(successful_callbacks),
        "failed_callback_count": len(failed_callbacks),
        "age_minutes": round(age_minutes, 1) if age_minutes is not None else None,
        "anomalies": anomalies,
        "recommended_next_action": next_action,
    }


def format_report(report: dict[str, Any]) -> str:
    tx = report["transaction"]
    customer = report["customer"]
    lines = [
        "MiniPay L2 transaction diagnostic",
        f"Transaction: {tx.get('transaction_ref', 'unknown')} (ID {tx.get('id', 'unknown')})",
        f"Customer: {customer.get('name', 'unknown')} [{customer.get('customer_ref', 'unknown')}]",
        f"Customer ID: {tx.get('customer_id', 'unknown')}",
        f"Amount: {tx.get('amount', 'unknown')} | Status: {tx.get('status', 'unknown')}",
        f"Created: {tx.get('created_at') or 'unknown'}",
        f"Completed: {tx.get('completed_at') or 'not completed'}",
        f"Failure code: {tx.get('failure_code') or 'none'}",
        f"Callback attempts: {report['callback_attempt_count']} "
        f"(successful {report['successful_callback_count']}, failed {report['failed_callback_count']})",
    ]
    for callback in report["callbacks"]:
        lines.append(
            f"  Attempt {callback.get('attempt_no', '?')}: {callback.get('status', 'unknown')} "
            f"(HTTP {callback.get('http_status') or 'n/a'}) at {callback.get('attempted_at') or 'unknown'}"
        )
    if report["age_minutes"] is not None:
        lines.append(f"Age: {report['age_minutes']:.1f} minutes")
    lines.append("Anomalies:")
    lines.extend(f"  - {item}" for item in report["anomalies"]) if report["anomalies"] else lines.append("  None detected")
    lines.append(f"Recommended next action: {report['recommended_next_action']}")
    return "\n".join(lines)


def _positive_float(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Diagnose a MiniPay transaction for L2 support.")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--transaction", help="Transaction reference, e.g. TXN000123")
    action.add_argument("--health", action="store_true", help="Check the MiniPay API/database health endpoint")
    parser.add_argument("--json", action="store_true", help="Write machine-readable JSON")
    parser.add_argument("--timeout", type=_positive_float,
                        default=_positive_float(os.getenv("MINIPAY_TIMEOUT", "5")),
                        help="Request timeout in seconds (default: MINIPAY_TIMEOUT or 5)")
    parser.add_argument("--verbose", action="store_true", help="Log request details to stderr")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s: %(message)s")
    base_url = os.getenv("MINIPAY_API_URL", "http://127.0.0.1:8080")
    client = MiniPayClient(base_url, api_key=os.getenv("MINIPAY_API_KEY"), timeout=args.timeout)
    try:
        if args.health:
            result = client.health()
            if args.json:
                print(json.dumps({"ok": True, "health": result}, indent=2))
            else:
                print(f"API health: {result.get('status', 'unknown')}")
                print(f"Database: {result.get('database', 'unknown')}")
            return EXIT_OK

        transaction = client.get_transaction(args.transaction)
        report = diagnose_transaction(transaction)
        if args.json:
            print(json.dumps({"ok": True, **report}, indent=2, default=str))
        else:
            print(format_report(report))
        return EXIT_OK
    except SupportToolError as exc:
        logging.error("%s", exc)
        if args.json:
            print(json.dumps({"ok": False, "error": {"type": exc.kind, "message": str(exc)}}))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
