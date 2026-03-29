-- Monthly seasonal index: each month's average vs annual average
WITH monthly AS (
    SELECT d.month, d.month_name,
           ROUND(SUM(f.total_amount), 2) AS revenue
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.month, d.month_name
),
annual AS (
    SELECT ROUND(AVG(revenue), 2) AS avg_monthly_revenue FROM monthly
)
SELECT m.month, m.month_name, m.revenue,
       a.avg_monthly_revenue,
       ROUND(m.revenue / a.avg_monthly_revenue * 100, 1) AS seasonal_index
FROM monthly m, annual a
ORDER BY m.month;
