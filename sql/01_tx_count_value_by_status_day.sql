-- Daily transaction volume and value, grouped by status.
SELECT
    created_at::date AS transaction_day,
    status,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_value
FROM transactions
GROUP BY created_at::date, status
ORDER BY transaction_day, status;
