-- Non-unique indexes preserve the intentionally duplicated transaction_ref values.
CREATE INDEX IF NOT EXISTS idx_transactions_ref
    ON transactions (transaction_ref);

CREATE INDEX IF NOT EXISTS idx_transactions_status_created
    ON transactions (status, created_at);

CREATE INDEX IF NOT EXISTS idx_transactions_customer_created
    ON transactions (customer_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_callbacks_transaction_status
    ON callbacks (transaction_id, callback_status);

ANALYZE customers;
ANALYZE transactions;
ANALYZE callbacks;
