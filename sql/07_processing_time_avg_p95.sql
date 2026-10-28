-- Average and p95 processing time for transactions with a completion timestamp.
SELECT
    COUNT(*) AS completed_transaction_count,
    ROUND(AVG(EXTRACT(EPOCH FROM (completed_at - created_at)))::numeric, 3) AS average_processing_seconds,
    ROUND(
        percentile_cont(0.95) WITHIN GROUP (
            ORDER BY EXTRACT(EPOCH FROM (completed_at - created_at))
        )::numeric,
        3
    ) AS p95_processing_seconds
FROM transactions
WHERE completed_at IS NOT NULL;
