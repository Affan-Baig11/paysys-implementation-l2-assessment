# INCIDENT-003 – Transaction Search Performance

## Summary

The reported multi-second delay was not reproduced on this WSL/Docker environment with the assessment target of 50,000 transactions. The access plan did expose the scaling problem: searching by `transaction_ref` used a sequential scan of the whole table. A non-unique B-tree index changed the plan to an index scan and reduced the measured execution time in the recorded run.

## Dataset and reproduction

Seeded the separate `minipay_assessment` database, leaving the demo API database intact. Observed counts were 1,000 customers, 50,000 transactions, and 56,589 callback attempts. The generator intentionally includes duplicate transaction references, so a unique index would reject valid assessment data.

Reproduced the reference lookup with:

```bash
docker compose exec -T db psql -U minipay -d minipay_assessment < sql/explain_search.sql
```

## Evidence before optimization

`evidence/search-plan-before.txt` recorded a `Seq Scan on transactions`. PostgreSQL removed 49,998 rows by filter and returned two duplicate matches. In that run, the scan took 89.636 ms and read 665 shared buffers. This is a measured local result, not a reproduction of the reported several-second production delay.

## Root cause

The schema had no index on `transactions.transaction_ref`, the key used by transaction investigation/search. As the table grows, PostgreSQL must inspect every row for an equality lookup. Duplicate references in the assessment data also mean this column cannot safely be made unique without a separate cleanup and business decision.

## Correction

Added a non-unique B-tree index on `transactions(transaction_ref)`. Also added workload-oriented indexes for status/created-time searches, customer history, and callback reconciliation. `ANALYZE` refreshed planner statistics after index creation. SQL is in `sql/indexes.sql`.

## Evidence after optimization

`evidence/search-plan-after.txt` recorded `Index Scan using idx_transactions_ref`, returning the same two rows. In that run, execution took 0.187 ms and used one buffer hit plus two reads. The measured before/after runs differ by about 479x, but timings are sensitive to cache and host load; the reliable result is the plan changing from a full-table scan to an index scan while preserving both duplicate matches.

## Validation and preventive controls

- Re-ran the same `EXPLAIN (ANALYZE, BUFFERS)` query after applying indexes; it selected `idx_transactions_ref`.
- Ran the seven SQL reports against the 50,000-row dataset, including duplicate-reference detection, stuck processing, reconciliation, and processing-time summaries.
- Keep a representative volume dataset and query plan in performance checks; alert on sequential scans for high-volume reference lookups.
- Review index choice against actual query patterns and write overhead; retain non-unique semantics until duplicate-reference policy is resolved.
- Capture plans and timings before and after schema changes; do not rely on a single wall-clock timing.
