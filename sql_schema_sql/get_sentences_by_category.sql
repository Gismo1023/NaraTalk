-- 카테고리별 문장 조회
SELECT id, sentence_no, category, level, ko, en
FROM sentences
WHERE category = %s
ORDER BY sentence_no;
