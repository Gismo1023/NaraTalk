# python -m streamlit run app/app.py
import streamlit as st
import sys
from pathlib import Path
from dotenv import load_dotenv

# 페이지 함수 연결
from apps.app_home import page_start, page_home
from apps.app_practice import page_practice
from apps.app_result import page_result
from apps.app_history import page_history
from apps.app_dashboard import page_dashboard

# 프로젝트 경로 설정

PROJECT_DIR = Path(__file__).resolve().parent.parent

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# 환경 변수 설정
# 기존 경로 유지
ENV_PATH = PROJECT_DIR / "src_db" / ".env"
load_dotenv(ENV_PATH, override=True)

# 기존 STT 모듈 검색 경로 설정
CORE_DIR = PROJECT_DIR / "src_core"
STT_DIR = PROJECT_DIR / "src_stt"

for path in (CORE_DIR, STT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# ==========================================================

# Streamlit 기본 설정
st.set_page_config(
    page_title="나랏말싸미",
    page_icon="🇰🇷",
    layout="wide",
)

# 세션 상태 초기화
def init_state():
    defaults = {
        "user_name": "",
        "user_id": None,
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
        unsafe_allow_html=True,
    )

# 사이드바 메뉴 변경
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

# 메인 실행 및 페이지 연결
def main():
    init_state()
    apply_style()

    # 시작 페이지
    if not st.session_state.entered:
        page_start()
        return

    # 로그인 이후 사이드바 표시
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
