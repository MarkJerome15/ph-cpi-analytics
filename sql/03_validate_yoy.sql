-- Validation: recomputed YoY vs PSA's published YoY (expect max gap < 0.05 = rounding only)
WITH mine AS (
    SELECT geo_name, code, date,
           (cpi / LAG(cpi, 12) OVER (PARTITION BY geo_name, code ORDER BY date) - 1) * 100 AS yoy_mine
    FROM cpi
    WHERE geo_level = 'national' AND code = '0'
),
cmp AS (
    SELECT ABS(m.yoy_mine - p.yoy_pct) AS gap
    FROM mine m
    JOIN yoy_published p
      ON p.geo_name = m.geo_name AND p.code = m.code AND p.date = m.date
)
SELECT COUNT(*)           AS months_checked,
       ROUND(MAX(gap), 3) AS worst_gap,
       SUM(gap >= 0.05)   AS months_off
FROM cmp;