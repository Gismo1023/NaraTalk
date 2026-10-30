-- error_items.sql
-- STT 인식에서 발생한 개별 오류를 저장하는 테이블
CREATE TABLE IF NOT EXISTS error_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- 오류 기록 고유 ID, 기본키(PK)
    run_id UUID NOT NULL REFERENCES practice_runs(id) ON DELETE CASCADE, -- 어떤 연습에서 발생했는지 참조(FK), 연습 삭제 시 오류도 삭제
    error_type TEXT NOT NULL, -- 오류 유형: substitution(대체), deletion(삭제), insertion(삽입)
    reference_token TEXT, -- 정답에서 대응되는 단어 또는 어절
    hypothesis_token TEXT, -- STT 예측에서 대응되는 단어 또는 어절
    position INTEGER -- 오류 발생 위치(필요 시 기록)
);

CREATE INDEX IF NOT EXISTS idx_error_items_run_id
    ON error_items (run_id);
