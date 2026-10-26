"""시작 페이지 + 홈 페이지 — 순수 Python 버전 (CSS·HTML 없음).

Streamlit 기본 부품만 사용합니다.
색상은 .streamlit/config.toml 의 [theme] 설정으로만 지정합니다.
"""
from pathlib import Path

import streamlit as st

# ==========================================================
# 이미지 경로: app/assets 를 먼저 찾고, 없으면 프로젝트 루트의 assets
# ==========================================================
_APP_DIR = Path(__file__).resolve().parent.parent          # NaraTalk/app
_ASSETS_DIR = next(
    (d for d in (_APP_DIR / "assets", _APP_DIR.parent / "assets") if d.exists()),
    _APP_DIR / "assets",
)
HERO_IMAGE = _ASSETS_DIR / "start_hero.jpg"


# ==========================================================
# 동의 문구 (예시 — 실제 문구로 교체해 사용)
# ==========================================================
CONSENT_TITLE = "개인정보 및 음성 데이터 수집·이용 동의 (필수)"
CONSENT_TEXT = """
**1. 수집 항목**
- 이름 또는 닉네임
- 발음 연습 시 녹음·업로드한 음성 데이터
- 음성 인식 결과(텍스트), 발음 평가 점수 및 학습 이력

**2. 이용 목적**
- AI 음성 인식(STT)을 통한 발음 분석 및 교정 피드백 제공
- 학습 이력 저장 및 학습 대시보드 제공

**3. 보유 및 이용 기간**
- 서비스 이용 종료 또는 삭제 요청 시까지 보관 후 지체 없이 파기

**4. 동의 거부 권리**
- 동의를 거부할 수 있으며, 거부 시 서비스 이용이 제한됩니다.
"""


# ==========================================================
# 공통
# ==========================================================
def _go(page: str):
    """버튼 클릭 시 페이지 이동 (on_click 콜백)."""
    st.session_state.page = page


def _show_image(path: Path):
    """Streamlit 버전에 상관없이 이미지를 칸 너비에 맞춰 표시."""
    try:
        st.image(str(path), use_container_width=True)       # 1.40 이상
    except TypeError:
        st.image(str(path), use_column_width=True)          # 1.40 미만


# ==========================================================
# 시작 페이지 (이름 입력 전)
#   왼쪽: 포스터 / 오른쪽: 부제 → 동의 → 체크 → 이름 → 시작하기
# ==========================================================
def page_start():
    left, right = st.columns([1, 1], gap="large")

    # ── 왼쪽: 포스터 ──
    with left:
        if HERO_IMAGE.exists():
            _show_image(HERO_IMAGE)
        else:
            st.title("나랏말싸미")

    # ── 오른쪽: 입력 영역 ──
    with right:
        for _ in range(6):          # 포스터 가운데 높이에 맞추기 위한 빈 줄
            st.write("")

        st.title("나랏말싸미")
        st.subheader("듣고, 따라 말하고, 바로 교정받는 AI 한국어 발음 코치")
        st.write("")

        # ① 동의 문구: 클릭하면 아래로 펼쳐짐
        #    '동의합니다'를 체크하면 제목이 바뀌면서 새로 그려져 자동으로 닫힘
        already_agreed = st.session_state.get("start_agreed", False)
        title = f"✅ {CONSENT_TITLE}" if already_agreed else CONSENT_TITLE
        with st.expander(title, expanded=False):
            st.markdown(CONSENT_TEXT)

        # ② 동의 체크박스
        agreed = st.checkbox("동의합니다", key="start_agreed")

        # ③ 이름 입력
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
            type="primary",
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

        if not can_start:
            st.caption("동의 체크 후 이름을 입력하고 Enter를 누르면 시작할 수 있어요.")


# ==========================================================
# 홈 페이지 (이름 입력 후)
# ==========================================================
def page_home():
    name = st.session_state.user_name or "학습자"
    st.title(f"{name}님, 반갑습니다 👋")
    st.caption("오늘도 한 문장씩, 정확한 발음으로 말해 보세요.")
    st.write("")

    steps = [
        ("STEP 1", "🔊 문장 듣기", "제시된 문장의 정답 발음을 먼저 들어 보세요."),
        ("STEP 2", "🎙️ 따라 말하기", "마이크로 녹음하거나 음성 파일을 올리세요."),
        ("STEP 3", "✅ 교정 받기", "AI가 틀린 부분과 개선 방법을 알려 드려요."),
    ]

    cols = st.columns(3, gap="medium")
    for col, (num, title, desc) in zip(cols, steps):
        with col:
            with st.container(border=True):
                st.caption(num)
                st.subheader(title)
                st.write(desc)

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
