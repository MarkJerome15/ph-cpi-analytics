-- Validation: the 13 main categories' weights must add up to 100%
SELECT COUNT(*)              AS categories,
       ROUND(SUM(weight), 2) AS total_weight
FROM weights
WHERE geo_level = 'national'
  AND level = 1;