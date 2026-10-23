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
    # STT 추론 모듈(faster-whisper) 초기화
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):

        if not HAS_FASTER_WHISPER:
            raise ImportError("faster-whisper 라이브러리가 설치되어 있지 않습니다.")

        print(f"STT 모델({model_size})을 로드하는 중...")
        self.stt_model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("STT 모델 로드 완료!")

    # 음성 파일(.wav) 경로를 받아 STT 전사를 수행하고, 소요 시간(밀리초)을 측정
    def run_stt_with_latency(self, audio_file_path: str) -> tuple[str, int]:

        print(f"음성 파일({audio_file_path}) STT 추론 중...")

        start_time = time.time()  # 추론 시작 시간 기록

        segments, info = self.stt_model.transcribe(audio_file_path, language="ko")
        transcript = " ".join([segment.text for segment in segments]).strip()

        end_time = time.time()  # 추론 종료 시간 기록
        latency_ms = int((end_time - start_time) * 1000)  # 밀리초(ms) 단위 환산

        print(f"STT 전사 완료: '{transcript}' (소요 시간: {latency_ms}ms)")
        return transcript, latency_ms

    # 전체 파이프라인 실행: 음성 파일 STT 추론 + 시간 측정 + CER/WER 평가 리포트 산출
    def evaluate(self, audio_file_path: str, reference_text: str, level: str = "보통") -> dict:

        # STT 추론 및 처리 시간 측정
        hypothesis_text, latency_ms = self.run_stt_with_latency(audio_file_path)

        # 평가 모듈 호출 및 결과 반환 (측정된 latency_ms 자동 주입)
        evaluation_result = evaluate_pronunciation(
            reference_text=reference_text,
            hypothesis_text=hypothesis_text,
            level=level,
            latency_ms=latency_ms
        )

        return evaluation_result


# --- 테스트 예시 실행 ---
if __name__ == "__main__":
    target_reference = "역삼역으로 가는 지하철이 어느 방향인가요?"
    hyp = "역삼역으로는 가는 지하찰다 어 방향인가오??"

    # 텍스트 단독 평가 테스트 (latency_ms 수동 지정 가능)
    res = evaluate_pronunciation(target_reference, hyp, level="어려움", latency_ms=350)
    import json

    print("=== [텍스트 단독 평가 테스트 결과] ===")
    print(json.dumps(res, ensure_ascii=False, indent=2))

    # 파이프라인 클래스를 통한 실제 음성/STT 연동 테스트 시나리오
    # pipeline = PronunciationPipeline(model_size="base")
    # final_report = pipeline.evaluate("sample_recording.wav", target_reference, level="보통")
    # print(json.dumps(final_report, ensure_ascii=False, indent=2))