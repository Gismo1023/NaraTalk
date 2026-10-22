-- 사용자 화면에는 닉네임만 표시하고, 테이블 관계에는 UUID를 사용합니다.
-- 닉네임으로만 사용자를 찾는 프로토타입 구조이므로 인증 기능은 없습니다.
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- 사용자 내부 고유 ID(PK)
    nickname TEXT NOT NULL CHECK (length(btrim(nickname)) > 0), -- 화면에 보여주는 닉네임
    created_at TIMESTAMPTZ NOT NULL DEFAULT now() -- 사용자 등록 시각
);

-- 영문 대소문자가 다른 닉네임도 중복으로 등록하지 않도록 설정
CREATE UNIQUE INDEX IF NOT EXISTS users_nickname_unique_lower
    ON users (LOWER(nickname));
