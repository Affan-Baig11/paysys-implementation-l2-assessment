# INCIDENT-001 – Intermittent Transaction Search Failure

## Summary

A transaction search returned HTTP 500 for a payment in `PROCESSING` status. This defect was deliberately introduced to reproduce the incident, as required by the assessment.

## Observations and reproduction

- Before introducing the defect, searching for `TXN-INCIDENT-20261028` returned HTTP 200 with status `PROCESSING` and `completed_at: null`.
- I deliberately changed the response code to call `row[6].isoformat()` without checking whether the timestamp was present.
- Then searching for that processing payment then returned HTTP 500.
- A completed payment had a timestamp, so its search still worked.

Reproduction command:

    curl -i http://localhost:8080/api/payments/TXN-INCIDENT-20261028

## Evidence gathered

- The database contained transaction ID 15, reference `TXN-INCIDENT-20261028`, status `PROCESSING`, with no `completed_at` value.
- The API traceback showed: `AttributeError: 'NoneType' object has no attribute 'isoformat'`.
- After the fix, searches for both the processing payment and successful payment `TXN67D991F53394` returned HTTP 200.
- After the fix, the API test suite reported `6 passed, 8 warnings`.

## Hypotheses considered

- The reference did not exist. That would return HTTP 404; the transaction was present.
- The database was unavailable. Health checks returned HTTP 200.
- The lookup query or index failed. The traceback showed the error occurred while formatting the response.
- The completion timestamp was null and formatted as a date. The traceback confirmed this.

## Root cause

`completed_at` is nullable because a payment can still be processing. Calling `.isoformat()` on its `None` value raised an `AttributeError`, which caused the HTTP 500 response.

## Immediate corrective action

Changed the response code to format the timestamp only when it exists:

    "completed_at": row[6].isoformat() if row[6] is not None else None,

## Permanent corrective and preventive action

Keep nullable database fields nullable in API responses and check a value before calling date methods on it. `tests/api/test_api.py` now includes a regression case for a `PROCESSING` payment with `completed_at: null`; the existing successful-payment lookup test covers a non-null completion timestamp.

## Validation after the fix

- The processing payment search returned HTTP 200 with `completed_at: null`.
- The successful payment search returned HTTP 200 with a completion timestamp.
- The original API run reported `6 passed, 8 warnings` before the focused regression test was added.
- After adding `test_processing_payment_lookup_keeps_null_completion_time`, the final combined run `python -m pytest -q tests/api tests/python` reported `15 passed, 8 warnings` (7 API tests and 8 Python utility tests). The warnings were Starlette/FastAPI deprecations.
