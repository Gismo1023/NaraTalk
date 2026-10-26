-- 오류 기록 UUID로 특정 오류 상세 삭제
DELETE FROM error_items
WHERE id = %s
RETURNING id;
