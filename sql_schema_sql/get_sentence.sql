-- 표시 번호로 학습 문장 1개 조회
SELECT id, sentence_no, category, level, ko, en
FROM sentences
WHERE sentence_no = %s;
