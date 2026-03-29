-- Customer retention cohort analysis
WITH first_purchase AS (
    SELECT customer_key, MIN(date_key) AS first_date_key
    FROM fact_sales
    GROUP BY customer_key
),
cohort_data AS (
    SELECT fp.customer_key,
           d1.year || '-' || printf('%02d', d1.month) AS cohort_month,
           (d2.year - d1.year) * 12 + (d2.month - d1.month) AS months_since_first
    FROM fact_sales f
    JOIN first_purchase fp ON f.customer_key = fp.customer_key
    JOIN dim_date d1 ON fp.first_date_key = d1.date_key
    JOIN dim_date d2 ON f.date_key = d2.date_key
)
SELECT cohort_month, months_since_first,
       COUNT(DISTINCT customer_key) AS active_customers
FROM cohort_data
GROUP BY cohort_month, months_since_first
ORDER BY cohort_month, months_since_first;
