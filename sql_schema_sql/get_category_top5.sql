SELECT s.category,
       COUNT(*) AS practice_count
FROM practice_runs AS p
JOIN sentences AS s ON p.sentence_id = s.id
GROUP BY s.category
ORDER BY practice_count DESC, s.category ASC
LIMIT 5;
