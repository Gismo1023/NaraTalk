# app_home.py

import streamlit as st
from datetime import datetime, date, timedelta
from src.db import register_user, login_user, login_manager, get_practice_history

def page_start():
    _, center, _ = st.columns([1, 2, 1])

    with center:
        st.title("🇰🇷 나랏말싸미")
        st.caption("한국어 발음 연습")

        st.markdown(
            "<div style='height: 40px;'></div>",
            unsafe_allow_html=True
        )

        st.markdown("### 음성 파일 이용 동의 안내")

        with st.expander("내용 보기", expanded=False):
            st.markdown("""
                **외국인 한국어 발음 교정 서비스 - 음성 녹음 및 데이터 수집 이용 동의서**

                **1. 수집 및 이용 목적**
                - 외국인 학습자의 한국어 발음 정확도 평가 및 오류 분석 (STT 모델 활용)
                - 개인 맞춤형 발음 피드백 및 모범 음성(TTS) 품질 고도화

                **2. 수집하는 항목**
                - 음성 녹음 파일 (.wav) 및 사용자가 발화한 텍스트 스크립트
                - 발음 평가 점수 및 오류율(WER/CER) 메타데이터

                **3. 보유 및 이용 기간**
                - 프로젝트 개발 및 평가 기간 동안만 한시적으로 활용하며,
                  프로젝트 종료(또는 모델 학습 완료) 즉시 원본 음성 데이터는 안전하게 파기합니다.

                **4. 동의 거부 권리 및 불이익**
                - 이용자는 음성 녹음 수집에 대한 동의를 거부할 수 있습니다.
                - 단, 동의를 거부하실 경우 음성 기반 발음 연습 및 실시간 피드백 서비스 이용이 제한될 수 있습니다.
            """)

        agreed = st.checkbox("위 안내 내용을 확인했으며 이에 동의합니다.")

        user_name = st.text_input(
            "이름",
            disabled=not agreed,
            placeholder=(
                "동의 후 이름을 입력해 주세요."
                if not agreed
                else "이름을 입력해 주세요."
            ),
            key="start_user_name",
        )

        nickname = user_name.strip()

        # 관리자 인증 오류는 닉네임이 바뀌면 초기화
        if st.session_state.get("manager_error_nickname") != nickname:
            st.session_state.manager_error_nickname = nickname
            st.session_state.manager_login_error = False

        # 관리자 닉네임을 입력했을 때만 비밀번호 입력란 표시
        if agreed and nickname == "관리자":
            manager_password = st.text_input(
                "관리자 비밀번호",
                type="password",
                key="manager_password",
                placeholder="관리자 비밀번호를 입력하세요.",
            )

            if st.button(
                    "관리자 로그인",
                    use_container_width=True,
                    disabled=not manager_password,
            ):
                try:
                    manager = login_manager(manager_password)

                    if (
                            manager is not None
                            and manager.get("manager_name") == "관리자"
                    ):
                        user = login_user(manager["manager_name"])

                        if user is None or user.get("id") is None:
                            st.error("users 테이블에 관리자 계정이 없습니다.")
                            return

                        if str(user["id"]) != str(manager["id_manager"]):
                            st.error("관리자 계정의 UUID가 일치하지 않습니다.")
                            return

                        st.session_state.user_name = user["nickname"]
                        st.session_state.user_id = user["id"]
                        st.session_state.is_admin = True
                        st.session_state.entered = True
                        st.session_state.page = "관리자"
                        st.session_state.manager_login_error = False
                        st.rerun()
                    else:
                        st.session_state.manager_login_error = True

                except Exception as e:
                    st.session_state.manager_login_error = True
                    st.error(f"관리자 인증 중 오류가 발생했습니다: {e}")

            if st.session_state.get("manager_login_error", False):
                st.error("관리자 비밀번호가 올바르지 않습니다.")

        # 일반 사용자의 기존 로그인 및 회원 등록
        elif st.button(
                "시작하기",
                use_container_width=True,
                disabled=not agreed or not nickname,
        ):
            try:
                user = login_user(nickname)

                if user is None:
                    user = register_user(nickname)

                if user is None or user.get("id") is None:
                    st.error("회원 정보를 확인하지 못했습니다.")
                    return

                st.session_state.user_name = user["nickname"]
                st.session_state.user_id = user["id"]
                st.session_state.is_admin = False
                st.session_state.entered = True
                st.session_state.page = "홈"
                st.rerun()

            except ValueError as e:
                st.error(str(e))

            except Exception as e:
                st.error(f"회원 정보를 처리하지 못했습니다: {e}")

