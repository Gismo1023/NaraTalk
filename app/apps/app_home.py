import streamlit as st

from src.db import register_user, login_user


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

        agreed = st.checkbox(
            "위 안내 내용을 확인했으며 이에 동의합니다."
        )

        user_name = st.text_input(
            "이름",
            disabled=not agreed,
            placeholder=(
                "동의 후 이름을 입력해 주세요."
                if not agreed
                else "이름을 입력해 주세요."
            ),
        )

        if st.button(
            "시작하기",
            use_container_width=True,
            disabled=not agreed or not user_name.strip(),
        ):
            nickname = user_name.strip()

            try:
                # 기존 회원인지 조회
                user = login_user(nickname)

                # 회원이 없으면 신규 등록
                if user is None:
                    user = register_user(nickname)

                # 회원 정보가 정상적으로 반환되었는지 확인
                if user is None or user.get("id") is None:
                    st.error("회원 정보를 확인하지 못했습니다.")
                    return

                # 세션에 회원 정보 저장
                st.session_state.user_name = user["nickname"]
                st.session_state.user_id = user["id"]
                st.session_state.entered = True
                st.session_state.page = "홈"

                st.rerun()

            except ValueError as e:
                st.error(str(e))

            except Exception as e:
                st.error(f"회원 정보를 처리하지 못했습니다: {e}")


def page_home():
    st.title("홈")

    st.subheader(
        f"{st.session_state.user_name}님, 환영합니다!"
    )

    # 요약 정보
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("오늘 학습 횟수", "-")

    with col2:
        st.metric("오늘 평균 점수", "-")

    with col3:
        st.metric("연속 학습일", "-")

    # 나중에 데이터를 합치고 수정해야 하는 부분
    # with col1:
    #     st.metric("총 연습 횟수", f"{total_practice}회")
    #
    # with col2:
    #     st.metric("평균 점수", f"{average_score:.1f}점")
    #
    # with col3:
    #     st.metric("연속 학습일", f"{streak_days}일")

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
