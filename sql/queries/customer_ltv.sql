-- Customer lifetime value with running purchase history
SELECT c.customer_id, c.name, c.segment, c.region,
       COUNT(DISTINCT f.order_key) AS total_orders,
       ROUND(SUM(f.total_amount), 2) AS lifetime_value,
       ROUND(AVG(f.total_amount), 2) AS avg_order_value,
       MIN(d.full_date) AS first_purchase,
       MAX(d.full_date) AS last_purchase,
       julianday(MAX(d.full_date)) - julianday(MIN(d.full_date)) AS customer_tenure_days
FROM fact_sales f
JOIN dim_customer c ON f.customer_key = c.customer_key
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY c.customer_id, c.name, c.segment, c.region
ORDER BY lifetime_value DESC;
