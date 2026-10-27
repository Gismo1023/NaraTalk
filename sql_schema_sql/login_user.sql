-- 닉네임으로 사용자 찾기 (비밀번호 검증이 없으므로 인증 기능은 아님)
SELECT id, nickname, created_at
FROM users
WHERE LOWER(nickname) = LOWER(%s);
