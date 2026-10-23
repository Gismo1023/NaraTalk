import re
import time
from datetime import datetime
from jiwer import cer, wer, process_characters

# 평가(지표 계산)를 위해 구두점 제거 및 영문 소문자 통일만 수행
def clean_for_evaluation(text: str) -> str:
    if not text:
        return ""

    text = text.lower()  # 영문 소문자 변환
    # 한글(가-힣), 영문(a-z), 숫자(0-9), 공백을 제외한 모든 특수문자/구두점 제거 (. ! ? 등 포함)
    text = re.sub(r'[^가-힣a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()  # 공백 정돈

    return text


# WER 계산
def calculate_wer(reference: str, hypothesis: str) -> float:
    if not reference.strip():
        return 0.0 if not hypothesis.strip() else 1.0

    result = wer(reference, hypothesis)
    return round(float(result), 4)


# Levenshtein 정렬·오류 유형 표시
# CER 계산 (S, D, I 정밀 측정)
def calculate_cer_details(reference: str, hypothesis: str) -> dict:
    """
    공백 제외 CER 및 상세 글자 오류 개수 계산
    - 공백을 제거한 뒤 글자 단위 전용 process_characters를 활용하여
      대체(S), 누락(D), 삽입(I)을 정밀하게 측정
    """
    # 공백 제거
    ref_no_space = reference.replace(" ", "")
    hyp_no_space = hypothesis.replace(" ", "")

    if not ref_no_space:
        sub = 0
        dele = 0
        ins = len(hyp_no_space) if hyp_no_space else 0
        cer_val = 0.0 if not hyp_no_space else 1.0
        return {"cer": cer_val, "substitutions": sub, "deletions": dele, "insertions": ins}

    # 공백 제거 문자열을 기준으로 정확한 CER 계산
    cer_val = cer(ref_no_space, hyp_no_space)

    # 글자 단위 전용 process_characters를 사용하여 S, D, I 정밀 측정
    out = process_characters(ref_no_space, hyp_no_space)

    return {
        "cer": round(float(cer_val), 4),
        "substitutions": out.substitutions,
        "deletions": out.deletions,
        "insertions": out.insertions
    }


def evaluate_grade_and_feedback(cer_val: float) -> tuple[str, str, float]:
    """
    CER 기준별 등급, 피드백 및 최소 보정 점수 매핑
    - 0% <= CER <= 15%: 매우 우수 (85.0점 이상)
    - 15% < CER <= 45%: 양호한 수준 (75.0점 이상 ~ 85.0점 미만)
    - 45% < CER: 기초에 집중 (최대 75.0점 미만)
    """
    raw_score = (1.0 - cer_val) * 100.0
    score = max(0.0, round(raw_score, 1))

    if cer_val <= 0.15:
        grade = "매우 우수"
        feedback = "완벽해요! 원어민처럼 매우 정확한 발음입니다."
        if score < 85.0:
            score = 85.0
    elif cer_val <= 0.45:
        grade = "양호한 수준"
        feedback = "좋아요! 의사소통에 문제없지만 일부 음절을 더 명확히 해보세요."
        if score >= 85.0:
            score = 84.9
        if score < 75.0:
            score = 75.0
    else:
        grade = "기초에 집중"
        feedback = "기초부터 다시 차근차근 읽어볼까요?"
        if score >= 75.0:
            score = 74.9

    return grade, feedback, score


# 종합 발음 평가 함수 (파이프라인)
def evaluate_pronunciation(reference_text: str, hypothesis_text: str, level: str = "보통", latency_ms: int = 0) -> dict:
    clean_ref = clean_for_evaluation(reference_text)
    clean_hyp = clean_for_evaluation(hypothesis_text)

    wer_val = calculate_wer(clean_ref, clean_hyp)
    cer_info = calculate_cer_details(clean_ref, clean_hyp)

    grade, feedback, score = evaluate_grade_and_feedback(cer_info["cer"])

    result = {
        "reference_text": reference_text,  # 평가 당시 원본 정답 문장
        "transcript": hypothesis_text,  # 녹음 문장 STT 원본 전사
        "normalized_reference": clean_ref,  # 평가용 정제된 정답 문장
        "normalized_transcript": clean_hyp,  # 평가용 정제된 전사 문장
        "level": level,  # 난이도
        "cer": cer_info["cer"],
        "cer_details": {
            "substitutions": cer_info["substitutions"],  # 정답 글자와 다르게 인식된 글자 수
            "deletions": cer_info["deletions"],  # 정답 글자 중 누락된 글자 수
            "insertions": cer_info["insertions"]  # 없던 글자가 추가로 인식된 글자 수
        },
        "wer": wer_val,
        "score": score,  # CER을 기반으로 한 점수
        "grade": grade,
        "feedback": feedback,
        "latency_ms": latency_ms,  # DB practice_runs의 STT 처리시간(밀리초)
        "created_at": datetime.now().isoformat(),  # DB practice_runs의 연습 시각
        "display": {
            "cer_percent": f"{cer_info['cer'] * 100:.1f}%",
            "wer_percent": f"{wer_val * 100:.1f}%",
            "score_text": f"{score:.1f}점"
        }
    }

    return result


# STT 추론 및 시간 측정 클래스
try:
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    HAS_FASTER_WHISPER = False


class PronunciationPipeline:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        if not HAS_FASTER_WHISPER:
            raise ImportError("faster-whisper 라이브러리가 설치되어 있지 않습니다.")

        print(f"STT 모델({model_size})을 로드하는 중...")
        self.stt_model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("STT 모델 로드 완료!")

    def run_stt_with_latency(self, audio_file_path: str) -> tuple[str, int]:
        print(f"음성 파일({audio_file_path}) STT 추론 중...")
        start_time = time.time()

        segments, info = self.stt_model.transcribe(audio_file_path, language="ko")
        transcript = " ".join([segment.text for segment in segments]).strip()

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        print(f"STT 전사 완료: '{transcript}' (소요 시간: {latency_ms}ms)")
        return transcript, latency_ms

    def evaluate(self, audio_file_path: str, reference_text: str, level: str = "보통") -> dict:
        hypothesis_text, latency_ms = self.run_stt_with_latency(audio_file_path)
        evaluation_result = evaluate_pronunciation(
            reference_text=reference_text,
            hypothesis_text=hypothesis_text,
            level=level,
            latency_ms=latency_ms
        )
        return evaluation_result


# --- DB 연동 통합 테스트 실행부 ---
if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    # src_db 폴더를 파이썬 경로에 추가하여 db.py를 원활하게 임포트하도록 설정
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    sys.path.append(str(project_root / "src_db"))

    try:
        from db import initialize_database, register_user, login_user, get_sentence, save_practice_run, get_practice_history
    except ImportError as e:
        print(f"⚠️ DB 모듈 임포트 실패: {e}")
        print("src_db 폴더와 db.py 파일 위치를 확인해주세요.")
        sys.exit(1)

    print("=" * 60)
    print("🚀 발음 평가 엔진 & 데이터베이스(DB) 연동 테스트 시작")
    print("=" * 60)

    # 1. DB 초기화 (테이블이 없다면 생성)
    try:
        initialize_database()
    except Exception as e:
        print(f"⚠️ DB 초기화 스킵 또는 연결 확인 필요: {e}")

    # 2. 테스트용 회원 등록 (또는 기존 회원 조회)
    try:
        user = register_user("테스트수강생")
        user_id = user["id"]
        print(f"✅ 테스트 회원 준비 완료 (UUID: {user_id})")
    except Exception as e:
        user = login_user("테스트수강생")
        if user:
            user_id = user["id"]
            print(f"✅ 기존 테스트 회원으로 진행 (UUID: {user_id})")
        else:
            raise e

    # 3. 테스트용 문장 가져오기 (예: 1번 문장)
    sentence = get_sentence(sentence_no=16)
    if not sentence:
        raise ValueError("DB에 등록된 문장이 없습니다. seed_sentences_34.sql이 실행되었는지 확인하세요.")

    sentence_id = sentence["id"]
    target_reference = sentence["ko"]
    print(f"📖 타겟 문장 로드 성공: '{target_reference}' (ID: {sentence_id})")

    # 4. 사용자가 발음한 가상의 STT 텍스트 (조금 틀린 상태)
    mock_transcript = "부대이 시설이 어디 있야요!"

    # 5. evaluation.py의 평가 엔진 가동 (CER, WER, 점수, 피드백 및 latency_ms 산출)
    report = evaluate_pronunciation(
        reference_text=target_reference,
        hypothesis_text=mock_transcript,
        level=sentence["level"],
        latency_ms=450  # 가상의 STT 처리 시간 (450ms)
    )

    print("\n📊 [평가 엔진 산출 리포트]")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    # 6. 산출된 리포트를 db.py를 통해 practice_runs 테이블에 저장!
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

    print(f"\n🎉 [DB 저장 성공!] 생성된 practice_runs ID: {run_id}")

    # 7. DB에서 방금 저장한 내역이 잘 조회되는지 확인
    history = get_practice_history(user_id)
    print(f"\n📂 [DB 조회 결과] 해당 회원의 총 연습 기록 수: {len(history)}건")
    if history:
        print(f"가장 최근 기록 요약 -> 점수: {history[0]['score']}점, 등급: {history[0]['grade']}, 인식문장: '{history[0]['transcript']}'")
    print("=" * 60)