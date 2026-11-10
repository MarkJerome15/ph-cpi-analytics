-- Regional inflation ranking, latest month (all items)
WITH r AS (
    SELECT geo_name, date, cpi,
           LAG(cpi, 12) OVER (PARTITION BY geo_name ORDER BY date) AS cpi_ago
    FROM cpi
    WHERE geo_level = 'region'
      AND is_aggregate = 0
      AND code = '0'
)
SELECT geo_name                            AS region,
       ROUND(cpi, 1)                       AS cpi,
       ROUND((cpi / cpi_ago - 1) * 100, 1) AS yoy_pct
FROM r
WHERE date = '2026-10-01'
ORDER BY yoy_pct DESC;