-- 연습 기록 UUID로 삭제 (연결된 error_items는 CASCADE 삭제)
DELETE FROM practice_runs
WHERE id = %s
RETURNING id;
