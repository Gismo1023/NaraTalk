-- STT 인식 오류 상세 저장 및 오류 기록 ID 반환
INSERT INTO error_items
    (run_id, error_type, reference_token, hypothesis_token, position)
VALUES (%s, %s, %s, %s, %s)
RETURNING id;
