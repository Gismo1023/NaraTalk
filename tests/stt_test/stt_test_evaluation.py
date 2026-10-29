# stt_test_audio 파일의 녹음을 이용해 STT 평가 데이터 csv 만들기
import os
import sys
import glob
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))      # tests/stt_test 폴더
project_root = os.path.dirname(os.path.dirname(current_dir))  # project 루트 폴더 (tests/stt_test -> tests -> project)
src_core_dir = os.path.join(project_root, "src_core")         # src_core 폴더 (stt.py, core.py 위치)

if src_core_dir not in sys.path:
    sys.path.append(src_core_dir)

try:
    from stt import PronunciationPipeline
except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    print("stt.py와 core.py 파일의 위치를 확인해주세요.")
    sys.exit(1)


def main():
    # 1. 오디오 파일이 들어있는 폴더 경로
    target_dir = os.path.join(current_dir, "stt_test_audio")
    if not os.path.exists(target_dir):
        target_dir = current_dir

    print(f"대상 오디오 디렉토리: {target_dir}")

    # 2. 10건의 오디오 파일별 [정답 문장], [난이도], [카테고리] 메타데이터 매핑
    audio_metadata = {
        "test_audio_04.wav": {"ref": "도와주세요!", "level": "쉬움", "category": "필수 기초 회화"},
        "test_audio_08.wav": {"ref": "공항에 어떻게 가요?", "level": "보통", "category": "이동 및 길찾기"},
        "test_audio_09.wav": {"ref": "이 버스가 명동역으로 가나요?", "level": "보통", "category": "이동 및 길찾기"},
        "test_audio_13.wav": {"ref": "체크인 하고 싶어요.", "level": "쉬움", "category": "숙박 및 기타"},
        "test_audio_16.wav": {"ref": "부대 시설이 어디에 있나요?", "level": "보통", "category": "숙박 및 기타"},
        "test_audio_18.wav": {"ref": "근처에 약국이 어디에 있나요?", "level": "어려움", "category": "숙박 및 기타"},
        "test_audio_21.wav": {"ref": "이것 주세요.", "level": "쉬움", "category": "가격 및 쇼핑"},
        "test_audio_23.wav": {"ref": "카드 결제 돼요?", "level": "보통", "category": "가격 및 쇼핑"},
        "test_audio_30.wav": {"ref": "맵지 않게 해주세요.", "level": "보통", "category": "식당 및 주문"},
        "test_audio_31.wav": {"ref": "추천해주실 만한 대표 메뉴가 있나요?", "level": "어려움", "category": "식당 및 주문"}
    }

    default_ref = "파일이 없습니다"
    default_level = "미정"
    default_category = "미정"

    # 3. STT 및 발음 평가 파이프라인 초기화
    print("PronunciationPipeline 모델 로딩 중...")
    pipeline = PronunciationPipeline(model_size="base", device="cpu", compute_type="int8")

    # 4. wav 파일 탐색
    audio_files = sorted(glob.glob(os.path.join(target_dir, "*.wav")))

    if not audio_files:
        print(f"'{target_dir}' 경로에서 .wav 오디오 파일을 찾지 못했습니다.")
        return

    print(f"총 {len(audio_files)}개 음성 파일에 대한 STT 및 평가를 시작합니다.\n")

    results = []
    for audio_path in audio_files:
        file_name = os.path.basename(audio_path)

        # 메타데이터 가져오기
        meta = audio_metadata.get(file_name, {
            "ref": default_ref,
            "level": default_level,
            "category": default_category
        })
        ref_text = meta["ref"]
        level = meta["level"]
        category = meta["category"]

        print(f"▶ 처리 중: {file_name} | 카테고리: [{category}] | 난이도: [{level}]")
        try:
            # stt.py의 파이프라인으로 STT 및 평가 수행
            eval_res = pipeline.evaluate(
                audio_file_path=audio_path,
                reference_text=ref_text,
                level=level
            )

            # 결과 구조화 (CSV 통계용)
            row = {
                "file_name": file_name,
                "category": category,
                "assigned_level": level,
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
            print(f"   └ [완료] 점수: {eval_res['score']}점 ({eval_res['grade']}) | 전사: '{eval_res['transcript']}'")

        except Exception as e:
            print(f"   └ [오류 발생] {file_name}: {e}")

    # 5. 결과를 `tests/stt_test` 폴더 안에 CSV 파일로 저장
    if results:
        df = pd.DataFrame(results)

        # stt_test 폴더 내부에 stt_evaluation_result.csv로 저장
        output_csv = os.path.join(current_dir, "stt_evaluation_result.csv")

        # 한글 깨짐 방지 인코딩 적용
        df.to_csv(output_csv, index=False, encoding="utf-8-sig")

        print("\n" + "=" * 65)
        print(f"처리가 완료되었습니다!")
        print(f"CSV 저장 경로: {os.path.abspath(output_csv)}")
        print("=" * 65)

        # 요약 통계 출력
        print("\n[요약 통계]")
        print(f"- 전체 처리 파일 수: {len(df)}개")
        print(f"- 전체 평균 점수: {df['score'].mean():.2f}점")
        print(f"- 전체 평균 CER(음절 오류율): {df['cer_raw'].mean() * 100:.2f}%")


if __name__ == "__main__":
    main()