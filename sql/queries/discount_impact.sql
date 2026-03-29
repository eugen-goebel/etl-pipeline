-- Discount impact on margins by discount tier
SELECT
    CASE
        WHEN discount_pct = 0 THEN 'No Discount'
        WHEN discount_pct <= 5 THEN '1-5%'
        WHEN discount_pct <= 10 THEN '6-10%'
        WHEN discount_pct <= 15 THEN '11-15%'
        ELSE '16-20%'
    END AS discount_tier,
    COUNT(*) AS orders,
    ROUND(AVG(total_amount), 2) AS avg_order_value,
    ROUND(AVG(profit_margin), 1) AS avg_margin_pct,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM fact_sales
GROUP BY discount_tier
ORDER BY MIN(discount_pct);
