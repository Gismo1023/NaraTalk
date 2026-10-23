# python -m streamlit run app/app.py
import streamlit as st
import pandas as pd
import os
import tempfile
from datetime import date
# 한국어 >> 영어 발음표기 변환함수 모듈
from korean_romanizer.romanizer import Romanizer
import sys
from pathlib import Path
from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent.parent

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# src 폴더 안의 .env 파일 읽기
ENV_PATH = PROJECT_DIR / "src" / ".env"
load_dotenv(ENV_PATH, override=True)

# tts 파일 불러오기
from src.tts import generate_audio_on_fly
# db 테이블 연습문장 가져오기
from src.db import (get_sentences, register_user, login_user, )
# STT 및 평가 모듈 경로 설정
from src.stt import PronunciationPipeline
# 호환성 문제
import av

_original_av_open = av.open

def compatible_av_open(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _original_av_open(*args, **kwargs)

av.open = compatible_av_open
#==============================================================
def get_pronunciation(korean_sentence):
    """한국어 문장을 로마자 표기로 변환한다."""
    if not korean_sentence:
        return ""

    romanizer = Romanizer(korean_sentence)
    return romanizer.romanize()

# stt 모델 불러오기
@st.cache_resource
def load_stt_pipeline():
    return PronunciationPipeline(
        model_size="base",
        device="cpu",
        compute_type="int8",
    )

# 기본 설정
st.set_page_config(
    page_title="나랏말싸미",
    page_icon="🇰🇷",
    layout="wide"
)

# 세션 상태 초기화
def init_state():
    defaults = {
        "user_name": "",
        "user_id":None,
        "entered": False,
        "page": "시작",
        "recorded_audio": None,
        "audio_source": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# 공통 스타일
def apply_style():
    st.markdown(
        """
        <style>
        .section-label {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 10px;
        }

        .section-content {
            font-size: 16px;
            font-weight: 400;
            line-height: 1.7;
            overflow-wrap: anywhere;
        }

        .placeholder {
            opacity: 0.65;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# 사이드바 메뉴 변경 콜백
def change_page():
    st.session_state.page = st.session_state.sidebar_menu


# 사이드바
def show_sidebar():
    with st.sidebar:
        st.title("🇰🇷 나랏말싸미")
        st.divider()

        pages = [
            "홈",
            "연습하기",
            "결과",
            "학습 이력",
            "분석 대시보드",
        ]

        # 현재 페이지에 맞게 사이드바 상태 설정
        if st.session_state.page not in pages:
            st.session_state.page = "홈"

        if st.session_state.get("sidebar_menu") != st.session_state.page:
            st.session_state.sidebar_menu = st.session_state.page

        st.selectbox(
            "메뉴",
            pages,
            key="sidebar_menu",
            on_change=change_page,
        )

        st.divider()
        st.caption("집현전 해요")


# 시작 화면
def page_start():
    _, center, _ = st.columns([1, 2, 1])

    with center:
        st.title("🇰🇷 나랏말싸미")
        st.caption("한국어 발음 연습")

        st.markdown(
            "<div style='height: 40px;'></div>",
            unsafe_allow_html=True
        )

        st.markdown("### 음성 파일 이용 동의 안내")

        with st.expander("내용 보기", expanded=False):
            st.markdown("""
                **외국인 한국어 발음 교정 서비스 - 음성 녹음 및 데이터 수집 이용 동의서**

                **1. 수집 및 이용 목적**
                - 외국인 학습자의 한국어 발음 정확도 평가 및 오류 분석 (STT 모델 활용)
                - 개인 맞춤형 발음 피드백 및 모범 음성(TTS) 품질 고도화

                **2. 수집하는 항목**
                - 음성 녹음 파일 (.wav) 및 사용자가 발화한 텍스트 스크립트
                - 발음 평가 점수 및 오류율(WER/CER) 메타데이터

                **3. 보유 및 이용 기간**
                - 프로젝트 개발 및 평가 기간 동안만 한시적으로 활용하며,
                  프로젝트 종료(또는 모델 학습 완료) 즉시 원본 음성 데이터는 안전하게 파기합니다.

                **4. 동의 거부 권리 및 불이익**
                - 이용자는 음성 녹음 수집에 대한 동의를 거부할 수 있습니다.
                - 단, 동의를 거부하실 경우 음성 기반 발음 연습 및 실시간 피드백 서비스 이용이 제한될 수 있습니다.
            """)

        agreed = st.checkbox(
            "위 안내 내용을 확인했으며 이에 동의합니다."
        )

        user_name = st.text_input(
            "이름",
            disabled=not agreed,
            placeholder=(
                "동의 후 이름을 입력해 주세요."
                if not agreed
                else "이름을 입력해 주세요."
            ),
        )

        if st.button(
                "시작하기",
                use_container_width=True,
                disabled=not agreed or not user_name.strip(),
        ):
            nickname = user_name.strip()

            try:
                # 기존 회원인지 조회
                user = login_user(nickname)

                # 회원이 없으면 신규 등록
                if user is None:
                    user = register_user(nickname)

                # 회원 정보가 정상적으로 반환되었는지 확인
                if user is None or user.get("id") is None:
                    st.error("회원 정보를 확인하지 못했습니다.")
                    return

                # 세션에 회원 정보 저장
                st.session_state.user_name = user["nickname"]
                st.session_state.user_id = user["id"]
                st.session_state.entered = True
                st.session_state.page = "홈"

                st.rerun()

            except ValueError as e:
                st.error(str(e))

            except Exception as e:
                st.error(f"회원 정보를 처리하지 못했습니다: {e}")


# 홈 화면
def page_home():
    st.title("홈")

    st.subheader(
        f"{st.session_state.user_name}님, 환영합니다!"
    )

    # 요약 정보
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("총 연습 횟수", "-")

    with col2:
        st.metric("평균 점수", "-")

    with col3:
        st.metric("연속 학습일", "-")

    # 나중에 데이터를 합치고 수정해야 하는 부분
    # with col1:
    #     st.metric("총 연습 횟수", f"{total_practice}회")
    #
    # with col2:
    #     st.metric("평균 점수", f"{average_score:.1f}점")
    #
    # with col3:
    #     st.metric("연속 학습일", f"{streak_days}일")

    st.divider()
    st.subheader("바로가기")

    if st.button("연습하기", use_container_width=True):
        st.session_state.page = "연습하기"
        st.rerun()

    st.subheader("안내")

    with st.container(border=True):
        st.write("* 음성 파일을 사용할 시에 반드시 동의가 필요합니다!")
        st.write("* 즐거운 발음 연습이 되시길 바랍니다.")
        st.write("* 문의 시 000을 이용해주시기 바랍니다.")



# 연습하기 화면
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
        categories = sorted({
            row["category"] for row in all_sentences
        })

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
                    with st.spinner("음성을 분석하고 있습니다. 잠시 기다려 주세요."):
                        pipeline = load_stt_pipeline()

                        report = pipeline.evaluate(
                            audio_file_path=audio_path,
                            reference_text=korean_sentence,
                            level=selected_sentence["level"],
                        )

                    # 결과 화면에서 사용할 데이터 저장
                    st.session_state.evaluation_result = report
                    st.session_state.selected_sentence = selected_sentence

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

# 결과 화면
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

    details = report.get("cer_details", {})

    st.subheader("결과 요약")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("WER", f"{report['wer'] * 100:.1f}%")

    with col2:
        st.metric("CER", f"{report['cer'] * 100:.1f}%")

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

        st.audio(
            recorded_audio,
            format="audio/wav",
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

    # 오류(오답) 및 오류유형 표시

    st.divider()

    if st.button("다시 연습하기", use_container_width=True):
        st.session_state.page = "연습하기"
        st.rerun()


# 학습 이력 화면
def page_history():
    st.title("학습 이력")

    # 요약 정보
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("총 학습 횟수", "-")

    with col2:
        st.metric("평균 점수", "-")

    with col3:
        st.metric("연속 학습일", "-")

    st.divider()
    st.subheader("조회 조건")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "시작 날짜",
            value=date.today(),
            key="skeleton_start_date",
        )

    with col2:
        end_date = st.date_input(
            "종료 날짜",
            value=date.today(),
            key="skeleton_end_date",
        )

    search_clicked = st.button(
        "조회",
        use_container_width=True,
    )

    st.divider()
    st.subheader("학습 기록")

    history_df = pd.DataFrame(
        columns=[
            "날짜",
            "카테고리",
            "난이도",
            "연습 문장",
            "연습 횟수",
            "평균 점수",
        ]
    )

    # 조회 버튼을 눌렀을 때 날짜 조건 확인
    if search_clicked:
        if start_date > end_date:
            st.warning("시작 날짜는 종료 날짜보다 늦을 수 없습니다.")
            return

        # 날짜 컬럼이 존재하는 학습 기록만 조회 조건 적용
        if not history_df.empty:
            history_df["날짜"] = pd.to_datetime(
                history_df["날짜"]
            ).dt.date

            history_df = history_df[
                (history_df["날짜"] >= start_date)
                & (history_df["날짜"] <= end_date)
            ]

    st.dataframe(
        history_df,
        column_config={
            "날짜": st.column_config.DateColumn(
                "날짜",
                format="YYYY-MM-DD",
                width="small",
            ),
            "카테고리": st.column_config.TextColumn(
                "카테고리",
                width="small",
            ),
            "난이도": st.column_config.TextColumn(
                "난이도",
                width="small",
            ),
            "연습 문장": st.column_config.TextColumn(
                "연습 문장",
                width="large",
            ),
            "연습 횟수": st.column_config.NumberColumn(
                "연습 횟수",
                width="small",
            ),
            "평균 점수": st.column_config.NumberColumn(
                "평균 점수",
                width="small",
            ),
        },
        use_container_width=True,
        hide_index=True,
    )

    if history_df.empty:
        st.caption("조회 조건에 맞는 학습 기록이 없거나 아직 데이터가 연결되지 않았습니다.")


# 분석 대시보드 화면
def page_dashboard():
    st.title("분석 대시보드")

    # 요약 지표
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("총 연습 횟수", "-")

    with col2:
        st.metric("평균 점수", "-")

    with col3:
        st.metric("학습 문장 수", "-")

    with col4:
        st.metric("학습 진행률", "-")

    # 요약지표 데이터 결과 수정하기

    st.divider()

    # 결과 값에 따라 그래프 넣기
    st.subheader("오류 유형 분석")

    with st.container(border=True):
        st.caption("오류 유형별 분석 결과가 표시될 영역입니다.")

    st.divider()

    st.subheader("난이도별 결과")

    with st.container(border=True):
        st.caption("난이도별 학습 현황이 표시될 영역입니다.")

    st.divider()

    st.subheader("전처리 전후 비교")

    with st.container(border=True):
        st.caption("전처리 전후 비교 결과가 표시될 영역입니다.")


# 메인 실행
def main():
    init_state()
    apply_style()

    if not st.session_state.entered:
        page_start()
        return

    show_sidebar()

    page = st.session_state.page

    if page == "홈":
        page_home()

    elif page == "연습하기":
        page_practice()

    elif page == "결과":
        page_result()

    elif page == "학습 이력":
        page_history()

    elif page == "분석 대시보드":
        page_dashboard()


if __name__ == "__main__":
    main()