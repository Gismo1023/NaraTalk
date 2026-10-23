-- 문장 번호로 카테고리, 난이도, 한국어/영어 문장 수정
UPDATE sentences
SET category = %s,
    level = %s,
    ko = %s,
    en = %s
WHERE sentence_no = %s
RETURNING id, sentence_no, category, level, ko, en;
