-- Return rate by category vs company average (subquery comparison)
SELECT p.category,
       COUNT(DISTINCT f.order_key) AS total_orders,
       SUM(CASE WHEN f.is_returned THEN 1 ELSE 0 END) AS returns,
       ROUND(SUM(CASE WHEN f.is_returned THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 1) AS return_rate_pct,
       ROUND((SELECT SUM(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100 FROM fact_sales), 1) AS company_avg_pct,
       ROUND(SUM(CASE WHEN f.is_returned THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100
             - (SELECT SUM(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100 FROM fact_sales), 1) AS vs_avg
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category
ORDER BY return_rate_pct DESC;
