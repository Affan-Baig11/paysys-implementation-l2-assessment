# Query performance investigation

## Access pattern

The API and support workflow search by transaction_ref. The supplied schema deliberately starts without an index on this column, while the data generator creates 50,000 rows and includes duplicate references. A unique constraint would reject valid assessment seed data, so the safe first change is a non-unique btree index.

## Reproduce with the supplied data

Follow the separate-database seed procedure in README.md. It keeps the demo API database intact and ensures the generated callback transaction IDs align with the clean assessment database.

Before indexing, run:

    docker compose exec -T db psql -U minipay -d minipay_assessment < sql/explain_search.sql

Save the actual EXPLAIN ANALYZE output in this file or in evidence/search-before.txt. Then apply the indexes and capture the plan again:

    docker compose exec -T db psql -U minipay -d minipay_assessment < sql/indexes.sql
    docker compose exec -T db psql -U minipay -d minipay_assessment < sql/explain_search.sql

## Expected change

Before the index, PostgreSQL should consider a sequential scan of transactions. After the index and ANALYZE, it can use idx_transactions_ref for the equality lookup. The planner may still choose a sequential scan for a small table or a query expected to return many rows. Record the actual plan, execution time, rows, and buffers from this environment; do not copy illustrative numbers from another machine.

## Indexes added

- transactions(transaction_ref): direct search.
- transactions(status, created_at): old PROCESSING transactions.
- transactions(customer_id, created_at DESC): customer payment history.
- callbacks(transaction_id, callback_status): callback reconciliation.

The transaction reference index remains non-unique because duplicate references are deliberately planted. Clean duplicates before considering a uniqueness constraint.
