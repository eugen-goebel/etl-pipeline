-- Top 3 products per category by revenue (DENSE_RANK window function)
WITH product_revenue AS (
    SELECT p.category, p.name AS product_name,
           ROUND(SUM(f.total_amount), 2) AS revenue,
           SUM(f.quantity) AS units_sold,
           DENSE_RANK() OVER (PARTITION BY p.category ORDER BY SUM(f.total_amount) DESC) AS rank
    FROM fact_sales f
    JOIN dim_product p ON f.product_key = p.product_key
    GROUP BY p.category, p.name
)
SELECT category, product_name, revenue, units_sold, rank
FROM product_revenue
WHERE rank <= 3
ORDER BY category, rank;
