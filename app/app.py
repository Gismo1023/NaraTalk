# 순수 Python 버전 (CSS·HTML 없음)
# 실행 방법 (NaraTalk 폴더에서):
#   python -m streamlit run app/app.py
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ==========================================================
# 1. 경로 설정 (반드시 apps import보다 먼저 실행)
# ==========================================================
APP_DIR = Path(__file__).resolve().parent      # NaraTalk/app
PROJECT_DIR = APP_DIR.parent                   # NaraTalk

# 서비스 이름: 훈민정음 옛한글 표기 (ㅆ + 아래아 ᆞ)
#   "\u110A" = 초성 ㅆ, "\u119E" = 아래아(ㆍ)
TITLE_TEXT = "나랏말\u110A\u119E미"

# 이미지 폴더: app/assets 를 먼저 찾고, 없으면 프로젝트 루트의 assets
ASSETS_DIR = next(
    (d for d in (APP_DIR / "assets", PROJECT_DIR / "assets") if d.exists()),
    APP_DIR / "assets",
)

# 사이드바 맨 아래 저작권 표시
FOOTER_ICON = ASSETS_DIR / "footer_icon.png"
FOOTER_ICON_WIDTH = 36         # ← 아이콘 크기(픽셀). 글자 높이와 비슷하게
FOOTER_TEXT = "Copyright © jiphyeonjeon Corp. All Rights Reserved."

for path in (APP_DIR, PROJECT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# 환경 변수 (.env 파일이 없어도 오류 없이 넘어감)
load_dotenv(PROJECT_DIR / "src" / ".env", override=True)

# ==========================================================
# 2. Streamlit 기본 설정 (다른 st 명령보다 먼저 실행)
#    색상은 .streamlit/config.toml 의 [theme] 으로 지정
# ==========================================================
st.set_page_config(
    page_title=TITLE_TEXT,
    page_icon="🇰🇷",
    layout="wide",
)

# ==========================================================
# 3. 페이지 함수 연결
# ==========================================================
from apps.app_home import page_start, page_home  # noqa: E402


def _coming_soon(title):
    """아직 파일이 없는 페이지는 '준비 중' 화면으로 대체."""
    def _page():
        st.title(title)
        st.info("🚧 준비 중인 페이지입니다.")
    return _page


def _load_page(module_name, func_name, title):
    """페이지 파일을 불러오고, 없거나 오류가 나면 '준비 중' 화면으로 대체."""
    try:
        module = __import__(f"apps.{module_name}", fromlist=[func_name])
        return getattr(module, func_name)
    except Exception:
        return _coming_soon(title)


# 사이드바 메뉴 이름 → 페이지 함수
PAGES = {
    "홈": page_home,
    "연습하기": _load_page("app_practice", "page_practice", "연습하기"),
    "결과": _load_page("app_result", "page_result", "결과"),
    "학습 이력": _load_page("app_history", "page_history", "학습 이력"),
    "분석 대시보드": _load_page("app_dashboard", "page_dashboard", "분석 대시보드"),
}


# ==========================================================
# 4. 세션 상태 초기화
# ==========================================================
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


# ==========================================================
# 5. 사이드바
# ==========================================================
def change_page():
    st.session_state.page = st.session_state.sidebar_menu


def logout():
    st.session_state.entered = False
    st.session_state.page = "시작"


def show_sidebar():
    with st.sidebar:
        # 타이틀: 글자로 표시 (나랏말ᄊᆞ미)
        st.title(TITLE_TEXT)

        if st.session_state.user_name:
            st.caption(f"👤 {st.session_state.user_name}님")
        st.divider()

        menu = list(PAGES.keys())

        if st.session_state.page not in menu:
            st.session_state.page = "홈"

        # 버튼으로 페이지를 바꾼 경우에도 메뉴 선택값 동기화
        if st.session_state.get("sidebar_menu") != st.session_state.page:
            st.session_state.sidebar_menu = st.session_state.page

        st.selectbox("메뉴", menu, key="sidebar_menu", on_change=change_page)

        st.divider()
        st.button("처음 화면으로", use_container_width=True, on_click=logout)

        show_footer()


def show_footer():
    """사이드바 맨 아래: 작은 한옥 아이콘 + 저작권 문구."""
    st.divider()
    try:
        icon_col, text_col = st.columns([1, 5], vertical_alignment="center")  # 1.36 이상
    except TypeError:
        icon_col, text_col = st.columns([1, 5])                                # 1.36 미만

    with icon_col:
        if FOOTER_ICON.exists():
            st.image(str(FOOTER_ICON), width=FOOTER_ICON_WIDTH)
    with text_col:
        st.caption(FOOTER_TEXT)


# ==========================================================
# 6. 메인
# ==========================================================
def main():
    init_state()

    # 시작 페이지 (이름 입력 전)
    if not st.session_state.entered:
        page_start()
        return

    show_sidebar()
    PAGES[st.session_state.page]()


if __name__ == "__main__":
    main()
