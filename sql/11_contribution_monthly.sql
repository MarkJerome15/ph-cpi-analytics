-- Contribution of each category group to inflation, every month (long format for Power BI)
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
)
SELECT d.date,
       CASE d.code
           WHEN '01' THEN 'Food'
           WHEN '04' THEN 'Housing & utilities'
           WHEN '07' THEN 'Transport'
           WHEN '11' THEN 'Restaurants & hotels'
           ELSE 'All other'
       END AS category,
       ROUND(SUM(d.weight * (d.cpi - d.cpi_ago) / h.cpi_ago), 3) AS contribution_pts
FROM div d
JOIN head h ON h.date = d.date
WHERE d.cpi_ago IS NOT NULL
GROUP BY d.date, category
ORDER BY d.date, category;