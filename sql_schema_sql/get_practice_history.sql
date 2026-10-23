-- 회원 UUID로 연습 기록 조회, 평가 결과 포함
SELECT p.id, u.nickname, s.sentence_no, s.category, s.level,
       s.ko, s.en, p.transcript, p.wer, p.cer, p.latency_ms,
       p.score, p.grade, p.feedback,
       p.substitutions, p.deletions, p.insertions,
       p.created_at
FROM practice_runs AS p
JOIN users AS u ON p.user_id = u.id
JOIN sentences AS s ON p.sentence_id = s.id
WHERE p.user_id = %s
ORDER BY p.created_at DESC, p.id DESC;