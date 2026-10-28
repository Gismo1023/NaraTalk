# app_dashboard.py
<<<<<<< HEAD

=======
>>>>>>> 06d9502f299fbbabe506eeac4fe92f871b6fb343
import streamlit as st
import pandas as pd
import altair as alt
from src.db import get_practice_history, get_sentences


# 분석 대시보드 화면 및 오류 처리
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

    # 필요한 컬럼 확인
    required_columns = {
        "sentence_no",
        "level",
        "score",
        "substitutions",
        "deletions",
        "insertions",
    }

    if history and not required_columns.issubset(history[0].keys()):
        st.error(
            "get_practice_history.sql에 필요한 컬럼이 없습니다. "
            "SQL 버전을 확인해 주세요."
        )
        return

    # 요약 지표 계산
    total_practice = len(history)

    scores = [
        float(row["score"])
        for row in history
        if row["score"] is not None
    ]

    average_score = sum(scores) / len(scores) if scores else None

    practiced_sentences = {
        row["sentence_no"]
        for row in history
        if row["sentence_no"] is not None
    }

    learned_count = len(practiced_sentences)
    total_sentences = len(all_sentences)

    progress = (
        learned_count / total_sentences * 100
        if total_sentences
        else None
    )

    # 요약 지표 표시
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("총 연습 횟수", f"{total_practice}회")

    with col2:
        st.metric(
            "평균 점수",
            f"{average_score:.1f}점"
            if average_score is not None
            else "-"
        )

    with col3:
        st.metric("학습 문장 수", f"{learned_count}개")

    with col4:
        st.metric(
            "학습 진행률",
            f"{progress:.1f}%"
            if progress is not None
            else "-"
        )

    st.caption(
        f"전체 문장 {total_sentences}개 중 "
        f"{learned_count}개를 연습했습니다."
    )

    st.divider()

    # 오류 유형 분석
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

            chart = alt.Chart(error_data).mark_bar().encode(
                x=alt.X(
                    "오류 유형:N",
                    title="오류 유형",
                    axis=alt.Axis(labelAngle=0),
                ),
                y=alt.Y(
                    "오류 횟수:Q",
                    title="오류 횟수",
                ),
                tooltip=["오류 유형", "오류 횟수"],
            )

            st.altair_chart(
                chart,
                use_container_width=True,
            )

    st.divider()

    # 난이도별 결과
    st.subheader("난이도별 결과")

    with st.container(border=True):
        level_data = []

        for level in ["쉬움", "보통", "어려움"]:
            level_scores = [
                float(row["score"])
                for row in history
                if row["level"] == level
                and row["score"] is not None
            ]

            if level_scores:
                level_data.append({
                    "난이도": level,
                    "평균 점수": round(
                        sum(level_scores) / len(level_scores),
                        1,
                    ),
                })

        if level_data:
            level_df = pd.DataFrame(level_data)

            chart = alt.Chart(level_df).mark_bar().encode(
                x=alt.X(
                    "난이도:N",
                    title="난이도",
                    axis=alt.Axis(labelAngle=0),
                    sort=["쉬움", "보통", "어려움"],
                ),
                y=alt.Y(
                    "평균 점수:Q",
                    title="평균 점수",
                ),
                tooltip=["난이도", "평균 점수"],
            )

            st.altair_chart(
                chart,
                use_container_width=True,
            )
        else:
            st.caption("아직 난이도별 점수 데이터가 없습니다.")

    st.divider()

    # 성장 그래프
    st.subheader("성장 그래프")

    with st.container(border=True):
        if not history:
            st.caption(
                "아직 성장 그래프를 표시할 연습 기록이 없습니다."
            )
        else:
            daily_score = []

            for row in history:
                score = row.get("score")
                created_at = row.get("created_at")

                if score is None or created_at is None:
                    continue

                date = pd.to_datetime(
                    created_at,
                    errors="coerce",
                )

                if pd.isna(date):
                    continue

                daily_score.append({
                    "날짜": date.normalize(),
                    "점수": float(score),
                })

            if daily_score:
                daily_df = pd.DataFrame(daily_score)

                # 날짜별 평균 점수 계산
                daily_df = (
                    daily_df.groupby(
                        "날짜",
                        as_index=False,
                    )["점수"]
                    .mean()
                    .sort_values("날짜")
                    .reset_index(drop=True)
                )

                daily_df["점수"] = daily_df["점수"].round(1)
                daily_df["날짜표시"] = daily_df["날짜"].dt.strftime("%y-%m-%d")

                # 한 번에 최대 7일치 표시
                page_size = 7
                total_days = len(daily_df)
                max_start = max(0, total_days - page_size)

                # 최신 기록이 기본값
                slider_key = "growth_date_slider"

                if slider_key not in st.session_state:
                    st.session_state[slider_key] = max_start

                # 새 기록 추가 등으로 범위가 달라졌을 때 값 보정
                st.session_state[slider_key] = min(
                    max(0, st.session_state[slider_key]),
                    max_start,
                )


                # 한 번에 최대 7일치 표시
                page_size = 7
                total_days = len(daily_df)
                max_start = max(0, total_days - page_size)

                # 최신 기록을 기본값으로 설정
                slider_key = "growth_date_slider"

                if max_start > 0:
                    # 기존 슬라이더 값이 범위를 벗어나지 않도록 보정
                    current_value = st.session_state.get(
                        slider_key, max_start
                    )
                    current_value = min(
                        max(0, current_value),
                        max_start,
                    )

                    start_index = st.slider(
                        "과거 기록 ← 드래그 → 최신 기록",
                        min_value=0,
                        max_value=max_start,
                        value=current_value,
                        step=1,
                        key=slider_key,
                        help="슬라이더를 움직여 과거 학습 기록을 확인하세요.",
                    )
                else:
                    # 7일 이하라면 슬라이더 없이 전체 기록 표시
                    start_index = 0
                    st.caption(
                        "학습 기록이 7일 이하이므로 전체 기록을 표시합니다."
                    )

                # 선택한 위치부터 최대 7일치 표시
                view_df = daily_df.iloc[
                    start_index:start_index + page_size
                ].copy()


                # 성장 그래프
                chart = alt.Chart(view_df).mark_line(
                    point=True,
                ).encode(
                    x=alt.X(
                        "날짜표시:N",
                        title="학습 날짜",
                        sort=view_df["날짜표시"].tolist(),
                        axis=alt.Axis(labelAngle=0),
                    ),
                    y=alt.Y(
                        "점수:Q",
                        title="일일 평균점수",
                    ),
                    tooltip=[
                        alt.Tooltip(
                            "날짜표시:N",
                            title="학습 날짜",
                        ),
                        alt.Tooltip(
                            "점수:Q",
                            title="일일 평균점수",
                        ),
                    ],
                ).properties(
                    height=300,
                )

                st.altair_chart(
                    chart,
                    use_container_width=True,
                )

                st.caption(
                    f"총 {total_days}일의 학습 기록이 있습니다."
                )
            else:
                st.caption(
                    "날짜와 점수가 있는 학습 기록이 없습니다. "
                    "학습 기록의 날짜 컬럼을 확인해 주세요."
                )
