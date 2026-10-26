# 생성된 TTS 음성 파일들을 대상으로 STT 추론 및 발음/인식 정확도 평가 CSV 추출
import os
import sys
import glob
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))  # tts/tts_test 폴더
tts_dir = os.path.dirname(current_dir)                    # tts 폴더
project_root = os.path.dirname(tts_dir)                   # project 루트 폴더
stt_dir = os.path.join(project_root, "stt")               # stt.py가 있는 stt 폴더
src_core_dir = os.path.join(project_root, "src_core")     # core.py가 있는 src_core 폴더

if stt_dir not in sys.path:
    sys.path.append(stt_dir)
if src_core_dir not in sys.path:
    sys.path.append(src_core_dir)
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from stt import PronunciationPipeline
except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    print(f"탐색된 stt 경로: {stt_dir}")
    sys.exit(1)


def main():
    # 1. 경로 설정 (tests/ 폴더에 있는 test.txt와 test용 audio 폴더 지정)
    txt_filename = os.path.join(project_root, "tests", "test.txt")
    audio_dir = os.path.join(project_root, "tests", "test용 audio")

    # 결과 CSV는 현재 폴더(tts/tts_test/)에 저장
    output_csv = os.path.join(current_dir, "tts_evaluation_results.csv")

    if not os.path.exists(txt_filename):
        print(f"오류: {txt_filename} 파일을 찾을 수 없습니다.")
        return

    if not os.path.exists(audio_dir):
        print(f"오류: {audio_dir} 폴더를 찾을 수 없습니다.")
        return

    # 2. STT 및 평가 파이프라인 초기화
    print("PronunciationPipeline 모델 로딩 중...")
    pipeline = PronunciationPipeline(model_size="base", device="cpu", compute_type="int8")

    # 3. test.txt 파일 읽기
    with open(txt_filename, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    if "category" in lines[0] and "ko" in lines[0]:
        lines = lines[1:]

    print(f"총 {len(lines)}개의 TTS 음성 파일에 대한 평가를 시작합니다.\n")

    results = []

    for i, line in enumerate(lines):
        parts = line.split(",")
        if len(parts) < 4:
            continue

        category = parts[0].strip()
        ko_text = parts[1].strip()
        difficulty = parts[-1].strip()

        safe_category = category.replace("/", "_").replace(" ", "_")
        safe_difficulty = difficulty.replace(" ", "_")
        filename = f"{safe_category}_{safe_difficulty}_{i + 1:02d}.wav"
        audio_path = os.path.join(audio_dir, filename)

        if not os.path.exists(audio_path):
            print(f"⚠️ 경고: 음성 파일을 찾을 수 없습니다 - {audio_path}")
            continue

        print(f"처리 중 [{i + 1}/{len(lines)}]: {filename} | 정답: '{ko_text}'")

        try:
            eval_res = pipeline.evaluate(
                audio_file_path=audio_path,
                reference_text=ko_text,
                level=difficulty
            )

            row = {
                "file_name": filename,
                "category": category,
                "assigned_level": difficulty,
                "reference_text": eval_res["reference_text"],
                "transcript": eval_res["transcript"],
                "cer_percent": eval_res["display"]["cer_percent"],
                "wer_percent": eval_res["display"]["wer_percent"],
                "cer_raw": eval_res["cer"],
                "wer_raw": eval_res["wer"],
                "substitutions": eval_res["cer_details"]["substitutions"],
                "deletions": eval_res["cer_details"]["deletions"],
                "insertions": eval_res["cer_details"]["insertions"],
                "score": eval_res["score"],
                "grade": eval_res["grade"],
                "feedback": eval_res["feedback"],
                "latency_ms": eval_res["latency_ms"],
                "created_at": eval_res["created_at"]
            }
            results.append(row)
            print(f"   └ [완료] 인식 텍스트: '{eval_res['transcript']}' | 점수: {eval_res['score']}점 ({eval_res['grade']})")

        except Exception as e:
            print(f"   └ [오류 발생] {filename}: {e}")

    if results:
        df = pd.DataFrame(results)
        df.to_csv(output_csv, index=False, encoding="utf-8-sig")

        print("\n" + "=" * 65)
        print(f"🎉 TTS 평가 완료!")
        print(f"📄 CSV 저장 경로: {os.path.abspath(output_csv)}")
        print("=" * 65)

        print("\n[📊 요약 통계]")
        print(f"- 평가 완료된 파일 수: {len(df)}개")
        print(f"- 전체 평균 점수: {df['score'].mean():.2f}점")
        print(f"- 전체 평균 CER(음절 오류율): {df['cer_raw'].mean() * 100:.2f}%")
        print(f"- 전체 평균 WER(어절 오류율): {df['wer_raw'].mean() * 100:.2f}%")
    else:
        print("⚠️ 저장할 평가 결과가 없습니다.")


if __name__ == "__main__":
    main()