def calculate_home_statistics(rows):
    today = date.today()

    # 오늘 학습 기록
    today_rows = [
        row for row in rows
        if row.get("created_at") is not None
        and (
            row["created_at"].date()
            if isinstance(row["created_at"], datetime)
            else row["created_at"]
        ) == today
    ]

    # 오늘 평균 점수
    scores = [
        float(row["score"])
        for row in today_rows
        if row.get("score") is not None
    ]

    today_count = len(today_rows)
    today_average = (
        sum(scores) / len(scores)
        if scores else None
    )

    # 학습한 날짜 목록
    learning_dates = set()

    for row in rows:
        created_at = row.get("created_at")

        if created_at is None:
            continue

        record_date = (
            created_at.date()
            if isinstance(created_at, datetime)
            else created_at
        )

        if isinstance(record_date, date):
            learning_dates.add(record_date)

    # 오늘 학습했다면 오늘부터, 아니라면 어제부터 연속일 계산
    current_day = today if today in learning_dates else today - timedelta(days=1)
    streak = 0

    while current_day in learning_dates:
        streak += 1
        current_day -= timedelta(days=1)

    return today_count, today_average, streak


def page_home():
    st.title("홈")

    st.subheader(
        f"{st.session_state.user_name}님, 환영합니다!"
    )

    # 요약 정보
    try:
        user_id = st.session_state.user_id
        rows = get_practice_history(user_id)

        today_count, today_average, streak = calculate_home_statistics(rows)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("오늘 학습 횟수", f"{today_count}회")

        with col2:
            if today_average is None:
                st.metric("오늘 평균 점수", "-")
            else:
                st.metric("오늘 평균 점수", f"{today_average:.1f}점")

        with col3:
            st.metric("연속 학습일", f"{streak}일")

    except Exception as e:
        st.error(f"학습 통계를 불러오지 못했습니다: {e}")

    st.divider()
    st.subheader("바로가기")

    if st.button("연습하기", use_container_width=True):
        st.session_state.page = "연습하기"
        st.rerun()

    st.subheader("안내")

    with st.container(border=True):
        st.write("* 음성 파일을 사용할 시에 반드시 동의가 필요합니다!")
        st.write("* 즐거운 발음 연습이 되시길 바랍니다.")
        st.write("* 문의 시 000을 이용해주시기 바랍니다.")

# -----퀴즈 추가 코드------------------------------------------------------------
    render_daily_quiz_form()

