-- 회원가입: 닉네임만 입력받고 UUID는 PostgreSQL이 자동 생성
INSERT INTO users (nickname)
VALUES (%s)
RETURNING id, nickname, created_at;
