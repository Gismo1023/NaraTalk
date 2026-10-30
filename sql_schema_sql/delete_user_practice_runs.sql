-- 회원 탈퇴 전 해당 회원의 연습 기록 삭제 (연결된 error_items는 CASCADE 삭제)
DELETE FROM practice_runs
WHERE user_id = %s;
