-- Validation: do the 13 category contributions add up to headline inflation every month?
WITH div AS (
    SELECT c.date, c.code, w.weight, c.cpi,
           LAG(c.cpi, 12) OVER (PARTITION BY c.code ORDER BY c.date) AS cpi_ago
    FROM cpi c
    JOIN weights w ON w.geo_name = c.geo_name AND w.code = c.code
    WHERE c.geo_level = 'national' AND c.level = 1
),
head AS (
    SELECT date, cpi,
           LAG(cpi, 12) OVER (ORDER BY date) AS cpi_ago
    FROM cpi
    WHERE geo_level = 'national' AND code = '0'
),
monthly AS (
    SELECT d.date,
           SUM(d.weight * (d.cpi - d.cpi_ago) / h.cpi_ago) AS sum_of_parts,
           (h.cpi / h.cpi_ago - 1) * 100                    AS headline
    FROM div d
    JOIN head h ON h.date = d.date
    WHERE d.cpi_ago IS NOT NULL
    GROUP BY d.date
)
SELECT COUNT(*)                                    AS months_checked,
       ROUND(AVG(ABS(sum_of_parts - headline)), 3) AS avg_gap,
       ROUND(MAX(ABS(sum_of_parts - headline)), 3) AS worst_gap
FROM monthly;