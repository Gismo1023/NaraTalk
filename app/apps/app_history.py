# app_history.py

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from src.db import get_practice_history

# 학습 이력 화면
def page_history():
    st.title("학습 이력")

    # 현재 로그인한 회원의 학습 기록 조회
    user_id = st.session_state.get("user_id")

    if user_id is None:
        st.warning("회원 정보를 확인할 수 없습니다. 다시 로그인해 주세요.")
        return

    try:
        rows = get_practice_history(user_id)
    except Exception as e:
        st.error(f"학습 기록을 불러오지 못했습니다: {e}")
        return

    # DB 기록을 화면에 표시할 데이터로 변환
    records = []

    for row in rows:
        raw_date = row.get("created_at", row.get("date"))

        if isinstance(raw_date, datetime):
            record_date = raw_date.date()
        elif isinstance(raw_date, date):
            record_date = raw_date
        elif raw_date is not None:
            try:
                record_date = pd.to_datetime(raw_date).date()
            except (TypeError, ValueError):
                record_date = None
        else:
            record_date = None

        raw_score = row.get("score")
        try:
            score = float(raw_score) if raw_score is not None else None
        except (TypeError, ValueError):
            score = None

        records.append({
            "날짜": record_date,
            "카테고리": row.get("category", "-"),
            "난이도": row.get("level", "-"),
            "연습 문장": row.get("ko", "-"),
            "점수": score,
        })

    all_df = pd.DataFrame(
        records,
        columns=["날짜", "카테고리", "난이도", "연습 문장", "점수"],
    )

    # 상단 요약 정보: 전체 학습 기록 기준
    total_count = len(all_df)

    valid_scores = pd.to_numeric(
        all_df["점수"], errors="coerce"
    ).dropna()

    average_score = (
        valid_scores.mean() if not valid_scores.empty else None
    )

    total_days = all_df["날짜"].nunique()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("총 학습 횟수", f"{total_count}회")

    with col2:
        st.metric(
            "평균 점수",
            f"{average_score:.1f}점"
            if average_score is not None else "-"
        )

    with col3:
<<<<<<< HEAD
        st.metric("총 학습일", "-")
=======
        st.metric("총 학습일", f"{total_days}일")
>>>>>>> 06d9502f299fbbabe506eeac4fe92f871b6fb343

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

    # 조회 버튼을 눌렀을 때 날짜 조건 확인
    if start_date > end_date:
        st.warning("시작 날짜는 종료 날짜보다 늦을 수 없습니다.")
        return

    # 날짜 조건은 하단 기록 표에만 적용
    history_df = all_df[
        (all_df["날짜"] >= start_date)
        & (all_df["날짜"] <= end_date)
    ].copy()

    # 같은 날짜, 카테고리, 난이도, 문장을 하나로 묶기
    if not history_df.empty:
        history_df = (
            history_df
            .groupby(
                ["날짜", "카테고리", "난이도", "연습 문장"],
                dropna=False,
                as_index=False,
            )
            .agg(
                연습_횟수=("점수", "size"),
                평균_점수=("점수", "mean"),
            )
            .rename(columns={
                "연습_횟수": "연습 횟수",
                "평균_점수": "평균 점수",
            })
            .sort_values("날짜", ascending=False)
        )

        history_df["평균 점수"] = history_df["평균 점수"].round(1)

    # 조회 버튼을 누르지 않았을 때도 기본 날짜 범위의 기록 표시
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
                format="%.1f점",
            ),
        },
        use_container_width=True,
        hide_index=True,
    )

    if history_df.empty:
        st.caption("선택한 날짜 범위에 학습 기록이 없습니다.")
