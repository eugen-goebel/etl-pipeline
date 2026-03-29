-- Average basket size by customer segment and quarter
SELECT c.segment,
       d.year || '-Q' || d.quarter AS quarter,
       COUNT(DISTINCT f.order_key) AS orders,
       ROUND(AVG(f.quantity), 1) AS avg_items_per_order,
       ROUND(AVG(f.total_amount), 2) AS avg_order_value,
       ROUND(SUM(f.total_amount), 2) AS total_revenue
FROM fact_sales f
JOIN dim_customer c ON f.customer_key = c.customer_key
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY c.segment, d.year, d.quarter
ORDER BY c.segment, d.year, d.quarter;
