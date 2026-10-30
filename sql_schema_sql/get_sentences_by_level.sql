-- 난이도별 문장 조회
SELECT id, sentence_no, category, level, ko, en
FROM sentences
WHERE level = %s
ORDER BY sentence_no;
