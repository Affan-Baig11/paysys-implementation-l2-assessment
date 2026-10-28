# MiniPay API and browser UI

## Run locally with Docker Compose

1. Copy .env.example to .env and change both local development values before sharing the environment.
2. Start the database and API with docker compose up --build.
3. Open the operator UI at http://localhost:8080 and the API docs at http://localhost:8080/docs.
4. The local demo API key is dev-api-key. Successful test payments are completed by a local mock processor; no real payment is sent.
5. Stop with Ctrl+C or docker compose down. Do not add -v unless you intentionally want to erase the database volume.

PostgreSQL applies database/schema.sql when it first initializes its empty data volume. Existing databases are not automatically migrated if the schema changes later.

## API

- POST /api/customers creates a customer.
- POST /api/payments creates a payment; send an Idempotency-Key header.
- GET /api/payments/{transaction_ref} returns the payment and callback history.
- GET /api/customers/{id}/payments lists recent customer payments.
- GET /health checks the API and database.
- GET /api/ops/health checks dependencies and requires the API key.

Write requests require X-API-Key. Amounts must be positive. Development credentials must never be reused in a deployed environment.
