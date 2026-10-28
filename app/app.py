# app.py
<<<<<<< HEAD

# python -m streamlit run app/app.py
import streamlit as st
=======
# 실행 방법 (프로젝트 최상위 폴더에서): python -m streamlit run app/app.py
>>>>>>> 06d9502f299fbbabe506eeac4fe92f871b6fb343
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ----------------------------------------------------------
# 1. 경로 설정 — 반드시 apps import보다 먼저 실행
#    (apps 안의 파일들이 `from src.db import ...`를 쓰기 때문)
# ----------------------------------------------------------
APP_DIR = Path(__file__).resolve().parent       # 프로젝트/app
PROJECT_DIR = APP_DIR.parent                    # 프로젝트 최상위

for path in (APP_DIR, PROJECT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# ----------------------------------------------------------
# 2. 환경 변수 — src/.env (db.py와 같은 위치)
# ----------------------------------------------------------
load_dotenv(PROJECT_DIR / "src" / ".env", override=True)

# ----------------------------------------------------------
# 3. 페이지 함수 연결
# ----------------------------------------------------------
from apps.app_home import page_start, page_home  # noqa: E402
from apps.app_practice import page_practice  # noqa: E402
from apps.app_result import page_result  # noqa: E402
from apps.app_history import page_history  # noqa: E402
from apps.app_dashboard import page_dashboard  # noqa: E402
from apps.app_manager import page_manager  # noqa: E402

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
            "분석 대시보드"
        ]
        if st.session_state.get("is_admin", False):
            pages.append("관리자")

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

    elif page == "관리자":
        page_manager()

if __name__ == "__main__":
    main()