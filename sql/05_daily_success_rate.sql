-- Daily success percentage among all transaction rows created that day.
SELECT
    created_at::date AS transaction_day,
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE status = 'SUCCESS') AS successful_transactions,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'SUCCESS') / NULLIF(COUNT(*), 0),
        2
    ) AS success_rate_percent
FROM transactions
GROUP BY created_at::date
ORDER BY transaction_day;
