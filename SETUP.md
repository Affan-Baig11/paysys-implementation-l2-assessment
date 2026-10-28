# MiniPay API and database

## Run locally with Docker Compose

1. Copy .env.example to .env and change both local development values.
2. Start the database and API with docker compose up --build.
3. Check http://localhost:8080/health and open http://localhost:8080/docs.
4. Stop with docker compose down. Add -v only when you intentionally want to delete the local database volume.

The database schema is applied automatically when PostgreSQL initializes its empty data volume. If you change the schema after the first startup, use a migration or recreate the local volume only if its data can be discarded.

## API

- POST /api/customers creates a customer.
- POST /api/payments creates a payment; send an Idempotency-Key header.
- GET /api/payments/{transaction_ref} returns the payment and callback history.
- GET /api/customers/{id}/payments lists recent customer payments.
- GET /health checks the API and database.

Write requests require the X-API-Key header. For the local example, its value is dev-api-key; change it in .env before use. Amounts must be positive. Development credentials must never be reused in a deployed environment.
