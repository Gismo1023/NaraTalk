SELECT s.level,
       COUNT(*) AS practice_count
FROM practice_runs AS p
JOIN sentences AS s ON p.sentence_id = s.id
GROUP BY s.level
ORDER BY practice_count DESC,
         CASE s.level
             WHEN '쉬움' THEN 1
             WHEN '보통' THEN 2
             WHEN '어려움' THEN 3
         END ASC
LIMIT 3;
