-- Year-over-year category growth comparison
WITH yearly AS (
    SELECT p.category, d.year,
           ROUND(SUM(f.total_amount), 2) AS revenue
    FROM fact_sales f
    JOIN dim_product p ON f.product_key = p.product_key
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY p.category, d.year
)
SELECT category,
       MAX(CASE WHEN year = 2024 THEN revenue END) AS revenue_2024,
       MAX(CASE WHEN year = 2025 THEN revenue END) AS revenue_2025,
       ROUND((MAX(CASE WHEN year = 2025 THEN revenue END) - MAX(CASE WHEN year = 2024 THEN revenue END))
             * 100.0 / NULLIF(MAX(CASE WHEN year = 2024 THEN revenue END), 0), 1) AS yoy_growth_pct
FROM yearly
GROUP BY category
ORDER BY yoy_growth_pct DESC;
