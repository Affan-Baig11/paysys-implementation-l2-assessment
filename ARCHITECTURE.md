# MiniPay architecture

MiniPay is a small support-assessment application composed of a FastAPI REST service and PostgreSQL. Docker Compose runs both services locally. PostgreSQL stores customers, transactions, and callback attempts. The API uses parameterized SQL and checks database readiness before accepting traffic.

The API separates customer creation, payment submission, transaction lookup, customer payment history, and health checks. Payment submission accepts an idempotency key so a client retry can return the original payment rather than create a second one.

The same API and database will be containerized for Kubernetes. Secrets are supplied through environment configuration; only development placeholders are checked into Git. The browser UI and support CLI will use the API rather than accessing database credentials directly.
