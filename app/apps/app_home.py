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