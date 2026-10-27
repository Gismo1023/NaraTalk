# css/app_css.py
# 전체 화면 배경과 공통 CSS만 관리합니다.
import base64
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = APP_DIR.parent
ASSETS_DIR = next(
    (folder for folder in (APP_DIR / "assets", PROJECT_DIR / "assets") if folder.exists()),
    APP_DIR / "assets",
)
BG_IMAGE_PATH = ASSETS_DIR / "bg_hanji.jpg"
START_IMAGE_PATH = ASSETS_DIR / "start_hero.jpg"

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

