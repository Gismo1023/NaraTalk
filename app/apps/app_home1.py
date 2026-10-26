"""시작 페이지(이름 입력) + 홈 페이지."""
import base64
from pathlib import Path

import streamlit as st

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"   # project/app/assets


# ==========================================================
# 공통
# ==========================================================
@st.cache_data
def _image_base64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()


def _go(page: str):
    """버튼 클릭 시 페이지 이동 (on_click 콜백)."""
    st.session_state.page = page


def _home_style():
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


# ==========================================================
# 시작 페이지 (이름 입력 전)
# ==========================================================
def _start_style():
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


# 동의 문구 (예시 — 실제 문구로 교체해 사용)
CONSENT_TITLE = "개인정보 및 음성 데이터 수집·이용 동의 (필수)"
CONSENT_HTML = """
<div class="consent-text">
<b>1. 수집 항목</b>
<ul>
  <li>이름 또는 닉네임</li>
  <li>발음 연습 시 녹음·업로드한 음성 데이터</li>
  <li>음성 인식 결과(텍스트), 발음 평가 점수 및 학습 이력</li>
</ul>
<b>2. 이용 목적</b>
<ul>
  <li>AI 음성 인식(STT)을 통한 발음 분석 및 교정 피드백 제공</li>
  <li>학습 이력 저장 및 학습 대시보드 제공</li>
</ul>
<b>3. 보유 및 이용 기간</b>
<ul>
  <li>서비스 이용 종료 또는 삭제 요청 시까지 보관 후 지체 없이 파기</li>
</ul>
<b>4. 동의 거부 권리</b>
<ul>
  <li>동의를 거부할 수 있으며, 거부 시 서비스 이용이 제한됩니다.</li>
</ul>
</div>
"""


def page_start():
    """배경(start_hero.jpg)은 app.py에서 전체 화면으로 깔고, 부제·입력창·동의·버튼만 올림."""
    _start_style()

    st.markdown(
        '<div class="start-sub">듣고, 따라 말하고, 바로 교정받는 AI 한국어 발음 코치</div>',
        unsafe_allow_html=True,
    )

    with st.container(key="start_card"):
        # ① 동의 문구: 클릭하면 아래로 펼쳐짐
        #    '동의합니다'를 체크하면 제목이 바뀌면서 새로 그려져 자동으로 닫힘
        already_agreed = st.session_state.get("start_agreed", False)
        title = f"✅ {CONSENT_TITLE}" if already_agreed else CONSENT_TITLE
        with st.expander(title, expanded=False):
            st.markdown(CONSENT_HTML, unsafe_allow_html=True)

        # ② 동의 체크박스
        agreed = st.checkbox("동의합니다", key="start_agreed")

        # ③ 이름 입력 (form을 쓰지 않아야 입력·체크 상태에 따라 버튼을 바로 켜고 끌 수 있음)
        name = st.text_input(
            "이름",
            value=st.session_state.user_name,
            placeholder="이름 또는 닉네임을 입력해 주세요",
            max_chars=20,
            label_visibility="collapsed",
            key="start_name",
        )

        # ④ 이름 입력 + 동의 체크가 모두 되어야 시작하기 활성화
        can_start = bool(name.strip()) and agreed

        if st.button(
            "시작하기",
            use_container_width=True,
            disabled=not can_start,
            key="start_button",
        ):
            st.session_state.user_name = name.strip()
            st.session_state.consent_agreed = True
            # TODO: DB 연동 시 사용자 조회/생성 후 user_id·동의 일시 저장
            st.session_state.user_id = None
            st.session_state.entered = True
            st.session_state.page = "홈"
            st.rerun()


# ==========================================================
# 홈 페이지 (이름 입력 후)
# ==========================================================
def page_home():
    _home_style()

    name = st.session_state.user_name or "학습자"
    st.title(f"{name}님, 반갑습니다 👋")
    st.caption("오늘도 한 문장씩, 정확한 발음으로 말해 보세요.")
    st.write("")

    steps = [
        ("STEP 1", "문장 듣기", "제시된 문장의 정답 발음을 먼저 들어 보세요."),
        ("STEP 2", "따라 말하기", "마이크로 녹음하거나 음성 파일을 올리세요."),
        ("STEP 3", "교정 받기", "AI가 틀린 부분과 개선 방법을 알려 드려요."),
    ]

    cols = st.columns(3, gap="medium")
    for col, (num, title, desc) in zip(cols, steps):
        with col:
            st.markdown(
                f"""
                <div class="home-card">
                    <div class="num">{num}</div>
                    <div class="title">{title}</div>
                    <div class="desc">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    st.write("")

    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        st.button(
            "🎙️ 연습 시작하기",
            type="primary",
            use_container_width=True,
            on_click=_go,
            args=("연습하기",),
        )
    with c2:
        st.button(
            "📈 학습 이력 보기",
            use_container_width=True,
            on_click=_go,
            args=("학습 이력",),
        )
