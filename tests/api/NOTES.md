# API test notes

Run with the application started using Docker Compose:

    python -m pip install -r tests/api/requirements.txt
    pytest -q tests/api

The suite uses MINIPAY_API_URL (default http://localhost:8080) and MINIPAY_API_KEY (default dev-api-key).

For payment integrations, set a client timeout appropriate to the operation. A timeout leaves the outcome unknown because the server may have accepted the request before the response was lost. Retry using the same idempotency key. Retry transient connection failures and selected 5xx responses with bounded exponential backoff and jitter. Do not retry ordinary 4xx validation or authorization errors without correcting the request or credentials. Keep retries bounded and idempotent.
