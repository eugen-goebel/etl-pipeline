-- Monthly revenue with running total and month-over-month growth
WITH monthly AS (
    SELECT d.year, d.month, d.month_name,
           ROUND(SUM(f.total_amount), 2) AS revenue,
           COUNT(DISTINCT f.order_key) AS orders
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.year, d.month, d.month_name
)
SELECT year, month, month_name, revenue, orders,
       ROUND(SUM(revenue) OVER (ORDER BY year, month), 2) AS cumulative_revenue,
       LAG(revenue) OVER (ORDER BY year, month) AS prev_month_revenue,
       ROUND((revenue - LAG(revenue) OVER (ORDER BY year, month)) * 100.0
           / NULLIF(LAG(revenue) OVER (ORDER BY year, month), 0), 1) AS mom_growth_pct
FROM monthly
ORDER BY year, month;
