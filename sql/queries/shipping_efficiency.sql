-- Shipping cost as percentage of order value by shipping tier
SELECT
    CASE
        WHEN shipping_cost < 5 THEN 'Economy (< 5)'
        WHEN shipping_cost < 8 THEN 'Standard (5-8)'
        ELSE 'Express (> 8)'
    END AS shipping_tier,
    COUNT(*) AS orders,
    ROUND(AVG(shipping_cost), 2) AS avg_shipping_cost,
    ROUND(AVG(total_amount), 2) AS avg_order_value,
    ROUND(SUM(shipping_cost) / NULLIF(SUM(total_amount), 0) * 100, 1) AS shipping_pct
FROM fact_sales
WHERE shipping_cost > 0
GROUP BY shipping_tier
ORDER BY avg_shipping_cost;
