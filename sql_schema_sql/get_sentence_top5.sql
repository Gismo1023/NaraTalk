SELECT s.id AS sentence_id,
       s.sentence_no,
       s.category,
       s.level,
       s.ko,
       COUNT(*) AS practice_count
FROM practice_runs AS p
JOIN sentences AS s ON p.sentence_id = s.id
GROUP BY s.id, s.sentence_no, s.category, s.level, s.ko
ORDER BY practice_count DESC, s.sentence_no ASC
LIMIT 5;
