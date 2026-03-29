-- Day-of-week sales patterns with deviation from average
WITH daily_avg AS (
    SELECT d.day_name, d.day_of_week,
           ROUND(AVG(f.total_amount), 2) AS avg_order_value,
           COUNT(*) AS total_orders,
           ROUND(SUM(f.total_amount), 2) AS total_revenue
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY d.day_name, d.day_of_week
),
overall AS (
    SELECT ROUND(AVG(total_revenue), 2) AS avg_daily_revenue FROM daily_avg
)
SELECT da.day_name, da.day_of_week, da.total_orders, da.total_revenue, da.avg_order_value,
       ROUND((da.total_revenue - o.avg_daily_revenue) / o.avg_daily_revenue * 100, 1) AS pct_vs_avg
FROM daily_avg da, overall o
ORDER BY da.day_of_week;
