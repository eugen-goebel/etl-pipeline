-- Supplier performance scorecard
SELECT s.supplier_id, s.name AS supplier_name, s.country,
       s.reliability_rating,
       COUNT(DISTINCT f.order_key) AS total_orders,
       ROUND(SUM(f.total_amount), 2) AS total_revenue,
       ROUND(AVG(f.profit_margin), 1) AS avg_margin,
       ROUND(SUM(CASE WHEN f.is_returned THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 1) AS return_rate_pct
FROM fact_sales f
JOIN dim_supplier s ON f.supplier_key = s.supplier_key
GROUP BY s.supplier_id, s.name, s.country, s.reliability_rating
ORDER BY total_revenue DESC;
