-- Year-on-year inflation: compare each month with the same month last year
SELECT date,
       cpi,
       LAG(cpi, 12) OVER (ORDER BY date) AS cpi_year_ago,
       ROUND((cpi / LAG(cpi, 12) OVER (ORDER BY date) - 1) * 100, 1) AS yoy_pct
FROM cpi
WHERE geo_level = 'national'
  AND code = '0'
ORDER BY date DESC
LIMIT 13;