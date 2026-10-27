# app.py
# python -m streamlit run app/app.py
import streamlit as st
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 경로를 먼저 설정해 apps와 src를 import할 수 있게 합니다.
APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
for path in (APP_DIR, PROJECT_DIR, PROJECT_DIR / "src_core", PROJECT_DIR / "src_stt"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# 실제 DB 모듈이 사용하는 src/.env 우선, 이전 src_db/.env도 지원
ENV_PATH = PROJECT_DIR / "src" / ".env"
if not ENV_PATH.exists():
    ENV_PATH = PROJECT_DIR / "src_db" / ".env"
load_dotenv(ENV_PATH, override=True)

# CSS 전용 파일에서 스타일만 불러옵니다.
from css.app_css import apply_style, apply_start_background, apply_background
from css.app_home import apply_start_style, apply_home_style

# 기존 페이지 구현은 apps에서 그대로 사용합니다.
from apps.app_home import page_start, page_home
from apps.app_practice import page_practice
from apps.app_result import page_result
from apps.app_history import page_history
from apps.app_dashboard import page_dashboard

try:
    from apps.app_manager import page_manager
except ModuleNotFoundError as error:
    if error.name != "apps.app_manager":
        raise

    def page_manager():
        st.title("관리자")
        st.info("app_manager.py 파일이 없어 관리자 화면을 표시할 수 없습니다.")

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
            "관리자"
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
        apply_start_background()
        apply_start_style()
        page_start()
        return

    # 로그인 이후 사이드바 표시
    apply_background()
    show_sidebar()

    page = st.session_state.page

    if page == "홈":
        apply_home_style()
        page_home()

    elif page == "연습하기":
        page_practice()

    elif page == "결과":
        page_result()

    elif page == "학습 이력":
        page_history()

    elif page == "분석 대시보드":
        page_dashboard()

    elif page == "관리자":
        page_manager()

if __name__ == "__main__":
    main()
