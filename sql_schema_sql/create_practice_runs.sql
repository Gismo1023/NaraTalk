-- 특정 회원이 특정 문장을 연습한 STT 평가 결과 저장
CREATE TABLE IF NOT EXISTS practice_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- 연습 기록 ID(PK)
    user_id UUID NOT NULL REFERENCES users(id), -- 회원 고유 ID(FK), 닉네임이 아님
    sentence_id UUID NOT NULL REFERENCES sentences(id), -- 문장 고유 ID(FK)
    transcript TEXT, -- STT 인식 결과
    wer DOUBLE PRECISION, -- 단어 오류율
    cer DOUBLE PRECISION, -- 문자 오류율
    latency_ms INTEGER, -- 처리시간(ms)
    status BOOLEAN NOT NULL, -- TRUE=합격, FALSE=불합격 (판정 기준은 평가 기능에서 결정)
    created_at TIMESTAMPTZ NOT NULL DEFAULT now() -- 연습 날짜 및 시간
);

CREATE INDEX IF NOT EXISTS idx_practice_runs_user_id ON practice_runs (user_id);
CREATE INDEX IF NOT EXISTS idx_practice_runs_sentence_id ON practice_runs (sentence_id);
