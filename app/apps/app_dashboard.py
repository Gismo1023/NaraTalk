# app_dashboard.py
import streamlit as st
import pandas as pd
from src.db import get_practice_history, get_sentences


# 분석 대시보드 화면 및 오류 처리 (바꾼 부분)
def page_dashboard():
    st.title("분석 대시보드")

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("먼저 닉네임으로 로그인해 주세요.")
        return

    try:
        history = get_practice_history(user_id)
        all_sentences = get_sentences()
    except Exception as error:
        st.error(f"분석 데이터를 불러오지 못했습니다: {error}")
        return

    # 회원별 기록을 조회하는 SQL에서 필요한 컬럼 확인 (추가한 부분)
    required_columns = {
        "sentence_no", "level", "score",
        "substitutions", "deletions", "insertions",
    }
    if history and not required_columns.issubset(history[0].keys()):
        st.error("get_practice_history.sql에 필요한 컬럼이 없습니다. SQL 버전을 확인해 주세요.")
        return

    total_practice = len(history)
    scores = [float(row["score"]) for row in history if row["score"] is not None]
    average_score = sum(scores) / len(scores) if scores else None

    practiced_sentences = {row["sentence_no"] for row in history if row["sentence_no"] is not None}
    learned_count = len(practiced_sentences)
    total_sentences = len(all_sentences)
    progress = learned_count / total_sentences * 100 if total_sentences else None

    # 요약 지표
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("총 연습 횟수", f"{total_practice}회")

    with col2:
        st.metric("평균 점수", f"{average_score:.1f}점" if average_score is not None else "-")

    with col3:
        st.metric("학습 문장 수", f"{learned_count}개")

    with col4:
        st.metric("학습 진행률", f"{progress:.1f}%" if progress is not None else "-")

    st.caption(f"전체 문장 {total_sentences}개 중 {learned_count}개를 연습했습니다.")

    st.divider()

    # 결과 값에 따라 그래프 넣기
    st.subheader("오류 유형 분석")

    with st.container(border=True):
        if not history:
            st.caption("아직 분석할 연습 기록이 없습니다.")
        else:
            error_data = pd.DataFrame({
                "오류 유형": ["대치", "삭제", "삽입"],
                "오류 횟수": [
                    sum(row["substitutions"] or 0 for row in history),
                    sum(row["deletions"] or 0 for row in history),
                    sum(row["insertions"] or 0 for row in history),
                ],
            })
            st.bar_chart(error_data, x="오류 유형", y="오류 횟수")

    st.divider()

    st.subheader("난이도별 결과")

    with st.container(border=True):
        level_data = []
        for level in ["쉬움", "보통", "어려움"]:
            level_scores = [
                float(row["score"])
                for row in history
                if row["level"] == level and row["score"] is not None
            ]
            if level_scores:
                level_data.append({
                    "난이도": level,
                    "평균 점수": round(sum(level_scores) / len(level_scores), 1),
                })

        if level_data:
            st.bar_chart(pd.DataFrame(level_data), x="난이도", y="평균 점수")
        else:
            st.caption("아직 난이도별 점수 데이터가 없습니다.")

    st.divider()

    st.subheader("성장 그래프")

    with st.container(border=True):
        daily_score = []