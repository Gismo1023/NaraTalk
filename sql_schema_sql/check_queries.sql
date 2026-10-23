-- 학습 문장 수 및 각 카테고리의 행 개수 확인 - 실사용용은 아님 확인용임
SELECT COUNT(*) AS sentence_count FROM sentences;
SELECT category, COUNT(*) AS sentence_count FROM sentences
GROUP BY category ORDER BY MIN(sentence_no);
SELECT sentence_no, category, level, ko, en
FROM sentences ORDER BY sentence_no;

-- 연습 내역은 생성된 기록이 있을 때만 표시됩니다.
SELECT u.nickname, s.ko AS reference, s.level, p.transcript,
       p.wer, p.cer, p.status,
       CASE WHEN p.status THEN '합격' ELSE '불합격' END AS status_label,
       p.created_at
FROM practice_runs AS p
JOIN users AS u ON p.user_id = u.id
JOIN sentences AS s ON p.sentence_id = s.id
ORDER BY p.created_at DESC;
