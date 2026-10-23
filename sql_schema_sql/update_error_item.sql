-- 오류 상세 기록 UUID로 오류 내용 수정
UPDATE error_items
SET error_type = %s,
    reference_token = %s,
    hypothesis_token = %s,
    position = %s
WHERE id = %s
RETURNING id, run_id, error_type, reference_token, hypothesis_token, position;
