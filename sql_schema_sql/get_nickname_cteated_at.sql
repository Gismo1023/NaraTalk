SELECT u.nickname,
       u.created_at,
       COUNT(r.id) AS practice_count
FROM users AS u
LEFT JOIN practice_runs AS r ON u.id = r.user_id
GROUP BY u.id, u.nickname, u.created_at
ORDER BY u.created_at DESC, u.id DESC;
