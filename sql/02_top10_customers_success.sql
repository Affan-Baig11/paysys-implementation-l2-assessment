-- Top 10 customers by successful payment value.
SELECT
    c.id AS customer_id,
    c.customer_ref,
    c.name,
    COUNT(t.id) AS successful_transaction_count,
    SUM(t.amount) AS successful_transaction_value
FROM customers AS c
JOIN transactions AS t ON t.customer_id = c.id
WHERE t.status = 'SUCCESS'
GROUP BY c.id, c.customer_ref, c.name
ORDER BY successful_transaction_value DESC, c.id
LIMIT 10;
