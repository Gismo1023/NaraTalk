# app_history.py

import streamlit as st
import pandas as pd
from datetime import date

# 학습 이력 화면
def page_history():
    st.title("학습 이력")

    # 요약 정보
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("총 학습 횟수", "-")

    with col2:
        st.metric("평균 점수", "-")

    with col3:
        st.metric("총 학습일", "-")

    st.divider()
    st.subheader("조회 조건")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "시작 날짜",
            value=date.today(),
            key="skeleton_start_date",
        )

    with col2:
        end_date = st.date_input(
            "종료 날짜",
            value=date.today(),
            key="skeleton_end_date",
        )

    search_clicked = st.button(
        "조회",
        use_container_width=True,
    )

    st.divider()
    st.subheader("학습 기록")

    history_df = pd.DataFrame(
        columns=[
            "날짜",
            "카테고리",
            "난이도",
            "연습 문장",
            "연습 횟수",
            "평균 점수",
        ]
    )

    # 조회 버튼을 눌렀을 때 날짜 조건 확인
    if search_clicked:
        if start_date > end_date:
            st.warning("시작 날짜는 종료 날짜보다 늦을 수 없습니다.")
            return

        # 날짜 컬럼이 존재하는 학습 기록만 조회 조건 적용
        if not history_df.empty:
            history_df["날짜"] = pd.to_datetime(
                history_df["날짜"]
            ).dt.date

            history_df = history_df[
                (history_df["날짜"] >= start_date)
                & (history_df["날짜"] <= end_date)
            ]

    st.dataframe(
        history_df,
        column_config={
            "날짜": st.column_config.DateColumn(
                "날짜",
                format="YYYY-MM-DD",
                width="small",
            ),
            "카테고리": st.column_config.TextColumn(
                "카테고리",
                width="small",
            ),
            "난이도": st.column_config.TextColumn(
                "난이도",
                width="small",
            ),
            "연습 문장": st.column_config.TextColumn(
                "연습 문장",
                width="large",
            ),
            "연습 횟수": st.column_config.NumberColumn(
                "연습 횟수",
                width="small",
            ),
            "평균 점수": st.column_config.NumberColumn(
                "평균 점수",
                width="small",
            ),
        },
        use_container_width=True,
        hide_index=True,
    )

    if history_df.empty:
        st.caption(
            "조회 조건에 맞는 학습 기록이 없거나 아직 데이터가 연결되지 않았습니다."
        )