SPELLING_QUIZZES = [
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["어이없다", "어의없다"],
        "answer": "어이없다",
        "explanation": "'이렇다 할만한 뜻이나 이유가 없다'는 뜻은 '어이없다'가 맞습니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["몇일 동안", "며칠 동안"],
        "answer": "며칠 동안",
        "explanation": "'몇 일'은 쓰이지 않으며 항상 '며칠'로 적어야 합니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": [ "감기를 낳다", "감기를 낫다"],
        "answer": "감기를 낫다",
        "explanation": "병이나 상처가 고쳐지는 것은 '낫다', 아이나 알을 몸 밖으로 배출하는 것은 '낳다'입니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["문제를 맞추다", "문제를 맞히다"],
        "answer": "문제를 맞히다",
        "explanation": "정답을 고르거나 맞게 하는 것은 '맞히다', 서로 비교하거나 조화시키는 것은 '맞추다'입니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["안 된다", "않 된다"],
        "answer": "안 된다",
        "explanation": "'아니'의 줄임말은 '안', '아니하다'의 줄임말은 '않'입니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["설레임", "설레는 마음"],
        "answer": "설레는 마음",
        "explanation": "동사 '설레다'의 명사형 표기는 '설렘'이 올바릅니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["금세 끝났다", "금새 끝났다"],
        "answer": "금세 끝났다",
        "explanation": "'금시에'가 줄어든 말이므로 '금세'가 맞습니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["구두를 띄다", "구두를 띠다"],
        "answer": "구두를 띄다",
        "explanation": "사이를 멀게 하거나 눈을 크게 뜨는 등은 '띄다'가 맞습니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["역사 안티테제", "역사 안티체제"],
        "answer": "역사 안티테제",
        "explanation": "'안티테제(Antithese)'가 올바른 외래어 표기입니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["스스럼업이", "스스럼없이"],
        "answer": "스스럼없이",
        "explanation": "부사 파생 접미사가 붙어 '스스럼없이'로 적습니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["구십 구", "구십구"],
        "answer": "구십구",
        "explanation": "만 단위 이하의 숫자는 띄어쓰지 않고 붙여 씁니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["알은체하다", "알은 체 하다"],
        "answer": "알은체하다",
        "explanation": "‘-체하다’는 하나의 보조 용언이므로 붙여 씁니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["오랫만에", "오랜만에"],
        "answer": "오랜만에",
        "explanation": "'오랜만'은 '오래간만'의 줄임말로 '오랜만에'가 표준어입니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["지긋지긋하다", "지겟지겟하다"],
        "answer": "지긋지긋하다",
        "explanation": "참기 힘들 정도로 넌더리가 나는 모양은 '지긋지긋하다'입니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["부인하다", "부분하다"],
        "answer": "부인하다",
        "explanation": "사실이 아니라고 인정하지 않는 것은 '부인(否認)하다'입니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["바람피다", "바람피우다"],
        "answer": "바람피우다",
        "explanation": "'바람피우다'가 표준어 기본형입니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["서슴지 않고", "서슴치 않고"],
        "answer": "서슴지 않고",
        "explanation": "'서슴다' 어간 뒤에 '-지'가 붙어 '서슴지'가 됩니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["허우적대다", "허우적거리다"],
        "answer": "허우적거리다",
        "explanation": "둘 다 표준어로 인정되지만 보통 기본형으로는 '허우적거리다'가 많이 쓰입니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["띄어쓰기", "뛰어쓰기"],
        "answer": "띄어쓰기",
        "explanation": "글을 쓸 때 낱말과 낱말 사이를 띄어 쓰는 것은 '띄어쓰기'입니다."
    },
    {
        "question": "다음 중 올바른 표기는 무엇일까요?",
        "options": ["안절부절 못하다", "안절부절못하다"],
        "answer": "안절부절못하다",
        "explanation": "'안절부절못하다'는 한 단어이므로 붙여 씁니다."
    }
]

