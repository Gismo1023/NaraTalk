-- get_recent_errors.sql
SELECT p.id AS run_id,
       p.created_at AS practiced_at,
       u.nickname,
       s.sentence_no,
       s.ko,
       s.en,
       p.transcript,
       e.error_type,
       e.reference_token,
       e.hypothesis_token,
       e.position
FROM error_items AS e
JOIN practice_runs AS p ON e.run_id = p.id
JOIN users AS u ON p.user_id = u.id
JOIN sentences AS s ON p.sentence_id = s.id
ORDER BY p.created_at DESC, p.id DESC, e.position NULLS LAST, e.id
LIMIT 100;