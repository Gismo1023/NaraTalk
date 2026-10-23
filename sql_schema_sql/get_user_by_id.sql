-- UUID로 회원 내부 정보 조회 (닉네임 표시용)
SELECT id, nickname, created_at
FROM users
WHERE id = %s;
