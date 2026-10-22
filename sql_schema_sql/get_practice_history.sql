-- 회원 UUID로 연습 기록 조회, 화면에는 닉네임과 합격/불합격을 표시
SELECT p.id, u.nickname, s.sentence_no, s.category, s.level,
       s.ko, s.en, p.transcript, p.wer, p.cer, p.latency_ms,
       p.status,
       CASE WHEN p.status THEN '합격' ELSE '불합격' END AS status_label,
       p.created_at
FROM practice_runs AS p
JOIN users AS u ON p.user_id = u.id
JOIN sentences AS s ON p.sentence_id = s.id
WHERE p.user_id = %s
ORDER BY p.created_at DESC, p.id DESC;
