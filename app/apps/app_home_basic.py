"""시작 페이지 + 홈 페이지 — CSS 없는 기본 버전.

Streamlit 기본 기능만 사용합니다 (CSS·HTML 없음).
색상은 .streamlit/config.toml 의 테마 설정으로만 지정합니다.
"""
from pathlib import Path

import streamlit as st

# 포스터 이미지: app/assets 또는 프로젝트 루트 assets 중 있는 곳에서 찾기
_APP_DIR = Path(__file__).resolve().parent.parent          # NaraTalk/app
_CANDIDATES = [
    _APP_DIR / "assets" / "start_hero.jpg",
    _APP_DIR.parent / "assets" / "start_hero.jpg",
]
HERO_IMAGE = next((p for p in _CANDIDATES if p.exists()), None)


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


# ==========================================================
# 시작 페이지 (이름 입력 전)
# ==========================================================
def page_start():
    # 화면 가운데 좁은 칸에 세로로 쌓기: 포스터 → 부제 → 동의 → 이름 → 시작하기
    _, center, _ = st.columns([1, 1.2, 1])

    with center:
        # ① 포스터
        if HERO_IMAGE is not None:
            st.image(str(HERO_IMAGE), use_container_width=True)
        else:
            st.title("나랏말싸미")

        # ② 부제
        st.subheader("듣고, 따라 말하고, 바로 교정받는 AI 한국어 발음 코치")

        # ③ 동의 문구: 클릭하면 아래로 펼쳐짐
        #    '동의합니다'를 체크하면 제목이 바뀌면서 새로 그려져 자동으로 닫힘
        already_agreed = st.session_state.get("start_agreed", False)
        title = f"✅ {CONSENT_TITLE}" if already_agreed else CONSENT_TITLE
        with st.expander(title, expanded=False):
            st.markdown(CONSENT_TEXT)

        # ④ 동의 체크박스
        agreed = st.checkbox("동의합니다", key="start_agreed")

        # ⑤ 이름 입력
        name = st.text_input(
            "이름",
            value=st.session_state.user_name,
            placeholder="이름 또는 닉네임을 입력해 주세요",
            max_chars=20,
            label_visibility="collapsed",
            key="start_name",
        )

        # ⑥ 이름 입력 + 동의 체크가 모두 되어야 시작하기 활성화
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
        ("STEP 1", "문장 듣기", "제시된 문장의 정답 발음을 먼저 들어 보세요."),
        ("STEP 2", "따라 말하기", "마이크로 녹음하거나 음성 파일을 올리세요."),
        ("STEP 3", "교정 받기", "AI가 틀린 부분과 개선 방법을 알려 드려요."),
    ]

    cols = st.columns(3, gap="medium")
    for col, (num, title, desc) in zip(cols, steps):
        with col:
            with st.container(border=True):
                st.caption(num)
                st.markdown(f"**{title}**")
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
