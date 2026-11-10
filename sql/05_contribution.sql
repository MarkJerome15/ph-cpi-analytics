-- What drives inflation? Contribution of each main category, October 2026
WITH div AS (
    SELECT c.date, c.code, c.item, w.weight, c.cpi,
           LAG(c.cpi, 12) OVER (PARTITION BY c.code ORDER BY c.date) AS cpi_ago
    FROM cpi c
    JOIN weights w
      ON w.geo_name = c.geo_name AND w.code = c.code
    WHERE c.geo_level = 'national' AND c.level = 1
),
head AS (
    SELECT date,
           LAG(cpi, 12) OVER (ORDER BY date) AS cpi_ago
    FROM cpi
    WHERE geo_level = 'national' AND code = '0'
)
SELECT d.code,
       d.item,
       ROUND(d.weight, 1)                                    AS weight_pct,
       ROUND((d.cpi / d.cpi_ago - 1) * 100, 1)               AS price_change_pct,
       ROUND(d.weight * (d.cpi - d.cpi_ago) / h.cpi_ago, 2)  AS contribution_pts
FROM div d
JOIN head h ON h.date = d.date
WHERE d.date = '2026-10-01'
ORDER BY contribution_pts DESC;