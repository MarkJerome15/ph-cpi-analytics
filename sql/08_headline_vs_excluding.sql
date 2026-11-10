-- Headline vs inflation excluding transport; food & transport; food, transport & housing/utilities
WITH div AS (
    SELECT c.date, c.code, w.weight, c.cpi
    FROM cpi c
    JOIN weights w ON w.geo_name = c.geo_name AND w.code = c.code
    WHERE c.geo_level = 'national' AND c.level = 1
),
idx AS (
    SELECT date,
           SUM(weight * cpi) / SUM(weight) AS headline,
           SUM(CASE WHEN code <> '07' THEN weight * cpi END)
             / SUM(CASE WHEN code <> '07' THEN weight END) AS ex_transport,
           SUM(CASE WHEN code NOT IN ('01', '07') THEN weight * cpi END)
             / SUM(CASE WHEN code NOT IN ('01', '07') THEN weight END) AS ex_food_transport,
           SUM(CASE WHEN code NOT IN ('01', '04', '07') THEN weight * cpi END)
             / SUM(CASE WHEN code NOT IN ('01', '04', '07') THEN weight END) AS ex_food_transport_housing
    FROM div
    GROUP BY date
)
SELECT date,
       ROUND((headline          / LAG(headline, 12)          OVER (ORDER BY date) - 1) * 100, 1) AS headline_yoy,
       ROUND((ex_transport      / LAG(ex_transport, 12)      OVER (ORDER BY date) - 1) * 100, 1) AS ex_transport_yoy,
       ROUND((ex_food_transport / LAG(ex_food_transport, 12) OVER (ORDER BY date) - 1) * 100, 1) AS ex_food_transport_yoy,
       ROUND((ex_food_transport_housing / LAG(ex_food_transport_housing, 12) OVER (ORDER BY date) - 1) * 100, 1) AS ex_food_transport_housing_yoy
FROM idx
ORDER BY date;