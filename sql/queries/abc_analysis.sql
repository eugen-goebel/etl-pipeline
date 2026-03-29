-- ABC Pareto analysis of products by cumulative revenue share
WITH product_totals AS (
    SELECT p.product_id, p.name, p.category,
           ROUND(SUM(f.total_amount), 2) AS revenue
    FROM fact_sales f
    JOIN dim_product p ON f.product_key = p.product_key
    GROUP BY p.product_id, p.name, p.category
),
ranked AS (
    SELECT *,
           ROUND(SUM(revenue) OVER (ORDER BY revenue DESC) * 100.0
                 / SUM(revenue) OVER (), 1) AS cumulative_pct
    FROM product_totals
)
SELECT product_id, name, category, revenue, cumulative_pct,
       CASE
           WHEN cumulative_pct <= 80 THEN 'A'
           WHEN cumulative_pct <= 95 THEN 'B'
           ELSE 'C'
       END AS abc_class
FROM ranked
ORDER BY revenue DESC;
