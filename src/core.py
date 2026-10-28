import re
from datetime import datetime
from jiwer import cer, wer, process_characters

# 평가(지표 계산)를 위해 구두점 제거 및 영문 소문자 통일만 수행
def clean_for_evaluation(text: str) -> str:
    if not text:
        return ""

    text = text.lower()  # 영문 소문자 변환
    text = re.sub(r'[^가-힣a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()  # 공백 정돈
    return text


# WER 계산
def calculate_wer(reference: str, hypothesis: str) -> float:
    if not reference.strip():
        return 0.0 if not hypothesis.strip() else 1.0

    result = wer(reference, hypothesis)
    return round(float(result), 4)


# CER 계산 (S, D, I 정밀 측정)
def calculate_cer_details(reference: str, hypothesis: str) -> dict:
    ref_no_space = reference.replace(" ", "")
    hyp_no_space = hypothesis.replace(" ", "")

    if not ref_no_space:
        sub = 0
        dele = 0
        ins = len(hyp_no_space) if hyp_no_space else 0
        cer_val = 0.0 if not hyp_no_space else 1.0
        errors = [
            {"error_type": "insertion", "reference_token": None,
             "hypothesis_token": ch, "position": 1}
            for ch in hyp_no_space
        ]
        return {"cer": cer_val, "substitutions": sub, "deletions": dele,
                "insertions": ins, "errors": errors}

    cer_val = cer(ref_no_space, hyp_no_space)
    out = process_characters(ref_no_space, hyp_no_space)

    return {
        "cer": round(float(cer_val), 4),
        "substitutions": out.substitutions,
        "deletions": out.deletions,
        "insertions": out.insertions,
        "errors": extract_char_errors(out, ref_no_space, hyp_no_space),
    }


# 글자 단위 오류 목록 추출 (B06 오류 위치)
#   jiwer 정렬 결과(alignments)를 한 글자씩 풀어서
#   [{"error_type", "reference_token", "hypothesis_token", "position"}, ...] 로 반환
#   position: 정답 문장(공백 제외)에서 몇 번째 글자인지 (1부터 시작)
#             삽입(insertion)은 "이 위치 앞에 끼어든 글자"를 뜻함
def extract_char_errors(out, ref: str, hyp: str) -> list:
    errors = []
    alignments = getattr(out, "alignments", None) or [[]]

    for chunk in alignments[0]:
        rs, re_, hs, he = (chunk.ref_start_idx, chunk.ref_end_idx,
                           chunk.hyp_start_idx, chunk.hyp_end_idx)

        if chunk.type == "substitute":
            for i in range(re_ - rs):
                errors.append({"error_type": "substitution",
                               "reference_token": ref[rs + i],
                               "hypothesis_token": hyp[hs + i],
                               "position": rs + i + 1})
        elif chunk.type == "delete":
            for i in range(re_ - rs):
                errors.append({"error_type": "deletion",
                               "reference_token": ref[rs + i],
                               "hypothesis_token": None,
                               "position": rs + i + 1})
        elif chunk.type == "insert":
            for i in range(he - hs):
                errors.append({"error_type": "insertion",
                               "reference_token": None,
                               "hypothesis_token": hyp[hs + i],
                               "position": rs + 1})
    return errors

def evaluate_grade_and_feedback(cer_val: float) -> tuple[str, str, float]:
    # 점수 = 전사 일치도(100 - CER×100). 보정 없이 그대로 사용
    # CER이 100%를 넘으면(삽입 과다) 0점으로 표시 (CER 원값은 별도로 저장됨)
    score = max(0.0, round((1.0 - cer_val) * 100.0, 1))

    # 등급·피드백만 CER 구간으로 결정
    if cer_val <= 0.15:
        grade = "매우 우수"
        feedback = "완벽해요! 정답 문장과 거의 같게 인식되었습니다."
    elif cer_val <= 0.45:
        grade = "양호한 수준"
        feedback = "좋아요! 일부 음절이 다르게 인식되었어요. 정답을 듣고 다시 말해 보세요."
    else:
        grade = "기초에 집중"
        feedback = "기초부터 다시 차근차근 읽어볼까요?"

    return grade, feedback, score

# 종합 발음 평가 함수
def evaluate_pronunciation(reference_text: str, hypothesis_text: str, level: str = "보통", latency_ms: int = 0) -> dict:
    clean_ref = clean_for_evaluation(reference_text)
    clean_hyp = clean_for_evaluation(hypothesis_text)

    wer_val = calculate_wer(clean_ref, clean_hyp)
    cer_info = calculate_cer_details(clean_ref, clean_hyp)

    grade, feedback, score = evaluate_grade_and_feedback(cer_info["cer"])

    result = {
        "reference_text": reference_text,
        "transcript": hypothesis_text,
        "normalized_reference": clean_ref,
        "normalized_transcript": clean_hyp,
        "level": level,
        "cer": cer_info["cer"],
        "cer_details": {
            "substitutions": cer_info["substitutions"],
            "deletions": cer_info["deletions"],
            "insertions": cer_info["insertions"]
        },
        "error_items": cer_info.get("errors", []),   # 글자 단위 오류 위치 (error_items 테이블 저장용)
        "wer": wer_val,
        "score": score,
        "grade": grade,
        "feedback": feedback,
        "latency_ms": latency_ms,
        "created_at": datetime.now().isoformat(),
        "display": {
            "cer_percent": f"{cer_info['cer'] * 100:.1f}%",
            "wer_percent": f"{wer_val * 100:.1f}%",
            "score_text": f"{score:.1f}점"
        }
    }

    return result


# --- DB 연동 통합 테스트 실행부 ---
if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    sys.path.append(str(project_root / "src"))

    try:
        from db import initialize_database, register_user, login_user, get_sentence, save_practice_run, get_practice_history
    except ImportError as e:
        print(f"⚠️ DB 모듈 임포트 실패: {e}")
        sys.exit(1)

    print("=" * 60)
    print("🚀 core.py 단독 평가 & DB 연동 테스트 시작")
    print("=" * 60)

    try:
        initialize_database()
    except Exception as e:
        print(f"⚠️ DB 초기화 스킵: {e}")

    try:
        user = register_user("테스트수강생")
        user_id = user["id"]
    except Exception:
        user = login_user("테스트수강생")
        user_id = user["id"]

    sentence = get_sentence(sentence_no=25)
    sentence_id = sentence["id"]
    target_reference = sentence["ko"]

    mock_transcript = "혹 달은 사이즈냐 색상도오 있요~~?"
    report = evaluate_pronunciation(target_reference, mock_transcript, level=sentence["level"], latency_ms=450)

    print(json.dumps(report, ensure_ascii=False, indent=2))

    run_id = save_practice_run(
        user_id=user_id,
        sentence_id=sentence_id,
        transcript=report["transcript"],
        wer=report["wer"],
        cer=report["cer"],
        latency_ms=report["latency_ms"],
        score=report["score"],
        grade=report["grade"],
        feedback=report["feedback"],
        substitutions=report["cer_details"]["substitutions"],
        deletions=report["cer_details"]["deletions"],
        insertions=report["cer_details"]["insertions"]
    )
    print(f"🎉 [DB 저장 성공] ID: {run_id}")
    print("=" * 60)