# css/app_home_css.py
# 시작·홈 화면의 CSS만 관리합니다. 페이지 함수와 DB 로직은 apps/app_home.py에 있습니다.
import streamlit as st

def apply_home_style():
    st.markdown(
        """
        <style>
        /* 흰 배경 일러스트를 한지 배경에 자연스럽게 합성 */
        .hero-img {
            width: 100%;
            max-width: 520px;
            mix-blend-mode: multiply;
            display: block;
            margin: 0 auto;
        }
        .home-card {
            background: rgba(255, 255, 255, 0.6);
            border: 1px solid rgba(84, 112, 180, 0.25);
            border-radius: 14px;
            padding: 22px 20px;
            height: 100%;
        }
        .home-card .num {
            font-size: 14px;
            font-weight: 700;
            color: #5470B4;
            margin-bottom: 6px;
        }
        .home-card .title {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .home-card .desc {
            font-size: 15px;
            color: #5A5A5A;
            line-height: 1.6;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 기존 홈 통계와 버튼에도 동일한 색감 적용
    st.markdown(
        """
        <style>
        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.60);
            border: 1px solid rgba(84,112,180,0.20);
            border-radius: 14px;
            padding: 16px;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stButton"] button {
            border-radius: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



def apply_start_style():
    """시작 화면 전용 스타일 (카드 없이 포스터 위에 바로 배치).

    포스터(start_hero.jpg)는 화면 높이에 꽉 맞춰 가운데 표시됨
    → 포스터 높이 = 100vh, 포스터 폭 ≈ 70.8vh.
    그래서 모든 위치·크기를 vh로 지정하면 어떤 모니터에서도 포스터의 같은 자리에 놓임.
      - 부제:      포스터 높이 26% 지점 (타이틀 바로 아래)
      - 입력창:    70% 지점
      - 시작하기:  77% 지점
      - 폭:        포스터 폭의 약 54% (= 38vh)
    """
    st.markdown(
        """
        <style>
        /* ── 부제: 포스터 타이틀 아래 한 줄 ── */
        .start-sub {
            position: fixed;
            top: calc(24.5vh - 0.5cm);      /* 기존 위치에서 1cm 위로 */
            left: 50%;
            transform: translateX(-50%);
            width: 68vh;
            text-align: center;
            white-space: nowrap;
            z-index: 10;
            font-size: clamp(14px, 2.1vh, 28px);
            font-weight: 700;
            color: #FFFFFF;
            letter-spacing: -0.3px;
            text-shadow: 0 2px 8px rgba(10, 15, 60, 0.6);
        }

        /* ── 입력창 + 버튼 묶음 (배경·테두리 없음) ── */
        .st-key-start_card {
            position: fixed !important;
            bottom: 11vh;                 /* 아래 기준 고정 → 동의 문구를 펼치면 위로 늘어남 */
            left: 50%;
            transform: translateX(-50%);
            width: 38vh !important;
            z-index: 10;
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
        }
        .st-key-start_card [data-testid="stVerticalBlock"] {
            gap: 1.3vh !important;
        }

        /* ── 동의 문구 (펼치기) ── */
        .st-key-start_card [data-testid="stExpander"] details {
            background: rgba(20, 24, 70, 0.45) !important;
            border: 1px solid rgba(210, 214, 228, 0.6) !important;
            border-radius: 1vh !important;
        }
        .st-key-start_card [data-testid="stExpander"] summary {
            padding: 0.8vh 1.2vh !important;
        }
        .st-key-start_card [data-testid="stExpander"] summary p,
        .st-key-start_card [data-testid="stExpander"] summary svg {
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
            font-size: clamp(13px, 1.55vh, 20px) !important;
            font-weight: 700 !important;
        }
        .st-key-start_card [data-testid="stExpanderDetails"] {
            max-height: 22vh;             /* 길면 안에서 스크롤 */
            overflow-y: auto;
            padding: 0 1.4vh 1vh 1.4vh !important;
        }
        .consent-text {
            color: rgba(255, 255, 255, 0.92);
            font-size: clamp(12px, 1.35vh, 17px);
            line-height: 1.6;
        }
        .consent-text b { color: #F2CB5E; }
        .consent-text ul { margin: 0.4vh 0 0.6vh 0; padding-left: 1.6vh; }

        /* ── 동의합니다 체크박스 ── */
        .st-key-start_card [data-testid="stCheckbox"] label p {
            color: #FFFFFF !important;
            font-size: clamp(14px, 1.7vh, 22px) !important;
            font-weight: 700 !important;
            text-shadow: 0 1px 4px rgba(40, 8, 12, 0.7);
        }

        /* ── 시작하기 비활성 상태 (이름·동의 전) ── */
        .st-key-start_card [data-testid="stButton"] button:disabled,
        .st-key-start_card [data-testid="stFormSubmitButton"] button:disabled {
            opacity: 1 !important;                    /* 버튼 전체를 흐리게 하지 않음 */
            background: linear-gradient(180deg, #6B7BB8 0%, #55639C 100%) !important;  /* 비활성: 차분한 파랑 */
            border-color: rgba(255, 255, 255, 0.55) !important;
            cursor: not-allowed !important;
            box-shadow: none !important;
        }
        /* 시작하기 글씨: 활성·비활성 모두 불투명한 흰색 */
        .st-key-start_card [data-testid="stButton"] button p,
        .st-key-start_card [data-testid="stButton"] button:disabled p {
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            opacity: 1 !important;
        }
        .st-key-start_card [data-testid="stForm"] {
            padding: 0 !important;
            border: none !important;
        }

        /* ── 입력창: 반투명 + 은회색 테두리 + 흰 글자 ── */
        .st-key-start_card [data-testid="stTextInput"] div[data-baseweb="input"] {
            min-height: 0 !important;
            height: 4.3vh !important;
            border-radius: 1.4vh !important;
            border: 2px solid rgba(210, 214, 228, 0.9) !important;
            background: transparent !important;       /* 박스 완전 투명 */
            box-shadow: none !important;
        }
        .st-key-start_card [data-testid="stTextInput"] div[data-baseweb="base-input"] {
            background: transparent !important;
        }
        .st-key-start_card [data-testid="stTextInput"] input {
            background: transparent !important;
            color: #FFFFFF !important;                /* 실제 입력 글자: 흰색 */
            -webkit-text-fill-color: #FFFFFF !important;
            caret-color: #FFFFFF;
            text-shadow: 0 1px 4px rgba(40, 8, 12, 0.7);   /* 빨간 배경 위 가독성 */
            font-size: clamp(14px, 1.8vh, 24px) !important;
            font-weight: 600 !important;
            padding: 0 1.2vh !important;
            height: 100% !important;
        }
        .st-key-start_card [data-testid="stTextInput"] input::placeholder {
            color: #FFFFFF !important;                /* 안내 문구: 흰색 */
            -webkit-text-fill-color: #FFFFFF !important;
            opacity: 1;
        }
        /* 입력 칸 안쪽 모든 겹(div·input)의 회색 테마 배경 제거 — 포커스·마우스오버 포함 */
        .st-key-start_card [data-testid="stTextInput"],
        .st-key-start_card [data-testid="stTextInput"] *,
        .st-key-start_card [data-testid="stTextInput"] *:hover,
        .st-key-start_card [data-testid="stTextInput"] *:focus,
        .st-key-start_card [data-testid="stTextInput"] *:focus-within {
            background: transparent !important;
            background-color: transparent !important;
        }
        /* 브라우저 자동완성 시 생기는 하늘색 배경 제거 */
        .st-key-start_card [data-testid="stTextInput"] input:-webkit-autofill,
        .st-key-start_card [data-testid="stTextInput"] input:-webkit-autofill:focus {
            -webkit-box-shadow: 0 0 0 1000px transparent inset !important;
            -webkit-text-fill-color: #FFFFFF !important;
            transition: background-color 9999s ease-in-out 0s;
        }
        /* 입력 칸 바깥 래퍼 배경도 투명 (포커스 시 포함) */
        .st-key-start_card [data-testid="stTextInput"] div[data-baseweb="input"] > div,
        .st-key-start_card [data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
            background: transparent !important;
        }
        /* 'Press Enter to submit' 안내 문구 숨김 */
        .st-key-start_card [data-testid="InputInstructions"] {
            display: none !important;
        }

        /* ── 시작하기: 파란색 박스 + 흰 글씨 (포스터 밤하늘 색) ── */
        .st-key-start_card [data-testid="stButton"] button,
        .st-key-start_card [data-testid="stFormSubmitButton"] button {
            width: 100% !important;
            min-height: 0 !important;
            height: 4.1vh !important;
            padding: 0 !important;
            background: linear-gradient(180deg, #4062D6 0%, #2C45A8 100%) !important;
            border: 2px solid rgba(255, 255, 255, 0.75) !important;
            border-radius: 1vh !important;
            box-shadow: 0 0.4vh 1.2vh rgba(10, 15, 60, 0.45);
        }
        .st-key-start_card [data-testid="stButton"] button:hover:enabled,
        .st-key-start_card [data-testid="stFormSubmitButton"] button:hover {
            background: linear-gradient(180deg, #5274E6 0%, #3653BE 100%) !important;
            border-color: #FFFFFF !important;
        }
        .st-key-start_card [data-testid="stButton"] button:active:enabled,
        .st-key-start_card [data-testid="stFormSubmitButton"] button:active {
            transform: translateY(1px);
        }
        .st-key-start_card [data-testid="stButton"] button p,
        .st-key-start_card [data-testid="stFormSubmitButton"] button p {
            color: #FFFFFF !important;
            font-size: clamp(15px, 1.9vh, 24px) !important;
            font-weight: 800 !important;
            letter-spacing: 1px;
        }

        /* 세로 화면(모바일): 포스터가 화면 폭 기준이므로 vw로 */
        @media (orientation: portrait) {
            .start-sub { width: 96vw; font-size: 3.4vw; }
            .st-key-start_card { width: 54vw !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 기존 apps/app_home.py의 컬럼·체크박스·입력창에도 스타일 적용
    st.markdown(
        """
        <style>
        [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) {
            max-width: 560px;
            margin-left: auto;
            margin-right: auto;
            padding-top: clamp(35px, 12vh, 130px);
        }
        [data-testid="stMainBlockContainer"] h1,
        [data-testid="stMainBlockContainer"] [data-testid="stCaptionContainer"] p {
            color: #FFFFFF !important;
            text-shadow: 0 2px 8px rgba(10, 15, 60, 0.7);
        }
        [data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] h3 {
            color: #FFFFFF !important;
            text-shadow: 0 1px 5px rgba(10, 15, 60, 0.65);
        }
        [data-testid="stMainBlockContainer"] [data-testid="stExpander"] details {
            background: rgba(20, 24, 70, 0.50) !important;
            border: 1px solid rgba(210, 214, 228, 0.65) !important;
            border-radius: 10px !important;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stExpander"] summary p,
        [data-testid="stMainBlockContainer"] [data-testid="stExpander"] summary svg,
        [data-testid="stMainBlockContainer"] [data-testid="stExpanderDetails"] p,
        [data-testid="stMainBlockContainer"] [data-testid="stExpanderDetails"] li,
        [data-testid="stMainBlockContainer"] [data-testid="stCheckbox"] label p,
        [data-testid="stMainBlockContainer"] [data-testid="stTextInput"] label p {
            color: #FFFFFF !important;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stTextInput"] input {
            background: rgba(20, 24, 70, 0.48) !important;
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            border-radius: 10px !important;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stTextInput"] input::placeholder {
            color: rgba(255, 255, 255, 0.84) !important;
            -webkit-text-fill-color: rgba(255, 255, 255, 0.84) !important;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stButton"] button[kind="secondary"],
        [data-testid="stMainBlockContainer"] [data-testid="stButton"] button[kind="primary"] {
            background: linear-gradient(180deg, #4062D6 0%, #2C45A8 100%) !important;
            border-color: rgba(255, 255, 255, 0.75) !important;
            border-radius: 10px !important;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stButton"] button p {
            color: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

