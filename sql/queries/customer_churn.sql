-- Customer churn: customers with no purchase in last 90 days
WITH last_activity AS (
    SELECT c.customer_id, c.name, c.segment, c.region,
           MAX(d.full_date) AS last_purchase_date,
           COUNT(DISTINCT f.order_key) AS total_orders,
           ROUND(SUM(f.total_amount), 2) AS lifetime_value
    FROM dim_customer c
    LEFT JOIN fact_sales f ON c.customer_key = f.customer_key
    LEFT JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY c.customer_id, c.name, c.segment, c.region
)
SELECT customer_id, name, segment, region, last_purchase_date,
       total_orders, lifetime_value,
       CAST(julianday('2026-01-01') - julianday(last_purchase_date) AS INTEGER) AS days_since_last,
       CASE
           WHEN last_purchase_date IS NULL THEN 'Never Purchased'
           WHEN julianday('2026-01-01') - julianday(last_purchase_date) > 180 THEN 'Churned'
           WHEN julianday('2026-01-01') - julianday(last_purchase_date) > 90 THEN 'At Risk'
           ELSE 'Active'
       END AS churn_status
FROM last_activity
ORDER BY days_since_last DESC;
