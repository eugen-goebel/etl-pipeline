-- RFM segmentation using NTILE window function
WITH rfm_raw AS (
    SELECT f.customer_key, c.customer_id, c.name,
           julianday('2026-01-01') - julianday(MAX(d.full_date)) AS recency_days,
           COUNT(DISTINCT f.order_key) AS frequency,
           ROUND(SUM(f.total_amount), 2) AS monetary
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_key = c.customer_key
    JOIN dim_date d ON f.date_key = d.date_key
    GROUP BY f.customer_key, c.customer_id, c.name
),
rfm_scored AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
           NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
           NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm_raw
)
SELECT customer_id, name, recency_days, frequency, monetary,
       r_score, f_score, m_score,
       CASE
           WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
           WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
           WHEN r_score >= 4 AND f_score <= 2 THEN 'New Customers'
           WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
           WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
           ELSE 'Regular'
       END AS segment
FROM rfm_scored
ORDER BY monetary DESC;
