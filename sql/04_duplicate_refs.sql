-- Duplicate references are retained for investigation; do not hide or delete them here.
SELECT
    transaction_ref,
    COUNT(*) AS occurrence_count,
    ARRAY_AGG(id ORDER BY id) AS transaction_ids,
    SUM(amount) AS combined_amount
FROM transactions
GROUP BY transaction_ref
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC, transaction_ref;
