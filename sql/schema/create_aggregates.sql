DELETE FROM agg_daily_sales;

INSERT INTO agg_daily_sales (date, total_revenue, total_orders, avg_order_value, unique_customers)
SELECT
    d.full_date                          AS date,
    SUM(f.total_amount)                  AS total_revenue,
    COUNT(DISTINCT f.order_key)          AS total_orders,
    AVG(f.total_amount)                  AS avg_order_value,
    COUNT(DISTINCT f.customer_key)       AS unique_customers
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.full_date
ORDER BY d.full_date;
