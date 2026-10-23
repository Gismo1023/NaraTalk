import asyncio
import os
import edge_tts
import librosa
import soundfile as sf
import streamlit as st

# normalize.py에서 정규화된 데이터베이스 불러오기
from normalize import SENTENCES_DB

st.set_page_config(
    page_title="한국어 학습 및 음성 플레이어", layout="centered"
)

st.title("🎤 한국어 학습 및 오디오 플레이어")
st.write(
    "카테고리와 난이도('쉬움', '보통', '어려움')를 선택하고 문장을 학습해"
    " 보세요!"
)

if not SENTENCES_DB:
  st.error("처리할 데이터가 없습니다. text.csv 및 normalize.py를 확인해주세요.")
  st.stop()

# 1. 카테고리 선택
categories = list(SENTENCES_DB.keys())
selected_category = st.selectbox("📂 카테고리를 선택하세요", categories)

# 2. 선택된 카테고리에 속한 아이템들 가져오기
category_items = SENTENCES_DB.get(selected_category, [])

# 3. 난이도 고정 선택지 제공 (쉬움, 보통, 어려움)
# 데이터에 실제로 존재하는 난이도만 필터링하거나 기본 순서대로 배치할 수 있습니다.
fixed_difficulties = ["쉬움", "보통", "어려움"]

# 실제 데이터에 존재하는 난이도만 추려내되, 위 순서대로 정렬
present_difficulties = [
    d
    for d in fixed_difficulties
    if any(item.get("difficulty") == d for item in category_items)
]

# 만약 데이터에 위 3가지 외에 다른 값이 있거나 할 경우를 대비한 예외 처리
if not present_difficulties:
  present_difficulties = sorted(
      list(set(item.get("difficulty", "보통") for item in category_items))
  )

selected_difficulty = st.selectbox("📊 난이도를 선택하세요", present_difficulties)

# 4. 카테고리와 난이도가 일치하는 문장 필터링
filtered_items = [
    item
    for item in category_items
    if item.get("difficulty") == selected_difficulty
]

st.markdown("---")

if not filtered_items:
  st.warning(
      f"'{selected_category}' 카테고리에 난이도 '{selected_difficulty}'에"
      " 해당하는 문장이 없습니다."
  )
else:
  st.subheader(
      f"📝 문장 목록 (카테고리: {selected_category} / 난이도:"
      f" {selected_difficulty})"
  )

  # 한국어 텍스트를 key로 하고 전체 item을 value로 하는 딕셔너리 생성
  sentence_options = {item["ko"]: item for item in filtered_items}

  # 학습할 문장 선택 (Selectbox)
  selected_ko_text = st.selectbox(
      "학습할 문장을 선택하세요", list(sentence_options.keys())
  )

  if selected_ko_text:
    selected_item = sentence_options[selected_ko_text]
    en_text = selected_item.get("en", "영어 번역 없음")

    # 결과 출력 영역
    st.markdown("### 💬 선택한 문장 정보")
    st.info(f"**한국어:** {selected_ko_text}")
    st.success(f"**영어:** {en_text}")


    # 오디오 생성 및 재생 함수 (캐싱 적용)
    @st.cache_resource
    def generate_audio_on_fly(text):
      os.makedirs("temp_audio", exist_ok=True)
      temp_path = "temp_audio/current_target.wav"

      async def _synth():
        communicate = edge_tts.Communicate(text, "ko-KR-SunHiNeural")
        await communicate.save("temp_audio/temp.mp3")

        audio_data, _ = librosa.load(
            "temp_audio/temp.mp3", sr=16000, mono=True
        )
        sf.write(temp_path, audio_data, 16000, subtype="PCM_16")

        if os.path.exists("temp_audio/temp.mp3"):
          os.remove("temp_audio/temp.mp3")

      asyncio.run(_synth())
      return temp_path


    # 오디오 파일 생성 및 재생 버튼
    if st.button("🔊 원어민 음성 듣기"):
      with st.spinner("음성을 생성하는 중입니다..."):
        audio_file_path = generate_audio_on_fly(selected_ko_text)
        st.audio(audio_file_path, format="audio/wav")