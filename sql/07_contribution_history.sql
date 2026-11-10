-- How the drivers of inflation changed over time (one row per month)
WITH div AS (
    SELECT c.date, c.code, w.weight, c.cpi,
           LAG(c.cpi, 12) OVER (PARTITION BY c.code ORDER BY c.date) AS cpi_ago
    FROM cpi c
    JOIN weights w ON w.geo_name = c.geo_name AND w.code = c.code
    WHERE c.geo_level = 'national' AND c.level = 1
),
head AS (
    SELECT date, LAG(cpi, 12) OVER (ORDER BY date) AS cpi_ago
    FROM cpi
    WHERE geo_level = 'national' AND code = '0'
),
contrib AS (
    SELECT d.date, d.code,
           d.weight * (d.cpi - d.cpi_ago) / h.cpi_ago AS pts
    FROM div d
    JOIN head h ON h.date = d.date
    WHERE d.cpi_ago IS NOT NULL
)
SELECT date,
       ROUND(SUM(CASE WHEN code = '01' THEN pts END), 2)                    AS food,
       ROUND(SUM(CASE WHEN code = '04' THEN pts END), 2)                    AS housing_utilities,
       ROUND(SUM(CASE WHEN code = '07' THEN pts END), 2)                    AS transport,
       ROUND(SUM(CASE WHEN code NOT IN ('01', '04', '07') THEN pts END), 2) AS everything_else,
       ROUND(SUM(pts), 2)                                                   AS total
FROM contrib
GROUP BY date
ORDER BY date;