CULTURE_QUIZZES = [
    {
        "question": "대한민국의 수도는 어디일까요?",
        "options": ["부산", "서울", "인천", "제주"],
        "answer": "서울",
        "explanation": "대한민국의 수도는 서울특별시입니다."
    },
    {
        "question": "한글을 창제하신 조선의 왕은 누구일까요?",
        "options": ["태조 이성계", "정조", "광개토대왕", "세종대왕"],
        "answer": "세종대왕",
        "explanation": "세종대왕께서 1443년 훈민정음(한글)을 창제하셨습니다."
    },
    {
        "question": "한국의 전통 의복은 무엇일까요?",
        "options": ["한복", "기모노", "치파오", "아오자이"],
        "answer": "한복",
        "explanation": "한국의 전통 옷은 '한복'입니다."
    },
    {
        "question": "한국에서 '음력 1월 1일'을 부르는 최대 명절은 무엇일까요?",
        "options": ["추석", "단오", "설날", "한식"],
        "answer": "설날",
        "explanation": "음력 1월 1일은 '설날'이며, 음력 8월 15일은 '추석'입니다."
    },
    {
        "question": "대한민국의 화폐 단위는 무엇일까요?",
        "options": ["엔(JPY)", "원(KRW)", "달러(USD)", "위안(CNY)"],
        "answer": "원(KRW)",
        "explanation": "대한민국의 통화 단위는 '원'입니다."
    },
    {
        "question": "조선 시대의 최고 교육 기관으로 서울에 위치했던 곳은?",
        "options": ["성균관", "서원", "향교", "규장각"],
        "answer": "성균관",
        "explanation": "조선 시대 최고 국가 교육 기관은 성균관입니다."
    },
    {
        "question": "한국의 국기인 '태극기'의 네 모서리에 있는 검은색 막대들을 무엇이라 부를까요?",
        "options": ["팔괘", "삼태극", "사괘", "음양오행"],
        "answer": "사괘",
        "explanation": "태극기 테두리의 건, 곤, 감, 리 네 막대를 '사괘'라고 합니다."
    },
    {
        "question": "유네스코 세계문화유산으로 지정된 조선시대의 대표적인 왕실 궁궐은?",
        "options": ["경복궁", "창덕궁", "덕수궁", "경희궁"],
        "answer": "창덕궁",
        "explanation": "자연과 조화를 이룬 아름다움으로 창덕궁이 유네스코 세계문화유산에 등재되어 있습니다."
    },
    {
        "question": "임진왜란 당시 조선 수군을 승리로 이끈 명장이며 거북선을 개선한 영웅은?",
        "options": ["이순신", "권율", "강감찬", "을지문덕"],
        "answer": "이순신",
        "explanation": "충무공 이순신 장군은 임진왜란 때 조선을 구한 명장입니다."
    },
    {
        "question": "한국의 전통 무술로, 손과 발을 주로 사용하는 세계적인 스포츠는?",
        "options": ["유도", "검도", "씨름", "태권도"],
        "answer": "태권도",
        "explanation": "대한민국의 국기(國技)이자 올림픽 종목인 태권도입니다."
    },
    {
        "question": "음력 5월 5일로, 여은들이 창포물에 머리를 감는 전통 명절은?",
        "options": ["추석", "설날", "단오", "동지"],
        "answer": "단오",
        "explanation": "음력 5월 5일은 단오이며, 옛날 사람들은 창포물에 머리를 감는 풍습이 있었습니다."
    },
    {
        "question": "신라 시대의 화랑들이 심신을 단련하던 명산으로 유명한 강원도의 산은?",
        "options": ["오대산", "설악산", "태백산", "치악산"],
        "answer": "설악산",
        "explanation": "강원도의 대표적인 명산이자 화랑들이 수도하던 곳으로 유명합니다."
    },
    {
        "question": "한국에서 가장 큰 섬이자 세계적인 화산섬으로 유네스코에 등재된 곳은?",
        "options": ["제주도", "울릉도", "거제도", "강화도"],
        "answer": "제주도",
        "explanation": "제주도는 한라산과 독특한 화산 지형을 가진 대한민국의 대표 섬입니다."
    },
    {
        "question": "조선 후기 정조가 부모인 사도세자를 그리기 위해 경기도 수원에 축조한 성곽은?",
        "options": ["남한산성", "북한산성", "수원 화성", "진주성"],
        "answer": "수원 화성",
        "explanation": "정조가 세운 계획도시이자 유네스코 세계문화유산인 수원 화성입니다."
    },
    {
        "question": "한국의 고유 악기로, 거문고와 함께 대표적인 현악기로 꼽히는 것은?",
        "options": ["가야금", "대금", "해금", "장구"],
        "answer": "가야금",
        "explanation": "가야의 가실왕이 만들었다고 전해지는 열두 줄의 현악기 가야금입니다."
    },
    {
        "question": "삼국시대 중 가장 전성기를 맞아 한강 유역을 차지하고 삼국을 통일한 기반을 마련한 왕은?",
        "options": ["광개토대왕", "문무왕", "근초고왕", "진흥왕"],
        "answer": "진흥왕",
        "explanation": "신라의 진흥왕은 한강 유역을 장악하고 영토를 크게 넓혔습니다."
    },
    {
        "question": "한국의 전통 주거 형태로서 아궁이의 열기로 방바닥을 데우는 난방 장치는?",
        "options": ["마루", "처마", "온돌", "한옥"],
        "answer": "온돌",
        "explanation": "한국 고유의 난방 방식으로 바닥을 따뜻하게 데우는 온돌 시스템입니다."
    },
    {
        "question": "대한민국 국경일 중 3월 1일에 일어난 독립 만세 운동을 기념하는 날은?",
        "options": ["삼일절", "광복절", "개천절", "제헌절"],
        "answer": "삼일절",
        "explanation": "1919년 3월 1일의 3·1 독립운동을 기념하는 국경일입니다."
    },
    {
        "question": "세계에서 가장 오래된 금속활자본으로 인정받는 고려시대의 불교 유물은?",
        "options": ["직지심체요절", "팔만대장경", "무구정광대다리니경", "청자 투각칠보문 향로"],
        "answer": "직지심체요절",
        "explanation": "백운화상초록 불조직지심체요절은 현존 세계 최고(最古)의 금속활자 인쇄본입니다."
    },
    {
        "question": "동의보감을 집필한 조선시대의 명의는 누구일까요?",
        "options": ["장기봉", "이제마", "허준", "정약용"],
        "answer": "허준",
        "explanation": "조선 광해군 때 허준이 편찬한 의학 서적이자 유네스코 세계기록유산인 동의보감입니다."
    }
]


