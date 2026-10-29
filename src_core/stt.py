import time
import os
import numpy as np
import librosa
import soundfile as sf
import noisereduce as nr
from src_core.core import evaluate_pronunciation

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

    # 정제된 오디오(.wav) 파일 추출을 위한 추가 메서드 (기존 코드 수정 없음)
    def export_cleaned_wav(self, audio_file_path: str, output_wav_path: str):
        print(f"[Export] 정제 오디오 추출 중: {audio_file_path} ➔ {output_wav_path}")
        y, sr = librosa.load(audio_file_path, sr=16000, mono=True)
        y_denoise = nr.reduce_noise(y=y, sr=sr)
        y_trimmed, _ = librosa.effects.trim(y_denoise, top_db=25)
        if len(y_trimmed) == 0:
            y_trimmed = y_denoise
        sf.write(output_wav_path, y_trimmed, 16000)

    # 1. 원본(Raw) STT 추론
    def run_stt_with_latency(self, audio_file_path: str) -> tuple[str, int]:
        print(f"[Raw] 음성 파일({audio_file_path}) STT 추론 중...")
        start_time = time.time()

        segments, info = self.stt_model.transcribe(audio_file_path, language="ko")
        transcript = " ".join([segment.text for segment in segments]).strip()

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        print(f"[Raw] 전사 완료: '{transcript}' (소요 시간: {latency_ms}ms)")
        return transcript, latency_ms

    # 2. 무음 제거(VAD / Trim) 오디오 전처리 및 STT 추론
    def run_stt_with_vad(self, audio_file_path: str) -> tuple[str, int]:
        print(f"[VAD] 무음 제거 전처리 시작: {audio_file_path}")
        start_time = time.time()

        # 오디오 로드 및 앞뒤 무음 구간 제거 (librosa trim)
        y, sr = librosa.load(audio_file_path, sr=16000, mono=True)
        y_trimmed, _ = librosa.effects.trim(y, top_db=25)
        if len(y_trimmed) == 0:
            y_trimmed = y

        # 임시 파일 저장 후 STT 수행
        vad_path = audio_file_path.replace(".wav", "_vad_temp.wav")
        sf.write(vad_path, y_trimmed, 16000)

        segments, info = self.stt_model.transcribe(vad_path, language="ko")
        transcript = " ".join([segment.text for segment in segments]).strip()

        # 임시 파일 정리
        if os.path.exists(vad_path):
            try:
                os.remove(vad_path)
            except OSError:
                pass

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        print(f"[VAD] 전사 완료: '{transcript}' (소요 시간: {latency_ms}ms)")
        return transcript, latency_ms

    # 3. 잡음 제거(Noise Reduction + VAD) 오디오 전처리 및 STT 추론
    def run_stt_with_denoise(self, audio_file_path: str) -> tuple[str, int]:
        print(f"[Denoise] 잡음 제거 및 무음 전처리 시작: {audio_file_path}")
        start_time = time.time()

        # 오디오 로드 후 noisereduce로 배경 백그라운드 노이즈 감쇄 및 무음 제거
        y, sr = librosa.load(audio_file_path, sr=16000, mono=True)
        y_denoise = nr.reduce_noise(y=y, sr=sr)
        y_trimmed, _ = librosa.effects.trim(y_denoise, top_db=25)
        if len(y_trimmed) == 0:
            y_trimmed = y_denoise

        # 임시 파일 저장 후 STT 수행
        denoise_path = audio_file_path.replace(".wav", "_denoise_temp.wav")
        sf.write(denoise_path, y_trimmed, 16000)

        segments, info = self.stt_model.transcribe(denoise_path, language="ko")
        transcript = " ".join([segment.text for segment in segments]).strip()

        # 임시 파일 정리
        if os.path.exists(denoise_path):
            try:
                os.remove(denoise_path)
            except OSError:
                pass

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        print(f"[Denoise] 전사 완료: '{transcript}' (소요 시간: {latency_ms}ms)")
        return transcript, latency_ms

    # 기본 평가 메서드 (Raw 기준)
    def evaluate(self, audio_file_path: str, reference_text: str, level: str = "보통") -> dict:
        hypothesis_text, latency_ms = self.run_stt_with_latency(audio_file_path)

        evaluation_result = evaluate_pronunciation(
            reference_text=reference_text,
            hypothesis_text=hypothesis_text,
            level=level,
            latency_ms=latency_ms
        )
        return evaluation_result

    # 파이프라인별(Raw / VAD / Denoise) 종합 평가 리포트 비교 메서드 추가
    def evaluate_all_pipelines(self, audio_file_path: str, reference_text: str, level: str = "보통") -> dict:
        # 1. Raw 평가
        hyp_raw, lat_raw = self.run_stt_with_latency(audio_file_path)
        res_raw = evaluate_pronunciation(reference_text, hyp_raw, level, lat_raw)

        # 2. VAD(무음 제거) 평가
        hyp_vad, lat_vad = self.run_stt_with_vad(audio_file_path)
        res_vad = evaluate_pronunciation(reference_text, hyp_vad, level, lat_vad)

        # 3. Denoise(잡음 제거) 평가
        hyp_denoise, lat_denoise = self.run_stt_with_denoise(audio_file_path)
        res_denoise = evaluate_pronunciation(reference_text, hyp_denoise, level, lat_denoise)

        return {
            "raw": res_raw,
            "vad": res_vad,
            "denoise": res_denoise
        }


# --- 파이프라인 단독 테스트 실행부 ---
if __name__ == "__main__":
    import json

    target_reference = "역삼역으로 가는 지하철이 어느 방향인가요?"
    audio_path = "sample_recording.wav"

    print("=" * 60)
    print("PronunciationPipeline (Raw / VAD / Denoise) 비교 테스트")
    print("=" * 60)

    try:
        # pipeline = PronunciationPipeline(model_size="base")
        # results = pipeline.evaluate_all_pipelines(audio_path, target_reference, level="보통")
        # print(json.dumps(results, ensure_ascii=False, indent=2))
        print("오디오 파일이 준비되면 pipeline.evaluate_all_pipelines()를 호출하여 비교 결과를 확인하세요.")
    except Exception as e:
        print(f"테스트 중 안내: {e}")