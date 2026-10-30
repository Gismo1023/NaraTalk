# app_dashboard.py
import streamlit as st
import pandas as pd
import altair as alt
from src.db import get_practice_history, get_sentences


# 그래프 축·범례 글자를 진하고 크게 (모든 그래프 공통)
AXIS_COLOR = "#000000"   # 축 글자·축선 색: 검정
TITLE_PAD = 28           # 축 제목과 축 사이 간격(픽셀, 약 2글자)


def bold_axes(chart):
    # Streamlit 기본 테마가 x축·y축 설정을 따로 덮어쓰므로, 축 종류별 설정에 모두 같은 값을 넣음
    axis_style = dict(
        labelColor=AXIS_COLOR, titleColor=AXIS_COLOR,
        labelFontSize=13, titleFontSize=14, titleFontWeight="bold",
        titlePadding=28,                                       # 축 제목과 축 사이 간격(약 2글자)
        domain=True, domainColor=AXIS_COLOR, domainWidth=2,      # 축선
        ticks=True, tickColor=AXIS_COLOR, tickWidth=1.5, tickSize=6,
        gridColor="#000000", gridWidth=1, gridOpacity=1,        # 눈금선: 검정(불투명)
    )
    chart = chart.configure_axis(**axis_style)
    for name in ("configure_axisX", "configure_axisY", "configure_axisBand",
                 "configure_axisQuantitative", "configure_axisTemporal", "configure_axisDiscrete"):
        if hasattr(chart, name):
            chart = getattr(chart, name)(**axis_style)
    # Streamlit 테마를 끄므로(theme=None) 배경·막대·선 색을 앱에 맞게 직접 지정
    chart = chart.configure(background="transparent").configure_view(stroke=None)
    chart = chart.configure_bar(color="#0068C9").configure_line(color="#0068C9").configure_point(color="#0068C9")
    return chart.configure_legend(
        labelColor=AXIS_COLOR, titleColor=AXIS_COLOR,
        labelFontSize=13, titleFontSize=13,
    )


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
    st.subheader("AI가 다르게 들은 유형")

    with st.container(border=True):
        if not history:
            st.caption("아직 분석할 연습 기록이 없습니다.")
        else:
            error_data = pd.DataFrame({
                "유형": ["다르게 들림", "빠짐", "더 들어감"],
                "횟수": [
                    sum(row["substitutions"] or 0 for row in history),
                    sum(row["deletions"] or 0 for row in history),
                    sum(row["insertions"] or 0 for row in history),
                ],
            })

            chart = alt.Chart(error_data).mark_bar().encode(
                x=alt.X(
                    "유형:N",
                    title="유형",
                    sort=None,
                    axis=alt.Axis(labelAngle=0, titlePadding=TITLE_PAD),
                ),
                y=alt.Y(
                    "횟수:Q",
                    title="글자 수",
                    axis=alt.Axis(titlePadding=TITLE_PAD),
                ),
                tooltip=["유형", "횟수"],
                # 막대마다 다른 색 (범례는 x축 이름과 겹치므로 숨김)
                color=alt.Color(
                    "유형:N",
                    scale=alt.Scale(
                        domain=["다르게 들림", "빠짐", "더 들어감"],
                        range=["#2C45A8", "#D9534F", "#F0A202"],
                    ),
                    legend=None,
                ),
            )

            # 막대 위에 숫자 표시
            bar_labels = alt.Chart(error_data).mark_text(
                dy=-10, fontSize=14, fontWeight="bold", color="#000000",
            ).encode(
                x=alt.X("유형:N", sort=None),
                y=alt.Y("횟수:Q"),
                text=alt.Text("횟수:Q", format="d"),
            )
            chart = chart + bar_labels

            st.altair_chart(bold_axes(chart), use_container_width=True, theme=None)

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
                    axis=alt.Axis(labelAngle=0, titlePadding=TITLE_PAD),
                    sort=["쉬움", "보통", "어려움"],
                ),
                y=alt.Y(
                    "평균 점수:Q",
                    title="평균 점수",
                    axis=alt.Axis(titlePadding=TITLE_PAD),
                ),
                tooltip=["난이도", "평균 점수"],
                # 난이도마다 다른 색: 쉬움 초록 · 보통 주황 · 어려움 빨강
                color=alt.Color(
                    "난이도:N",
                    scale=alt.Scale(
                        domain=["쉬움", "보통", "어려움"],
                        range=["#4CAF50", "#F0A202", "#D9534F"],
                    ),
                    legend=None,
                ),
            )

            # 막대 위에 평균 점수 표시
            bar_labels = alt.Chart(level_df).mark_text(
                dy=-10, fontSize=14, fontWeight="bold", color="#000000",
            ).encode(
                x=alt.X("난이도:N", sort=["쉬움", "보통", "어려움"]),
                y=alt.Y("평균 점수:Q"),
                text=alt.Text("평균 점수:Q", format=".1f"),
            )
            chart = chart + bar_labels

            st.altair_chart(bold_axes(chart), use_container_width=True, theme=None)
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

                # 최근 7일치만 표시 (슬라이더 없음)
                page_size = 7
                total_days = len(daily_df)
                start_index = max(0, total_days - page_size)

                if total_days > page_size:
                    st.caption(f"최근 {page_size}일의 학습 기록을 표시합니다.")
                else:
                    st.caption("전체 학습 기록을 표시합니다.")

                # 최근 7일치 데이터
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
                        axis=alt.Axis(labelAngle=0, titlePadding=TITLE_PAD),
                    ),
                    y=alt.Y(
                        "점수:Q",
                        title="일일 평균점수",
                        axis=alt.Axis(titlePadding=TITLE_PAD),
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
                )

                # 점 아래에 점수 표시 (소수점 첫째 자리, 예: 41.2점)
                point_labels = alt.Chart(view_df).mark_text(
                    dy=18,            # 점 아래로 18픽셀
                    fontSize=13,
                    fontWeight="bold",
                    color="#000000",
                ).encode(
                    x=alt.X("날짜표시:N", sort=view_df["날짜표시"].tolist()),
                    y=alt.Y("점수:Q"),
                    text=alt.Text("점수:Q", format=".1f"),
                )

                chart = (chart + point_labels).properties(height=300)

                st.altair_chart(bold_axes(chart), use_container_width=True, theme=None)

                st.caption(
                    f"총 {total_days}일의 학습 기록이 있습니다."
                )
            else:
                st.caption(
                    "날짜와 점수가 있는 학습 기록이 없습니다. "
                    "학습 기록의 날짜 컬럼을 확인해 주세요."
                )
