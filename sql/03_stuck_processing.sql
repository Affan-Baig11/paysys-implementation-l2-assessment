-- Transactions still processing more than 15 minutes after creation.
SELECT
    id,
    transaction_ref,
    customer_id,
    amount,
    created_at,
    ROUND((EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at)) / 60)::numeric, 2) AS minutes_processing
FROM transactions
WHERE status = 'PROCESSING'
  AND created_at < CURRENT_TIMESTAMP - INTERVAL '15 minutes'
ORDER BY created_at;
