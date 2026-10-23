-- 회원 UUID로 닉네임 변경
UPDATE users
SET nickname = %s
WHERE id = %s
RETURNING id, nickname, created_at;
