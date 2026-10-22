import asyncio
import os
import edge_tts
import librosa
import soundfile as sf

# normalize.py에서 정규화된 데이터베이스 불러오기
from normalize import SENTENCES_DB


async def generate_korean_tts_with_soundfile(
    sentences_db, output_dir="test_audio"
):
  """edge-tts로 음성 생성 후, soundfile과 librosa를 이용해 16kHz 모노 WAV로 전처리"""
  if not sentences_db:
    print("처리할 데이터가 없습니다. text.csv 및 normalize.py를 확인해주세요.")
    return

  os.makedirs(output_dir, exist_ok=True)
  voice_name = "ko-KR-SunHiNeural"

  print("=== 한국어 텍스트 오디오 생성 및 전처리 ===")

  file_count = 0
  for category, items in sentences_db.items():
    print(f"\n[카테고리] {category}")
    for item in items:
      ko_text = item["ko"]
      file_count += 1

      temp_filename = f"temp_{file_count:02d}.mp3"
      temp_path = os.path.join(output_dir, temp_filename)

      final_filename = f"ko_test_{file_count:02d}.wav"
      final_path = os.path.join(output_dir, final_filename)

      try:
        # 1. edge-tts로 음성 생성
        communicate = edge_tts.Communicate(ko_text, voice_name)
        await communicate.save(temp_path)

        # 2. librosa를 이용해 16kHz, 모노(mono=True)로 오디오 로드 및 리샘플링

        audio_data, sample_rate = librosa.load(temp_path, sr=16000, mono=True)

        # 3. soundfile을 이용해 표준 WAV 파일로 저장
        sf.write(final_path, audio_data, 16000, subtype="PCM_16")

        # 4. 임시 파일 삭제
        if os.path.exists(temp_path):
          os.remove(temp_path)

        print(
            f" [생선후 변환 완료] '{ko_text}' -> {final_path}"
            " (Mono, 16kHz)"
        )

      except Exception as e:
        print(f"  [실패] '{ko_text}' 처리 중 에러 발생: {e}")
        if os.path.exists(temp_path):
          os.remove(temp_path)

  print(f"\n {file_count}개의 파일 생성 및 변환 완료")


if __name__ == "__main__":
  asyncio.run(generate_korean_tts_with_soundfile(SENTENCES_DB))