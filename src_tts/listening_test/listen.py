# tts 자연스러움 명료도 청취평가 기록 csv
import time
import pandas as pd
from pathlib import Path
import asyncio
import re
import sys

# 부모 디렉토리(src_tts)의 모듈을 임포트하기 위해 sys.path에 추가
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# normalize.py에서 전처리 함수 임포트
try:
    from normalize import normalize_korean
except ImportError:
    from normalize import normalize_text as normalize_korean

# 경로 설정
text_csv_path = parent_dir / "text.csv"
output_audio_dir = current_dir / "saved_audio"  # 오디오가 저장될 폴더
output_csv_path = current_dir / "listening_results.csv"

# 오디오 저장 폴더 생성
output_audio_dir.mkdir(parents=True, exist_ok=True)


async def generate_tts(text: str, output_path: Path):
    """edge-tts를 이용해 한국어 텍스트를 오디오 파일로 저장"""
    import edge_tts
    voice = "ko-KR-SunHiNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


def main():
    if not text_csv_path.exists():
        return

    # text.csv 읽기
    df = pd.read_csv(text_csv_path)

    # 한국어('ko') 데이터만 필터링
    if 'lang' in df.columns:
        df = df[df['lang'] == 'ko'].reset_index(drop=True)
    elif 'language' in df.columns:
        df = df[df['language'] == 'ko'].reset_index(drop=True)

    # 📌 [핵심] 기존에 이미 작성한 결과(점수, 채점자 등)가 있다면 불러와서 유지하기 위함
    existing_data = {}
    if output_csv_path.exists():
        try:
            old_df = pd.read_csv(output_csv_path, encoding="utf-8-sig")
            for _, row in old_df.iterrows():
                key = str(row.get("text", "")).strip()
                existing_data[key] = {
                    "자연스러움": row.get("자연스러움", ""),
                    "명료도": row.get("명료도", ""),
                    "채점자": row.get("채점자", "")
                }
        except Exception:
            pass

    results = []

    print("[생성 중...]")

    for idx, row in df.iterrows():
        category = str(row.get('category', 'N/A')).strip()
        difficulty = str(row.get('difficulty', 'N/A')).strip()

        # 진짜 한국어 문장 추출
        raw_text = str(
            row.get('text') or
            row.get('sentence') or
            row.get('ko') or
            row.get('ref') or
            row.iloc[2]
        ).strip()

        cleaned_text = normalize_korean(raw_text)

        # 윈도우 파일명 에러 방지: 특수문자 제거
        safe_text_for_filename = re.sub(r'[\/:*?"<>|!?.,]', '', cleaned_text)
        safe_text_for_filename = safe_text_for_filename.strip().replace(" ", "_")[:20]

        audio_filename = f"{category}_{difficulty}_{safe_text_for_filename}.wav"
        audio_path = output_audio_dir / audio_filename

        # 처리 지연 시간 (Latency) 측정 시작
        start_time = time.time()

        # TTS 오디오 생성 및 저장 (비동기 실행)
        asyncio.run(generate_tts(cleaned_text, audio_path))

        end_time = time.time()
        latency = end_time - start_time

        # 📌 기존에 작성했던 점수와 채점자 이름이 있으면 가져오고, 없으면 빈 칸으로 유지
        saved_score = existing_data.get(cleaned_text, {})

        results.append({
            "카테고리": category,
            "난이도": difficulty,
            "text": cleaned_text,
            "걸린시간": f"{latency:.4f}",
            "자연스러움": saved_score.get("자연스러움", ""),
            "명료도": saved_score.get("명료도", ""),
            "채점자": saved_score.get("채점자", "")
        })

    # 최종 결과 CSV 저장
    result_df = pd.DataFrame(results)
    result_df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")

    print("[생성 완료]")


if __name__ == "__main__":
    main()