import asyncio
import os
import edge_tts

# 1. 사용할 음성 (기본 한국어 보이스 중 자연스러운 톤)
VOICE = "ko-KR-SunHiNeural"  # 또는 "ko-KR-InJoonNeural"

# 2. 저장할 폴더 이름 설정
OUTPUT_DIR = "test용 audio"


async def generate_foreign_accent_wav(text: str, output_path: str):
    """
    Edge-TTS를 사용하여 텍스트를 wav 파일로 변환합니다.
    rate를 살짝 느리게(-5%) 설정하여 외국인 학습자의 발화 템포를 유도합니다.
    """
    communicate = edge_tts.Communicate(text, VOICE, rate="-5%")
    await communicate.save(output_path)


async def main():
    # 텍스트(CSV) 파일 이름
    csv_filename = "test.txt"

    if not os.path.exists(csv_filename):
        print(f"오류: {csv_filename} 파일이 존재하지 않습니다. 파일을 확인해주세요!")
        return

    # 저장할 폴더가 없으면 자동으로 생성
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"'{OUTPUT_DIR}' 폴더를 새로 생성했습니다.")

    with open(csv_filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    data_lines = [line.strip() for line in lines if line.strip()]

    if "category" in data_lines[0] and "ko" in data_lines[0]:
        data_lines = data_lines[1:]

    print(f"총 {len(data_lines)}개의 문장을 음성 파일(.wav)로 변환합니다...\n")

    for i, line in enumerate(data_lines):
        parts = line.split(",")
        if len(parts) < 4:
            continue

        category = parts[0].strip()
        ko_text = parts[1].strip()
        difficulty = parts[-1].strip()

        # 파일명 특수문자/공백 정제
        safe_category = category.replace("/", "_").replace(" ", "_")
        safe_difficulty = difficulty.replace(" ", "_")

        # 파일 이름 설정 및 'test용 audio' 폴더 경로와 결합
        filename = f"{safe_category}_{safe_difficulty}_{i + 1:02d}.wav"
        output_path = os.path.join(OUTPUT_DIR, filename)

        print(f"진행 상황 [{i + 1}/{len(data_lines)}] 변환 중: '{ko_text}' -> {output_path}")

        # 음성 파일 생성 실행
        await generate_foreign_accent_wav(ko_text, output_path)

    print(f"\n모든 평가용 wav 파일 생성이 완료되었습니다! (저장 폴더: ./{OUTPUT_DIR})")


if __name__ == "__main__":
    asyncio.run(main())