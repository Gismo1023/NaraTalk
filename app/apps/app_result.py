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

        if st.button("연습하러 가기", type="primary"):
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
    st.subheader("AI가 다르게 들은 부분")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("다르게 들린 글자", details.get("substitutions", 0))

    with col2:
        st.metric("빠진 글자", details.get("deletions", 0))

    with col3:
        st.metric("더 들어간 글자", details.get("insertions", 0))

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
    st.subheader("📝 글자별로 확인하기")

    error_items = report.get("error_items", [])

    if error_items:
        import pandas as pd

        # 데이터를 보기 좋게 DataFrame으로 변환 후 매핑
        error_df = pd.DataFrame(error_items)

        # 키 이름이 다를 경우를 대비해 안전하게 리네이밍 (존재하는 컬럼만 반영)
        rename_map = {}
        if "type" in error_df.columns:
            rename_map["type"] = "결과"
        elif "error_type" in error_df.columns:
            rename_map["error_type"] = "결과"

        if "ref" in error_df.columns:
            rename_map["ref"] = "읽어야 할 글자"
        elif "reference_token" in error_df.columns:
            rename_map["reference_token"] = "읽어야 할 글자"

        if "hyp" in error_df.columns:
            rename_map["hyp"] = "AI가 들은 글자"
        elif "hypothesis_token" in error_df.columns:
            rename_map["hypothesis_token"] = "AI가 들은 글자"

        if "pos" in error_df.columns:
            rename_map["pos"] = "몇 번째 글자"
        elif "position" in error_df.columns:
            rename_map["position"] = "몇 번째 글자"

        error_df = error_df.rename(columns=rename_map)
        if "결과" in error_df.columns:
            error_df["결과"] = error_df["결과"].map({
                "insertion": "더 들어감",
                "deletion": "빠짐",
                "substitution": "다르게 들림",
            }).fillna(error_df["결과"])

        # 빈칸은 "—"로, 위치는 "5번째"처럼 표시
        for col in ("읽어야 할 글자", "AI가 들은 글자"):
            if col in error_df.columns:
                error_df[col] = error_df[col].fillna("").replace("", "—")
        if "몇 번째 글자" in error_df.columns:
            error_df["몇 번째 글자"] = error_df["몇 번째 글자"].map(
                lambda v: f"{int(v)}번째" if pd.notna(v) and str(v).strip() != "" else "—"
            )

        st.dataframe(error_df, use_container_width=True, hide_index=True)
    else:
        st.success("AI가 모든 글자를 문장과 똑같이 알아들었어요! 🎉")

    st.divider()

    if st.button("다시 연습하기", use_container_width=True, type="primary"):
        st.session_state.recorded_audio = None
        st.session_state.audio_source = None
        st.session_state.evaluation_result = None
        st.session_state.saved_run_id = None
        st.session_state.save_error = None
        st.session_state.page = "연습하기"
        st.rerun()