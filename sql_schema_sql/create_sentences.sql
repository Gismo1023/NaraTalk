-- 프로토타입의 5개 카테고리, 한국어/영어 문장, 문자열 난이도 저장
CREATE TABLE IF NOT EXISTS sentences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- 문장 고유 ID(PK), 연습 기록에서 참조
    sentence_no INTEGER NOT NULL UNIQUE CHECK (sentence_no > 0), -- 표시 순서(1~34)
    category TEXT NOT NULL, -- 예: 필수 기초 회화, 이동 및 길찾기
    level TEXT NOT NULL CHECK (level IN ('쉬움', '보통', '어려움')), -- 문자열 난이도
    ko TEXT NOT NULL, -- 한국어 정답 문장
    en TEXT NOT NULL -- 영어 번역
);
