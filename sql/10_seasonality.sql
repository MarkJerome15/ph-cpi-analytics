-- Seasonality: average month-on-month price change for each calendar month
WITH m AS (
    SELECT date, cpi,
           LAG(cpi, 1) OVER (ORDER BY date) AS cpi_prev
    FROM cpi
    WHERE geo_level = 'national' AND code = '0'
)
SELECT CAST(strftime('%m', date) AS INTEGER)     AS month,
       ROUND(AVG((cpi / cpi_prev - 1) * 100), 2) AS avg_mom_pct,
       COUNT(*)                                  AS years
FROM m
WHERE cpi_prev IS NOT NULL
GROUP BY month
ORDER BY month;