def render_daily_quiz_form():
    import random

    st.divider()
    st.subheader("📚 오늘의 퀴즈")
    st.caption("맞춤법과 한국 문화 상식 문제를 하나씩 풀고 다음 문제로 도전해 보세요!")

    # 1. 최초 진입 시 20개 전체 중에서 무작위로 5문제씩 뽑아서 세션에 저장 (원하신다면 개수를 늘리거나 전체로 변경 가능)
    if "spelling_pool" not in st.session_state:
        st.session_state["spelling_pool"] = random.sample(SPELLING_QUIZZES, min(5, len(SPELLING_QUIZZES)))
        st.session_state["sp_idx"] = 0
        st.session_state["sp_score"] = 0
        st.session_state["spelling_submitted"] = False
        st.session_state["user_spelling_ans"] = None

    if "culture_pool" not in st.session_state:
        st.session_state["culture_pool"] = random.sample(CULTURE_QUIZZES, min(5, len(CULTURE_QUIZZES)))
        st.session_state["cu_idx"] = 0
        st.session_state["cu_score"] = 0
        st.session_state["culture_submitted"] = False
        st.session_state["user_culture_ans"] = None

    col1, col2 = st.columns(2)

    # --- 2. 왼쪽: 한국어 맞춤법 영역 ---
    with col1:
        sp_pool = st.session_state["spelling_pool"]
        sp_idx = st.session_state["sp_idx"]
        total_sp = len(sp_pool)

        st.markdown("### <span style='color: red;'>ㄱ</span><span style='color: blue;'>ㄴ</span>한국어 맞춤법",
                    unsafe_allow_html=True)

        if sp_idx >= total_sp:
            with st.container(border=True):
                st.success(f"💐 맞춤법 퀴즈 완료!\n\n총 **{total_sp}문제 중 {st.session_state['sp_score']}문제**를 맞히셨습니다!!")
                if st.button("맞춤법 문제 다시 풀기", key="restart_sp", use_container_width=True):
                    st.session_state["spelling_pool"] = random.sample(SPELLING_QUIZZES, min(5, len(SPELLING_QUIZZES)))
                    st.session_state["sp_idx"] = 0
                    st.session_state["sp_score"] = 0
                    st.session_state["spelling_submitted"] = False
                    st.session_state["user_spelling_ans"] = None
                    st.rerun()
        else:
            q_sp = sp_pool[sp_idx]
            st.caption(f"진행도: {sp_idx + 1} / {total_sp}")

            if not st.session_state.get("spelling_submitted", False):
                with st.form("spelling_quiz_form"):
                    st.markdown(f"**Q. {q_sp['question']}**")
                    user_sp_choice = st.radio(
                        "sp_choice",
                        q_sp["options"],
                        key=f"radio_sp_{sp_idx}",
                        label_visibility="collapsed"
                    )
                    st.write("")

                    sp_submitted = st.form_submit_button("제출하기", use_container_width=True)
                    if sp_submitted:
                        st.session_state["spelling_submitted"] = True
                        st.session_state["user_spelling_ans"] = user_sp_choice
                        if user_sp_choice == q_sp["answer"]:
                            st.session_state["sp_score"] += 1
                        st.rerun()
            else:
                chosen = st.session_state["user_spelling_ans"]
                correct = q_sp["answer"]

                with st.container(border=True):
                    st.markdown(f"**Q. {q_sp['question']}**")
                    if chosen == correct:
                        st.success(f"⭕ 정답입니다! (선택: {chosen})")
                    else:
                        st.error(f"❌ 틀렸습니다. (선택: {chosen} / 정답: {correct})")
                    st.caption(f"💡 {q_sp['explanation']}")

                if st.button("다음 문제", key=f"next_sp_{sp_idx}", use_container_width=True):
                    st.session_state["sp_idx"] += 1
                    st.session_state["spelling_submitted"] = False
                    st.session_state["user_spelling_ans"] = None
                    st.rerun()

    # --- 3. 오른쪽: 한국 문화 상식 영역 ---
    with col2:
        cu_pool = st.session_state["culture_pool"]
        cu_idx = st.session_state["cu_idx"]
        total_cu = len(cu_pool)

        st.markdown(
            "### <img src='https://flagcdn.com/w40/kr.png' width='28' style='vertical-align: middle; margin-right: 5px;'> 한국 문화 상식",
            unsafe_allow_html=True)

        if cu_idx >= total_cu:
            with st.container(border=True):
                st.success(f"💐 상식 퀴즈 완료!\n\n총 **{total_cu}문제 중 {st.session_state['cu_score']}문제**를 맞히셨습니다!!")
                if st.button("한국 상식 문제 다시 풀기", key="restart_cu", use_container_width=True):
                    st.session_state["culture_pool"] = random.sample(CULTURE_QUIZZES, min(5, len(CULTURE_QUIZZES)))
                    st.session_state["cu_idx"] = 0
                    st.session_state["cu_score"] = 0
                    st.session_state["culture_submitted"] = False
                    st.session_state["user_culture_ans"] = None
                    st.rerun()
        else:
            q_cu = cu_pool[cu_idx]
            st.caption(f"진행도: {cu_idx + 1} / {total_cu}")

            if not st.session_state.get("culture_submitted", False):
                with st.form("culture_quiz_form"):
                    st.markdown(f"**Q. {q_cu['question']}**")
                    user_cu_choice = st.radio(
                        "cu_choice",
                        q_cu["options"],
                        key=f"radio_cu_{cu_idx}",
                        label_visibility="collapsed"
                    )
                    st.write("")

                    cu_submitted = st.form_submit_button("제출하기", use_container_width=True)
                    if cu_submitted:
                        st.session_state["culture_submitted"] = True
                        st.session_state["user_culture_ans"] = user_cu_choice
                        if user_cu_choice == q_cu["answer"]:
                            st.session_state["cu_score"] += 1
                        st.rerun()
            else:
                chosen = st.session_state["user_culture_ans"]
                correct = q_cu["answer"]

                with st.container(border=True):
                    st.markdown(f"**Q. {q_cu['question']}**")
                    if chosen == correct:
                        st.success(f"⭕ 정답입니다! (선택: {chosen})")
                    else:
                        st.error(f"❌ 틀렸습니다. (선택: {chosen} / 정답: {correct})")
                    st.caption(f"💡 {q_cu['explanation']}")

                if st.button("다음 문제", key=f"next_cu_{cu_idx}", use_container_width=True):
                    st.session_state["cu_idx"] += 1
                    st.session_state["culture_submitted"] = False
                    st.session_state["user_culture_ans"] = None
                    st.rerun()
