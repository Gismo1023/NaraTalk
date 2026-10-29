# app_result.py

import streamlit as st
from korean_romanizer.romanizer import Romanizer


def get_pronunciation(korean_sentence):
    """한국어 문장을 로마자 표기로 변환한다."""
    if not korean_sentence:
        return ""

    romanizer = Romanizer(korean_sentence)
    return romanizer.romanize()


def page_result():
    st.title("연습 결과")

    report = st.session_state.get("evaluation_result")
    selected_sentence = st.session_state.get("selected_sentence")

    if not report:
        st.info("아직 평가 결과가 없습니다. 먼저 음성 연습을 진행해 주세요.")

        if st.button("연습하러 가기"):
            st.session_state.page = "연습하기"
            st.rerun()

        return

    if st.session_state.get("save_error"):
        st.warning("평가는 완료됐지만 DB에 학습 기록을 저장하지 못했습니다.")
    elif st.session_state.get("saved_run_id"):
        st.success("학습 결과를 확인해 주세요.")

    details = report.get("cer_details", {})

    st.subheader("결과 요약")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("단어 오류율(wer)", f"{report['wer'] * 100:.1f}%")

    with col2:
        st.metric("글자/발음 오류율(cer)", f"{report['cer'] * 100:.1f}%")

    with col3:
        st.metric(
            "분석 시간",
            f"{report['latency_ms'] / 1000:.2f}초",
        )

    st.divider()
    st.subheader("문장 비교")

    # 하나의 폼 안에서 항목별로 구분
    with st.container(border=True):
        # 기준 문장
        st.markdown(
            """
            <div style="
                color: #60A5FA;
                font-size: 16px;
                font-weight: 700;
                margin-bottom: 8px;
            ">
                💬 기준 문장
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write(report.get("reference_text", ""))

        st.divider()

        # 인식된 문장
        st.markdown(
            """
            <div style="
                color: #F87171;
                font-size: 16px;
                font-weight: 700;
                margin-bottom: 8px;
            ">
                🎙️ 인식된 문장
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write(
            report.get("transcript", "")
            or "인식된 문장이 없습니다."
        )

        st.divider()

        # 영어 번역
        st.markdown(
            """
            <div style="
                color: #34D399;
                font-size: 16px;
                font-weight: 700;
                margin-bottom: 8px;
            ">
                🌐 영어 번역
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write(
            selected_sentence.get("en", "")
            if selected_sentence
            else "번역 정보가 없습니다."
        )

        st.divider()

        # 영어 발음 표기
        st.markdown(
            """
            <div style="
                color: #FBBF24;
                font-size: 16px;
                font-weight: 700;
                margin-bottom: 8px;
            ">
                🔊 영어 발음 표기
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write(
            get_pronunciation(
                report.get("reference_text", "")
            )
        )

    st.divider()
    st.subheader("발음 및 문장 오류")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("대치 오류", details.get("substitutions", 0))

    with col2:
        st.metric("삭제 오류", details.get("deletions", 0))

    with col3:
        st.metric("삽입 오류", details.get("insertions", 0))

    st.divider()
    st.subheader("녹음 음성")

    # 연습하기 화면에서 전달받은 음성 재생
    recorded_audio = st.session_state.get("recorded_audio")
    audio_source = st.session_state.get("audio_source")

    if recorded_audio is not None:
        if audio_source:
            st.caption(f"입력 방식: {audio_source}")

        # 업로드한 파일 형식에 맞춰 음성 재생 (추가부분)
        audio_format = "audio/wav"
        if audio_source == "upload":
            file_name = recorded_audio.name.lower()
            if file_name.endswith(".mp3"):
                audio_format = "audio/mpeg"
            elif file_name.endswith(".m4a"):
                audio_format = "audio/mp4"

        st.audio(
            recorded_audio,
            format=audio_format,
        )
    else:
        st.info("녹음하거나 업로드한 음성이 없습니다.")

    st.divider()
    st.subheader("피드백")

    with st.container(border=True):
        st.metric(
            "발음 점수",
            f"{report.get('score', 0):.1f}점",
        )
        st.write(f"**평가 등급:** {report.get('grade', '-')}")
        st.write(
            f"**피드백:** "
            f"{report.get('feedback', '피드백이 없습니다.')}"
        )

        # 오류(오답) 및 오류유형 표시 (상세 오답 노트 테이블 추가)
    st.divider()
    st.subheader("📝 상세 오답 노트")

    error_items = report.get("error_items", [])

    if error_items:
        import pandas as pd

        # 데이터를 보기 좋게 DataFrame으로 변환 후 매핑
        error_df = pd.DataFrame(error_items)

        # 키 이름이 다를 경우를 대비해 안전하게 리네이밍 (존재하는 컬럼만 반영)
        rename_map = {}
        if "type" in error_df.columns:
            rename_map["type"] = "오류 유형"
        elif "error_type" in error_df.columns:
            rename_map["error_type"] = "오류 유형"

        if "ref" in error_df.columns:
            rename_map["ref"] = "정답 토큰"
        elif "reference_token" in error_df.columns:
            rename_map["reference_token"] = "정답 토큰"

        if "hyp" in error_df.columns:
            rename_map["hyp"] = "인식 토큰"
        elif "hypothesis_token" in error_df.columns:
            rename_map["hypothesis_token"] = "인식 토큰"

        if "pos" in error_df.columns:
            rename_map["pos"] = "위치"
        elif "position" in error_df.columns:
            rename_map["position"] = "위치"

        error_df = error_df.rename(columns=rename_map)
        if "오류 유형" in error_df.columns:
            error_df["오류 유형"] = error_df["오류 유형"].map({
                "insertion": "삽입 오류",
                "deletion": "삭제 오류",
                "substitution": "대치 오류",
            }).fillna(error_df["오류 유형"])

        st.dataframe(error_df, use_container_width=True, hide_index=True)
    else:
        st.success("틀린 글자 없이 완벽하게 발음하셨습니다! 🎉")

    st.divider()

    if st.button("다시 연습하기", use_container_width=True):
        st.session_state.recorded_audio = None
        st.session_state.audio_source = None
        st.session_state.evaluation_result = None
        st.session_state.saved_run_id = None
        st.session_state.save_error = None
        st.session_state.page = "연습하기"
        st.rerun()