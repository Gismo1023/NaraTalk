-- 연습 기록 UUID로 합격/불합격 판정 수정 (TRUE=합격, FALSE=불합격)
UPDATE practice_runs
SET status = %s
WHERE id = %s
RETURNING id, user_id, sentence_id, status, created_at;
