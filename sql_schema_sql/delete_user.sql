-- 회원 UUID로 회원 삭제
DELETE FROM users
WHERE id = %s
RETURNING id;
