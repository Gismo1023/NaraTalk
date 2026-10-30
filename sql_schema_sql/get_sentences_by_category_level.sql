-- 카테고리와 난이도를 모두 지정하여 문장 조회
SELECT id, sentence_no, category, level, ko, en
FROM sentences
WHERE category = %s AND level = %s
ORDER BY sentence_no;
