# MiniPay architecture

MiniPay is a small support-assessment application composed of a browser operator UI, a FastAPI REST service, and PostgreSQL. Docker Compose runs the API and database locally. PostgreSQL stores customers, transactions, and callback attempts. The API uses parameterized SQL and checks database readiness before traffic is accepted.

The UI supports API-key sign-in, customer creation, payment submission, and payment lookup. A local mock processor completes valid test payments and records a successful callback; it does not contact a real payment provider or move money. Invalid requests return API validation errors.

The API separates customer creation, payment submission, transaction lookup, customer payment history, and health checks. Payment submission accepts an idempotency key so a client retry returns the original payment rather than creating a second one.

The separate minipay_assessment PostgreSQL database is used for generated 50,000-row SQL investigations. This keeps demo UI records independent from seeded reporting data.

The same API and database will be containerized for Kubernetes. Secrets are supplied through environment configuration; only development placeholders are checked into Git.
