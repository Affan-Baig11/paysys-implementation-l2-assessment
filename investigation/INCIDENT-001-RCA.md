# INCIDENT-001 – Intermittent Transaction Search Failure

## Summary

A transaction search returned HTTP 500 for a payment in `PROCESSING` status. This defect was deliberately introduced to reproduce the incident, as required by the assessment.

## Observations and reproduction

- Before introducing the defect, searching for `TXN-INCIDENT-20261028` returned HTTP 200 with status `PROCESSING` and `completed_at: null`.
- I deliberately changed the response code to call `row[6].isoformat()` without checking whether the timestamp was present.
- Searching for that processing payment then returned HTTP 500.
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

`completed_at` is nullable because a payment may still be processing. Calling `.isoformat()` on its `None` value raised an `AttributeError`, which caused the HTTP 500 response.

## Immediate corrective action

Changed the response code to format the timestamp only when it exists:

    "completed_at": row[6].isoformat() if row[6] is not None else None,

## Permanent corrective and preventive action

Keep nullable database fields nullable in API responses and check a value before calling date methods on it. Add regression coverage for searches of both processing and completed payments.

## Validation after the fix

- The processing payment search returned HTTP 200 with `completed_at: null`.
- The successful payment search returned HTTP 200 with a completion timestamp.
- `python -m pytest -q tests/api` reported `6 passed, 8 warnings`. The warnings were deprecations from the installed Starlette and FastAPI versions.
