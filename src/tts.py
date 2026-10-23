import asyncio
import os
from pathlib import Path
import edge_tts
import librosa
import soundfile as sf
import streamlit as st


# 오디오 생성 및 재생 함수 (캐싱 적용)
@st.cache_resource
def generate_audio_on_fly(text):
    audio_dir = Path(__file__).resolve().parent.parent / "temp_audio"
    os.makedirs(audio_dir, exist_ok=True)
    temp_path = str(audio_dir / "current_target.wav")

    async def _synth():
        communicate = edge_tts.Communicate(
            text, "ko-KR-SunHiNeural"
        )
        await communicate.save(str(audio_dir / "temp.mp3"))

        audio_data, _ = librosa.load(
            str(audio_dir / "temp.mp3"), sr=16000, mono=True
        )
        sf.write(
            temp_path, audio_data, 16000, subtype="PCM_16"
        )

        if os.path.exists(str(audio_dir / "temp.mp3")):
            os.remove(str(audio_dir / "temp.mp3"))

    asyncio.run(_synth())
    return temp_path