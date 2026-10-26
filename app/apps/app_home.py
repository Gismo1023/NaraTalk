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

# 서비스 이름: 훈민정음 옛한글 표기 (ㅆ + 아래아 ᆞ)
#   "\u110A" = 초성 ㅆ, "\u119E" = 아래아(ㆍ)
TITLE_TEXT = "나랏말\u110A\u119E미"


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


def _enter_app():
    """시작하기: 이름·동의를 저장하고 홈으로 이동."""
    name = st.session_state.get("start_name", "").strip()
    if not name or not st.session_state.get("start_agreed", False):
        return                      # 이름 또는 동의가 없으면 시작하지 않음

    st.session_state.user_name = name
    st.session_state.consent_agreed = True
    # TODO: DB 연동 시 사용자 조회/생성 후 user_id·동의 일시 저장
    st.session_state.user_id = None
    st.session_state.entered = True
    st.session_state.page = "홈"


def _space_cm(cm: float):
    """CSS 없이 세로 간격 만들기: 높이를 지정한 빈 컨테이너를 끼워 넣음.

    1cm ≈ 37.8px. Streamlit이 요소 사이에 기본으로 두는 간격(위·아래 약 16px씩)을
    빼서, 앞 요소와 다음 요소 사이가 지정한 cm가 되도록 맞춤.
    """
    px = round(cm * 37.8) - 32
    st.container(height=max(px, 1), border=False)


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
            st.title(TITLE_TEXT)

    # ── 오른쪽: 입력 영역 ──
    with right:
        # 제목: 빈 줄 없이 시작 → 포스터 맨 윗부분과 높이를 맞춤
        st.title(TITLE_TEXT)

        # 부제: 굵지 않은 보통 글씨
        st.write("듣고, 따라 말하고, 바로 교정받는 AI 한국어 발음 코치")

        # 부제와 동의 문구 사이 3cm
        _space_cm(3)

        # ① 동의 문구: 클릭하면 아래로 펼쳐짐
        #    '동의합니다'를 체크하면 제목이 바뀌면서 새로 그려져 자동으로 닫힘
        already_agreed = st.session_state.get("start_agreed", False)
        title = f"✅ {CONSENT_TITLE}" if already_agreed else CONSENT_TITLE
        with st.expander(title, expanded=False):
            st.markdown(CONSENT_TEXT)

        # ② 동의 체크박스
        agreed = st.checkbox("동의합니다", key="start_agreed")

        # 체크박스와 이름 입력 사이 3cm
        _space_cm(3)

        # ③ 이름 입력 + ④ 시작하기 (form: 입력창에서 Enter를 누를 때마다 제출됨)
        #   1번째 Enter(또는 클릭): 이름 확정 → 시작하기 버튼이 파란색으로 바뀜
        #   2번째 Enter(또는 클릭): 다음 화면(홈)으로 이동
        if not agreed:
            st.session_state.start_ready = False      # 동의를 풀면 다시 회색으로

        ready = st.session_state.get("start_ready", False)

        with st.form("start_form", border=False):
            st.text_input(
                "이름",
                value=st.session_state.user_name,
                placeholder="이름 또는 닉네임을 입력해 주세요",
                max_chars=20,
                label_visibility="collapsed",
                key="start_name",
            )
            submitted = st.form_submit_button(
                "시작하기",
                type="primary" if ready else "secondary",   # 준비되면 파란색
                use_container_width=True,
            )

        if submitted:
            name = st.session_state.get("start_name", "").strip()

            if not agreed:
                st.warning("먼저 '동의합니다'에 체크해 주세요.")
            elif not name:
                st.session_state.start_ready = False
                st.warning("이름 또는 닉네임을 입력해 주세요.")
            elif ready and name == st.session_state.get("start_ready_name"):
                _enter_app()                          # 파란 버튼 상태 → 다음 화면
                st.rerun()
            else:
                st.session_state.start_ready = True   # 이름 확정 → 버튼 파란색
                st.session_state.start_ready_name = name
                st.rerun()

        # 안내 문구
        if not agreed:
            st.caption("먼저 '동의합니다'에 체크해 주세요.")
        elif not ready:
            st.caption("이름을 입력하고 Enter를 누르면 [시작하기]가 파란색으로 바뀌어요.")
        else:
            st.caption("Enter를 한 번 더 누르거나 [시작하기]를 클릭하면 시작합니다.")


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
