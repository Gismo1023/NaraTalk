import time
from src.core import evaluate_pronunciation

try:
    from faster_whisper import WhisperModel

    HAS_FASTER_WHISPER = True
except ImportError:
    HAS_FASTER_WHISPER = False


class PronunciationPipeline:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        if not HAS_FASTER_WHISPER:
            raise ImportError("faster-whisper 라이브러리가 설치되어 있지 않습니다.")

        print(f"⏳ STT 모델({model_size})을 로드하는 중...")
        self.stt_model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("✅ STT 모델 로드 완료!")

    def run_stt_with_latency(self, audio_file_path: str) -> tuple[str, int]:
        print(f"🎙️ 음성 파일({audio_file_path}) STT 추론 중...")
        start_time = time.time()

        segments, info = self.stt_model.transcribe(audio_file_path, language="ko")
        transcript = " ".join([segment.text for segment in segments]).strip()

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        print(f"📝 STT 전사 완료: '{transcript}' (소요 시간: {latency_ms}ms)")
        return transcript, latency_ms

    def evaluate(self, audio_file_path: str, reference_text: str, level: str = "보통") -> dict:
        """
        음성 파일을 입력받아 STT 추론을 거친 뒤, evaluation.py의 평가 엔진을 호출하여 최종 리포트 반환
        """
        hypothesis_text, latency_ms = self.run_stt_with_latency(audio_file_path)

        evaluation_result = evaluate_pronunciation(
            reference_text=reference_text,
            hypothesis_text=hypothesis_text,
            level=level,
            latency_ms=latency_ms
        )
        return evaluation_result


# --- 파이프라인 단독 테스트 실행부 ---
if __name__ == "__main__":
    import json

    target_reference = "역삼역으로 가는 지하철이 어느 방향인가요?"
    audio_path = "sample_recording.wav"

    print("=" * 60)
    print("🎙️ PronunciationPipeline 모듈 테스트 (실제 오디오 파일 필요)")
    print("=" * 60)

    try:
        # 모델 로드 및 평가 실행 예시 (오디오 파일이 있을 때 주석 해제)
        # pipeline = PronunciationPipeline(model_size="base")
        # report = pipeline.evaluate(audio_path, target_reference, level="보통")
        # print(json.dumps(report, ensure_ascii=False, indent=2))
        print("오디오 파일이 준비되면 pipeline.evaluate()를 호출하세요.")
    except Exception as e:
        print(f"테스트 중 안내: {e}")