# 럭키쿠키------------
    st.divider()

    FORTUNE_COOKIES = [
        {"fortune": "오늘 '감사합니다'를 3번 말하면 큰 행운이 찾아와요!",
         "word": "<span style='background-color: white; color: black; padding: 2px 6px; border-radius: 4px; font-weight: bold;'>감사 (Gratitude)</span>",
         "tip": "[감사] - 억양을 평온하게 유지해 보세요."},
        {"fortune": "새로운 한국어 단어를 도전하기 아주 좋은 날이에요!",
         "word": "<span style='background-color: white; color: black; padding: 2px 6px; border-radius: 4px; font-weight: bold;'>도전 (Challenge)</span>",
         "tip": "[도전] - 'ㄷ' 발음을 명확하게 찍어주세요."},
        {"fortune": "발음 연습을 하면 할수록 자신감이 쑥쑥 올라갑니다!",
         "word": "<span style='background-color: white; color: black; padding: 2px 6px; border-radius: 4px; font-weight: bold;'>자신감 (Confidence)</span>",
         "tip": "[자신감] - '신'을 부드럽게 발음해요."},
        {"fortune": "오늘 연습한 문장이 조만간 실제 대화에서 쓰이게 될 거예요!",
         "word": "<span style='background-color: white; color: black; padding: 2px 6px; border-radius: 4px; font-weight: bold;'>기회 (Opportunity)</span>",
         "tip": "[기회] - 'ㅎ' 소리가 너무 세지 않게 주의하세요."},
        {"fortune": "꾸준히 한 발짝씩 나아가는 당신의 모습이 멋져요!",
         "word": "<span style='background-color: white; color: black; padding: 2px 6px; border-radius: 4px; font-weight: bold;'>꾸준함 (Consistency)</span>",
         "tip": "[꾸준함] - 된소리 'ᄁ'을 혀뿌리에 힘을 주어 발음해요."},
        {"fortune": "칭찬을 듣게 될 기분 좋은 하루가 될 것 같아요!",
         "word": "<span style='background-color: white; color: black; padding: 2px 6px; border-radius: 4px; font-weight: bold;'>칭찬 (Praise)</span>",
         "tip": "[칭찬] - 'ᄎ' 거센소리를 시원하게 내보내세요."}
    ]


    # 럭키 쿠키 UI 화면 구성 (작은 하이라이트 박스 형태)
    with st.container(border=True):
        import random
        col_cookie1, col_cookie2 = st.columns([1, 3])

        with col_cookie1:
            st.markdown("### 🥠 **럭키 쿠키**")
            st.caption("오늘의 운세 뽑기")

        with col_cookie2:
            if "cookie_result" not in st.session_state:
                if st.button("🥠 쿠키 깨뜨리기!", key="open_cookie"):
                    st.session_state["cookie_result"] = random.choice(FORTUNE_COOKIES)
                    st.rerun()
                else:
                    st.caption("버튼을 눌러 오늘의 한국어 운세와 추천 단어를 확인해보세요!")
            else:
                res = st.session_state["cookie_result"]
                st.markdown(f"✨ **오늘의 운세:** *\"{res['fortune']}\"*")
                st.markdown(f"💡 **오늘의 단어:** {res['word']} | **발음 팁:** {res['tip']}", unsafe_allow_html=True)
                if st.button("다른 쿠키 뽑기", key="retry_cookie"):
                    st.session_state["cookie_result"] = random.choice(FORTUNE_COOKIES)
                    st.rerun()