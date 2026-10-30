-- 특정 연습의 인식 오류 목록 조회
SELECT id, error_type, reference_token, hypothesis_token, position
FROM error_items
WHERE run_id = %s
ORDER BY position NULLS LAST, id;
