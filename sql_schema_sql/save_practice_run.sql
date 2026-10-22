-- STT 연습 결과 저장 및 생성된 연습 기록 ID 반환
INSERT INTO practice_runs
    (user_id, sentence_id, transcript, wer, cer, latency_ms, status)
VALUES (%s, %s, %s, %s, %s, %s, %s)
RETURNING id;
