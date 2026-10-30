# 전처리 전후 비교 CSV 산출 및 오디오 추출 통합 스크립트
import os
import sys
import glob
import pandas as pd

# 경로 설정 (현재 스크립트가 위치한 tests 폴더 기준)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))  # project 루트 경로

# src 폴더를 파이썬 모듈 검색 경로(sys.path)에 추가하여 stt.py 및 core.py 임포트 가능하게 설정
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.append(src_path)

# 1. 입력 오디오 폴더 (stt_vad_noise_audio) 및 정제된 WAV가 저장될 출력 폴더 설정
audio_dir = os.path.join(current_dir, "stt_vad_noise_audio")
output_cleaned_dir = os.path.join(current_dir, "stt_vad_noise_cleaned_audio_output")
os.makedirs(output_cleaned_dir, exist_ok=True)

# 2. 전처리 비교 결과 CSV 저장 경로
output_csv = os.path.join(current_dir, "stt_vad_noise_result.csv")

# src 폴더 내부의 stt 모듈 임포트
from src.stt import PronunciationPipeline


def main():
    # 3. 테스트 오디오 메타데이터 (파일명: 정답 문장 및 난이도 매핑)
    audio_metadata = {
        "stt_test_audio_01.wav": {"ref": "여기 어디에요?", "level": "쉬움"},
        "stt_test_audio_02.wav": {"ref": "공항에 어떻게 가요?", "level": "보통"},
        "stt_test_audio_03.wav": {"ref": "이 버스가 명동역으로 가나요?", "level": "보통"},
        "stt_test_audio_04.wav": {"ref": "체크인 하고 싶어요.", "level": "쉬움"},
        "stt_test_audio_05.wav": {"ref": "부대 시설이 어디에 있나요?", "level": "보통"}
    }

    print("PronunciationPipeline 모델 로딩 중...")
    pipeline = PronunciationPipeline(model_size="base", device="cpu", compute_type="int8")

    audio_files = sorted(glob.glob(os.path.join(audio_dir, "*.wav")))

    if not audio_files:
        print(f"'{audio_dir}' 폴더에서 .wav 파일을 찾을 수 없습니다. 오디오 파일을 확인해주세요.")
        return

    print(f" 총 {len(audio_files)}개 테스트 파일에 대해 정제 오디오 추출 및 3단계 전처리 성능 비교를 시작합니다.\n")

    results = []
    for audio_path in audio_files:
        file_name = os.path.basename(audio_path)
        meta = audio_metadata.get(file_name, {"ref": "안녕하세요", "level": "보통"})
        ref_text = meta["ref"]
        level = meta["level"]

        print(f"처리 중: {file_name} | 정답: '{ref_text}'")

        # ★ A. 키보드 소음 및 백그라운드 노이즈가 제거된 깨끗한 .wav 파일 추출 저장
        cleaned_wav_path = os.path.join(output_cleaned_dir, f"cleaned_{file_name}")
        pipeline.export_cleaned_wav(audio_path, cleaned_wav_path)

        # ★ B. 3단계 파이프라인 비교 평가 수행 (Raw vs VAD vs Denoise)
        eval_dict = pipeline.evaluate_all_pipelines(audio_path, ref_text, level)

        raw_res = eval_dict["raw"]
        vad_res = eval_dict["vad"]
        denoise_res = eval_dict["denoise"]

        # CER 개선 폭 계산 (%p)
        cer_imprv_vad = round((raw_res["cer"] - vad_res["cer"]) * 100, 2)
        cer_imprv_denoise = round((raw_res["cer"] - denoise_res["cer"]) * 100, 2)

        row = {
            "file_name": file_name,
            "reference_text": ref_text,
            "assigned_level": level,
            # Raw (전처리 전)
            "raw_transcript": raw_res["transcript"],
            "raw_cer_percent": raw_res["display"]["cer_percent"],
            "raw_score": raw_res["score"],
            # VAD (무음 제거)
            "vad_transcript": vad_res["transcript"],
            "vad_cer_percent": vad_res["display"]["cer_percent"],
            "vad_score": vad_res["score"],
            # Denoise (잡음 제거 + VAD)
            "denoise_transcript": denoise_res["transcript"],
            "denoise_cer_percent": denoise_res["display"]["cer_percent"],
            "denoise_score": denoise_res["score"],
            # 개선 효과 (%p)
            "vad_cer_improvement_p": f"{cer_imprv_vad}%p",
            "denoise_cer_improvement_p": f"{cer_imprv_denoise}%p"
        }
        results.append(row)
        print(f"   └ [비교 완료] Raw 점수: {raw_res['score']}점 ➔ Denoise 점수: {denoise_res['score']}점\n")

    # 4. 최종 결과 CSV 파일 저장
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print("=" * 70)
    print(f"모든 처리가 성공적으로 완료되었습니다!")
    print(f"정제된 깨끗한 WAV 파일 저장 폴더: {os.path.abspath(output_cleaned_dir)}")
    print(f"3단계 전처리 비교표 CSV 저장 경로: {os.path.abspath(output_csv)}")
    print("=" * 70)


if __name__ == "__main__":
    main()