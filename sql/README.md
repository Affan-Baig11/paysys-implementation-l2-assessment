# SQL investigation

All seven reports target the PostgreSQL schema in database/schema.sql. To avoid changing the small demo database used by the API, the commands below create a separate minipay_assessment database in the Compose PostgreSQL container. Run the create/load sequence once.

From the repository root:

    docker compose exec -T db psql -U minipay -d postgres -c "CREATE DATABASE minipay_assessment;"
    docker compose exec -T db psql -U minipay -d minipay_assessment < database/schema.sql
    python3 database/generate_data.py > seed.sql
    docker compose exec -T db psql -v ON_ERROR_STOP=1 -U minipay -d minipay_assessment < seed.sql

The generated seed.sql is ignored by Git. The assessment database starts empty, so the generator's callback transaction IDs match inserted transaction IDs. The existing MiniPay demo database is left untouched.

Run any report from the repository root, for example:

    docker compose exec -T db psql -U minipay -d minipay_assessment < sql/01_tx_count_value_by_status_day.sql

Run reports 01 through 07 to answer the assignment questions. Report 06 counts a transaction once if it has one or more successful callback attempts, so retries do not inflate reconciled value.

For INCIDENT-003, first capture the plan before the index, apply sql/indexes.sql, then capture the plan again:

    docker compose exec -T db psql -U minipay -d minipay_assessment < sql/explain_search.sql
    docker compose exec -T db psql -U minipay -d minipay_assessment < sql/indexes.sql
    docker compose exec -T db psql -U minipay -d minipay_assessment < sql/explain_search.sql

See PERFORMANCE.md for how to record the observed plans and timings. Do not claim expected performance numbers as measured results.
