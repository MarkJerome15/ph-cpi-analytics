-- Year-on-year inflation for the Philippines and every region, every month
WITH r AS (
    SELECT geo_name, geo_level, date, cpi,
           LAG(cpi, 12) OVER (PARTITION BY geo_name ORDER BY date) AS cpi_ago
    FROM cpi
    WHERE code = '0'
      AND (geo_level = 'national' OR (geo_level = 'region' AND is_aggregate = 0))
)
SELECT geo_name AS area,
       geo_level,
       date,
       ROUND(cpi, 1)                       AS cpi,
       ROUND((cpi / cpi_ago - 1) * 100, 2) AS yoy_pct
FROM r
WHERE cpi_ago IS NOT NULL
ORDER BY area, date;