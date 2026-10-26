# 실행 방법 (project 폴더에서):
#   python -m streamlit run app/app.py
import base64
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ==========================================================
# 1. 경로 설정 (반드시 apps import보다 먼저 실행)
# ==========================================================
APP_DIR = Path(__file__).resolve().parent      # project/app
PROJECT_DIR = APP_DIR.parent                   # project

CORE_DIR = PROJECT_DIR / "src_core"
STT_DIR = PROJECT_DIR / "src_stt"
ENV_PATH = PROJECT_DIR / "src_db" / ".env"
# 이미지 폴더: app/assets 를 먼저 찾고, 없으면 프로젝트 루트의 assets 사용
ASSETS_DIR = next(
    (d for d in (APP_DIR / "assets", PROJECT_DIR / "assets") if d.exists()),
    APP_DIR / "assets",
)
BG_IMAGE_PATH = ASSETS_DIR / "bg_hanji.jpg"              # 2번째 페이지부터
START_IMAGE_PATH = ASSETS_DIR / "start_hero.jpg"         # 첫 페이지 (전체 화면)

for path in (APP_DIR, PROJECT_DIR, CORE_DIR, STT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# 환경 변수 (.env 파일이 없어도 오류 없이 넘어감)
load_dotenv(ENV_PATH, override=True)

# ==========================================================
# 2. Streamlit 기본 설정 (다른 st 명령보다 먼저 실행)
# ==========================================================
st.set_page_config(
    page_title="나랏말싸미",
    page_icon="🇰🇷",
    layout="wide",
)

# ==========================================================
# 3. 페이지 함수 연결
# ==========================================================
# 시작·홈 화면 버전 선택
#   False → 디자인 버전 (app_home.py, CSS 사용, 포스터·한지 배경)
#   True  → 기본 버전 (app_home_basic.py, CSS 없음, 배경 없음)
USE_BASIC_HOME = False

if USE_BASIC_HOME:
    from apps.app_home_basic import page_start, page_home  # noqa: E402
else:
    from apps.app_home import page_start, page_home  # noqa: E402


def _coming_soon(title):
    """아직 파일이 없는 페이지는 '준비 중' 화면으로 대체."""
    def _page():
        st.title(title)
        st.info("🚧 준비 중인 페이지입니다.")
    return _page


try:
    from apps.app_practice import page_practice
except ModuleNotFoundError:
    page_practice = _coming_soon("연습하기")

try:
    from apps.app_result import page_result
except ModuleNotFoundError:
    page_result = _coming_soon("결과")

try:
    from apps.app_history import page_history
except ModuleNotFoundError:
    page_history = _coming_soon("학습 이력")

try:
    from apps.app_dashboard import page_dashboard
except ModuleNotFoundError:
    page_dashboard = _coming_soon("분석 대시보드")

# 사이드바 메뉴 이름 → 페이지 함수
PAGES = {
    "홈": page_home,
    "연습하기": page_practice,
    "결과": page_result,
    "학습 이력": page_history,
    "분석 대시보드": page_dashboard,
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
# 5. 스타일 (배경화면 + 공통)
# ==========================================================
@st.cache_data
def load_image_base64(image_path: str) -> str:
    return base64.b64encode(Path(image_path).read_bytes()).decode()


def _common_css() -> str:
    """배경을 가리는 헤더·본문 영역 투명 처리 (모든 페이지 공통)."""
    return """
        [data-testid="stHeader"],
        [data-testid="stMain"],
        [data-testid="stBottom"] > div,
        .main {
            background: transparent !important;
        }
    """


def apply_start_background():
    """첫 페이지: start_hero.jpg로 화면 전체를 채움."""
    if not START_IMAGE_PATH.exists():
        return

    hero = load_image_base64(str(START_IMAGE_PATH))

    # 넓은 화면에서 좌우 여백은 같은 이미지의 블러본으로 채움
    # (블러 파일이 없으면 원본으로 대신 채움)
    blur_path = ASSETS_DIR / "start_hero_blur.jpg"
    blur = load_image_base64(str(blur_path)) if blur_path.exists() else hero

    st.markdown(
        f"""
        <style>
        .stApp,
        [data-testid="stApp"],
        [data-testid="stAppViewContainer"] {{
            background-color: #31459C !important;
            background-image:
                url("data:image/jpeg;base64,{hero}"),
                url("data:image/jpeg;base64,{blur}") !important;
            background-size: auto 100%, cover !important;
            background-position: center, center !important;
            background-repeat: no-repeat, no-repeat !important;
            background-attachment: fixed, fixed !important;
        }}
        /* 세로 화면(모바일)에서는 포스터로 꽉 채움 */
        @media (orientation: portrait) {{
            .stApp,
            [data-testid="stApp"],
            [data-testid="stAppViewContainer"] {{
                background-size: cover, cover !important;
            }}
        }}
        {_common_css()}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_background():
    """2번째 페이지부터: 한지 배경."""
    if not BG_IMAGE_PATH.exists():
        return

    encoded = load_image_base64(str(BG_IMAGE_PATH))
    st.markdown(
        f"""
        <style>
        .stApp,
        [data-testid="stApp"],
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/jpeg;base64,{encoded}") !important;
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* 사이드바: 한지 톤 반투명 */
        [data-testid="stSidebar"] {{
            background-color: rgba(245, 240, 228, 0.85);
        }}
        {_common_css()}
        </style>
        """,
        unsafe_allow_html=True,
    )


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


# ==========================================================
# 6. 사이드바
# ==========================================================
def change_page():
    st.session_state.page = st.session_state.sidebar_menu


def show_sidebar():
    with st.sidebar:
        st.title("🇰🇷 나랏말싸미")
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
        st.caption("집현전 해요")


# ==========================================================
# 7. 메인
# ==========================================================
def main():
    init_state()
    apply_style()

    if not st.session_state.entered:      # 첫 페이지 (이름 입력 전)
        if not USE_BASIC_HOME:
            apply_start_background()      # → start_hero.jpg
        page_start()
        return

    if not USE_BASIC_HOME:
        apply_background()                # 2번째 페이지부터 → bg_hanji.jpg
    show_sidebar()
    PAGES[st.session_state.page]()


if __name__ == "__main__":
    main()
