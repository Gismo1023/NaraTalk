-- 문장 번호로 문장 삭제 (해당 문장의 연습 기록이 있으면 FK 제약으로 삭제되지 않음)
DELETE FROM sentences
WHERE sentence_no = %s
RETURNING id;
