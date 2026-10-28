-- Before/after index plan for the transaction search access pattern.
-- Run once before indexes.sql, then again after indexes.sql.
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id, transaction_ref, customer_id, amount, status, created_at
FROM transactions
WHERE transaction_ref = 'TXN00004999';
