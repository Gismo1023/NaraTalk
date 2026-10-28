# app_practice.py

import os
import sys
import tempfile
from pathlib import Path
import streamlit as st
from korean_romanizer.romanizer import Romanizer # 발음표기

PROJECT_DIR = Path(__file__).resolve().parents[2]

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.tts import generate_audio_on_fly
<<<<<<< HEAD
from src.db import get_sentences, save_practice_run
=======
from src.db import get_sentences, save_practice_run, save_error_items
>>>>>>> 06d9502f299fbbabe506eeac4fe92f871b6fb343
from src.stt import PronunciationPipeline
# 버전 호환성
import av

_original_av_open = av.open


def compatible_av_open(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _original_av_open(*args, **kwargs)


av.open = compatible_av_open


def get_pronunciation(korean_sentence):
    """한국어 문장을 로마자 표기로 변환한다."""
    if not korean_sentence:
        return ""

    romanizer = Romanizer(korean_sentence)
    return romanizer.romanize()


@st.cache_resource
def load_stt_pipeline():
    return PronunciationPipeline(
        model_size="base",
        device="cpu",
        compute_type="int8",
    )


def page_practice():
    st.title("연습하기")
    st.write("연습할 문장을 선택한 후 한국어로 읽어 보세요.")

    st.divider()
    st.subheader("1. 연습 조건")

    # DB에서 연습 문장 조회
    try:
        all_sentences = get_sentences()
    except Exception as e:
        st.error(f"연습 문장을 불러오지 못했습니다: {e}")
        return

    # 카테고리와 난이도 좌우 배치
    col_category, col_level = st.columns(2)

    # DB 데이터가 없는 경우
    if not all_sentences:
        categories = ["카테고리를 선택하세요"]
        selected_category = categories[0]
        levels = ["난이도를 선택하세요"]
        selected_level = levels[0]
        filtered_sentences = []

        with col_category:
            st.selectbox(
                "카테고리",
                options=categories,
                disabled=True,
                key="skeleton_category",
            )

        with col_level:
            st.selectbox(
                "난이도",
                options=levels,
                disabled=True,
                key="skeleton_level",
            )

    else:
        # DB에 저장된 카테고리 목록
        categories = list(dict.fromkeys(
            row["category"] for row in all_sentences
        ))

        with col_category:
            selected_category = st.selectbox(
                "카테고리",
                options=categories,
                key="skeleton_category",
            )

        # 선택한 카테고리에 해당하는 문장
        category_sentences = [
            row for row in all_sentences
            if row["category"] == selected_category
        ]

        # 난이도 표시 순서
        level_order = ["쉬움", "보통", "어려움"]

        levels = [
            level for level in level_order
            if any(
                row["level"] == level
                for row in category_sentences
            )
        ]

        if not levels:
            levels = ["난이도를 선택하세요"]

        with col_level:
            selected_level = st.selectbox(
                "난이도",
                options=levels,
                key="skeleton_level",
                disabled=not category_sentences,
            )

        # 선택한 카테고리와 난이도에 맞는 문장
        filtered_sentences = [
            row for row in category_sentences
            if row["level"] == selected_level
        ]

    # 기존 안내 문구 유지
    st.caption(
        "카테고리와 난이도 데이터 연결 후 선택 항목이 표시됩니다."
    )

    # 문장 번호를 기준으로 문장 선택
    sentence_by_no = {
        row["sentence_no"]: row
        for row in filtered_sentences
    }

    if sentence_by_no:
        sentence_numbers = list(sentence_by_no.keys())

        selected_sentence_no = st.selectbox(
            "연습할 문장",
            options=sentence_numbers,
            format_func=lambda no: (
                f"{sentence_by_no[no]['ko']}"
            ),
            key="skeleton_sentence",
        )

        selected_sentence = sentence_by_no[selected_sentence_no]

        korean_sentence = selected_sentence["ko"]
        english_translation = selected_sentence["en"]

    else:
        st.selectbox(
            "연습할 문장",
            options=["연습 문장을 선택하세요"],
            disabled=True,
            key="skeleton_sentence",
        )

        korean_sentence = "연습 문장이 표시될 영역입니다."
        english_translation = "영어 번역이 표시될 영역입니다."

    # 선택한 한국어 문장을 로마자 표기로 변환
    pronunciation = get_pronunciation(
        korean_sentence
    ) if sentence_by_no else ""

    st.divider()
    st.subheader("2. 연습 문장")

    # 한국어 문장
    with st.container(border=True):
        st.markdown(
            """<div style="color:#60A5FA; font-size:16px;
            font-weight:700; margin-bottom:10px;">
            💬 한국어 문장</div>""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""<div style="font-size:16px; font-weight:400;
            line-height:1.7;">{korean_sentence}</div>""",
            unsafe_allow_html=True,
        )

        # 선택한 한국어 문장 읽기 버튼
        if st.button("🔊 문장 듣기"):
            # 이전 TTS 캐시 삭제
            generate_audio_on_fly.clear()
            # 현재 선택한 문장으로 음성 생성
            audio_path = generate_audio_on_fly(korean_sentence)
            # 생성된 음성을 메모리에 읽기
            with open(audio_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
            # 음성 재생
            st.audio(audio_bytes, format="audio/wav")

    # 영어 번역
    with st.container(border=True):
        st.markdown(
            """<div style="color:#34D399; font-size:16px;
            font-weight:700; margin-bottom:10px;">
            🌐 영어 번역</div>""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""<div style="font-size:16px; font-weight:400;
            line-height:1.7;">{english_translation}</div>""",
            unsafe_allow_html=True,
        )

    # 영어 알파벳을 이용한 한국어 로마자 표기
    with st.container(border=True):
        st.markdown(
            """<div style="color:#FBBF24; font-size:16px;
            font-weight:700; margin-bottom:10px;">
            🔊 영어 발음 표기</div>""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""<div style="font-size:16px; font-weight:400;
            line-height:1.7;">{pronunciation}</div>""",
            unsafe_allow_html=True,
        )

    # 음성 입력
    st.divider()
    st.subheader("3. 음성 입력")

    audio_data = st.audio_input(
        "마이크로 녹음하기",
        key="practice_audio_input",
    )

    uploaded_audio = st.file_uploader(
        "음성 파일 업로드",
        type=["wav", "mp3", "m4a"],
        key="practice_audio_upload",
    )

    # 녹음 또는 업로드한 음성 보관
    if audio_data is not None:
        st.session_state.recorded_audio = audio_data
        st.session_state.audio_source = "record"

    elif uploaded_audio is not None:
        st.session_state.recorded_audio = uploaded_audio
        st.session_state.audio_source = "upload"

    # 입력 완료 및 발음 평가
    if st.button("입력 완료", key="practice_submit"):
        recorded_audio = st.session_state.get("recorded_audio")

        if recorded_audio is None:
            st.warning("먼저 음성을 녹음하거나 파일을 업로드해 주세요.")

        elif not sentence_by_no:
            st.warning("평가할 연습 문장을 먼저 선택해 주세요.")

        else:
            audio_path = None

            try:
                # 임시 음성 파일 저장 폴더 준비
                audio_dir = PROJECT_DIR / "temp_audio"
                audio_dir.mkdir(parents=True, exist_ok=True)

                # 녹음 또는 업로드한 음성 데이터 가져오기
                audio_bytes = recorded_audio.getvalue()

                if not audio_bytes:
                    st.warning("입력된 음성이 비어 있습니다.")

                else:
                    # 업로드 파일의 확장자 확인
                    if st.session_state.audio_source == "upload":
                        uploaded = st.session_state.get(
                            "practice_audio_upload"
                        )
                        suffix = Path(uploaded.name).suffix.lower()

                        if suffix not in [".wav", ".mp3", ".m4a"]:
                            suffix = ".wav"
                    else:
                        suffix = ".wav"

                    # STT가 처리할 임시 파일 생성
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=suffix,
                        dir=str(audio_dir),
                    ) as temp_file:
                        temp_file.write(audio_bytes)
                        audio_path = temp_file.name

                    # STT 실행 및 발음 평가
                    with st.spinner(
                        "음성을 분석하고 있습니다. 잠시 기다려 주세요."
                    ):
                        pipeline = load_stt_pipeline()

                        report = pipeline.evaluate(
                            audio_file_path=audio_path,
                            reference_text=korean_sentence,
                            level=selected_sentence["level"],
                        )

                    # 결과 화면에서 사용할 데이터 저장
                    st.session_state.evaluation_result = report
                    st.session_state.selected_sentence = selected_sentence

                    # 연습 결과 DB 저장
                    st.session_state.saved_run_id = None
                    st.session_state.save_error = None

                    try:
                        details = report["cer_details"]
                        run_id = save_practice_run(
                            user_id=st.session_state.user_id,
                            sentence_id=selected_sentence["id"],
                            transcript=report["transcript"],
                            wer=report["wer"],
                            cer=report["cer"],
                            latency_ms=report["latency_ms"],
                            score=report["score"],
                            grade=report["grade"],
                            feedback=report["feedback"],
                            substitutions=details["substitutions"],
                            deletions=details["deletions"],
                            insertions=details["insertions"],
                        )
                        st.session_state.saved_run_id = run_id
<<<<<<< HEAD
=======

                        # 글자 단위 오류 위치 저장 (B06) → error_items 테이블
                        st.session_state.saved_error_count = save_error_items(
                            run_id, report.get("error_items", [])
                        )
>>>>>>> 06d9502f299fbbabe506eeac4fe92f871b6fb343
                    except Exception as error:
                        st.session_state.save_error = str(error)

                    # 결과 화면으로 이동
                    st.session_state.page = "결과"
                    st.rerun()

            except Exception as e:
                st.error(f"음성 분석 중 오류가 발생했습니다: {e}")
                st.exception(e)

            finally:
                # 임시 파일 정리
                if audio_path and os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except OSError:
                        pass
