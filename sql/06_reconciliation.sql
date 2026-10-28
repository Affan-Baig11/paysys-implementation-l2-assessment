-- Compare successful transaction rows with transactions having at least one
-- successful callback. DISTINCT avoids counting multiple successful retries
-- for the same transaction more than once.
WITH successful_transactions AS (
    SELECT id, amount
    FROM transactions
    WHERE status = 'SUCCESS'
),
transactions_with_successful_callback AS (
    SELECT DISTINCT t.id, t.amount
    FROM transactions AS t
    JOIN callbacks AS cb ON cb.transaction_id = t.id
    WHERE cb.callback_status = 'SUCCESS'
),
success_without_callback AS (
    SELECT st.id, st.amount
    FROM successful_transactions AS st
    WHERE NOT EXISTS (
        SELECT 1
        FROM callbacks AS cb
        WHERE cb.transaction_id = st.id
          AND cb.callback_status = 'SUCCESS'
    )
)
SELECT
    (SELECT COUNT(*) FROM successful_transactions) AS successful_transaction_count,
    (SELECT COALESCE(SUM(amount), 0) FROM successful_transactions) AS successful_transaction_value,
    (SELECT COUNT(*) FROM transactions_with_successful_callback) AS callback_success_transaction_count,
    (SELECT COALESCE(SUM(amount), 0) FROM transactions_with_successful_callback) AS callback_success_transaction_value,
    (SELECT COUNT(*) FROM successful_transactions)
      - (SELECT COUNT(*) FROM transactions_with_successful_callback) AS count_difference,
    (SELECT COALESCE(SUM(amount), 0) FROM successful_transactions)
      - (SELECT COALESCE(SUM(amount), 0) FROM transactions_with_successful_callback) AS value_difference,
    (SELECT COUNT(*) FROM success_without_callback) AS success_without_callback_count,
    (SELECT COALESCE(SUM(amount), 0) FROM success_without_callback) AS success_without_callback_value;
