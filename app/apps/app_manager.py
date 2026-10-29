# app_manager.py

import streamlit as st
import pandas as pd
import altair as alt

from src.db import (
    get_count_users, get_nickname_cteated_at, get_category_top5,
    get_level_top5, get_sentence_top5, get_practice_history,get_manager_summary,
)
from src.core import clean_for_evaluation


def page_manager():
    st.title("관리자 대시보드")
    st.caption("서비스 운영 현황 및 사용자 발음 평가 데이터를 통합 모니터링합니다.")

    # 0. 상단 요약 지표 (방문자 수 / 총 연습량 등)
    st.subheader("📊 서비스 주요 지표 요약")

    try:
        # 방문자 수 (전체 가입 회원 수 기준)
        user_count = get_count_users()
        if isinstance(user_count, dict):
            user_count = user_count.get("total_users", 0)

        # 회원별 가입일 및 연습 횟수
        user_stats_rows = get_nickname_cteated_at()
        df_user_stats = pd.DataFrame(user_stats_rows) if user_stats_rows else pd.DataFrame()

        # 총 연습 횟수
        total_runs = (
            pd.to_numeric(df_user_stats["practice_count"], errors="coerce").fillna(0).sum()
            if not df_user_stats.empty and "practice_count" in df_user_stats.columns
            else 0
        )

        #전체 평균 점수 #전체 처리시간 평균
        summary = get_manager_summary()
        avg_score, avg_latency_ms = (
            summary["avg_score"],
            summary["avg_latency_ms"],
        )
        avg_latency_s = avg_latency_ms / 1000
        # 기존 DB 함수에는 전체 평균 점수와 전체 처리시간 집계 기능이 없음
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("총 방문자(회원) 수", f"{int(user_count or 0)}명")
        col_m2.metric("누적 연습 횟수", f"{int(total_runs)}회")
        col_m3.metric("전체 평균 점수", f"{round(avg_score, 1)}점")
        col_m4.metric("전체 처리시간 평균", f"{round(avg_latency_s, 2)}초")

        # 사용자별 가입일 및 연습 횟수 표 추가
        st.markdown("##### 👥 회원별 상세 현황 (등록일 및 연습 횟수)")

        if not df_user_stats.empty:
            # 날짜 형식 포맷팅 (YYYY-MM-DD)
            if "created_at" in df_user_stats.columns:
                df_user_stats["created_at"] = pd.to_datetime(
                    df_user_stats["created_at"], errors="coerce"
                ).dt.strftime("%Y-%m-%d")

            # 컬럼명을 화면 표시용으로 변경
            df_user_stats = df_user_stats.rename(columns={
                "nickname": "닉네임", "created_at": "등록일",
                "practice_count": "연습 횟수",
            })

            # "연습 횟수"를 정수형(int) 숫자로 유지
            if "연습 횟수" in df_user_stats.columns:
                df_user_stats["연습 횟수"] = (
                    pd.to_numeric(df_user_stats["연습 횟수"], errors="coerce")
                    .fillna(0).astype(int)
                )

            df_user_stats = df_user_stats[
                [c for c in ["닉네임", "등록일", "연습 횟수"] if c in df_user_stats.columns]
            ]

            st.dataframe(
                df_user_stats,
                column_config={
                    "닉네임": st.column_config.TextColumn("닉네임", width="medium"),
                    "등록일": st.column_config.TextColumn("등록일", width="medium"),
                    "연습 횟수": st.column_config.NumberColumn(
                        "연습 횟수 (회)", format="%d회", width="medium", alignment="left"
                    ),
                },
                use_container_width=True, hide_index=True,
            )
        else:
            st.caption("등록된 회원 정보가 없습니다.")

    except Exception as e:
        st.error(f"요약 지표를 불러오는 중 오류가 발생했습니다: {e}")

    st.divider()

    # 1. 사용자 전처리 전후 비교 (날짜별 선택 기능 추가)
    st.subheader("1. 사용자 전처리 전후 비교 (날짜별 조회)")
    st.caption("날짜를 선택한 후 해당 날짜의 세부 연습 기록을 선택하여 전처리 전후를 비교합니다.")

    with st.container(border=True):
        user_id = st.session_state.get("user_id")

        if user_id is None:
            st.info("전체 사용자 기록을 조회하려면 전체 기록 조회용 DB 함수가 필요합니다.")
        else:
            try:
                history_rows = get_practice_history(user_id)

                if not history_rows:
                    st.info("아직 DB에 저장된 사용자 연습 기록이 없습니다.")
                else:
                    df_history = pd.DataFrame(history_rows)

                    if "created_at" not in df_history.columns:
                        st.warning("연습 기록에 created_at 정보가 없습니다.")
                    else:
                        df_history["created_at"] = pd.to_datetime(
                            df_history["created_at"], errors="coerce"
                        )
                        df_history = df_history.dropna(subset=["created_at"])
                        df_history["조회 날짜"] = df_history["created_at"].dt.strftime("%Y-%m-%d")

                        # 날짜별 조회
                        available_dates = sorted(
                            df_history["조회 날짜"].unique().tolist(), reverse=True
                        )

                        if available_dates:
                            selected_date = st.selectbox(
                                "1️⃣ 조회할 날짜 선택", available_dates,
                                key="manager_date_select",
                            )
                            date_filtered_rows = df_history[
                                df_history["조회 날짜"] == selected_date
                            ]

                            # 세부 연습 기록 선택
                            options_map = {}
                            for i, (_, row) in enumerate(date_filtered_rows.iterrows()):
                                created_at = row["created_at"]
                                reference = row.get(
                                    "ko", row.get("reference", row.get("sentence", "문장 정보 없음"))
                                )
                                transcript = row.get("transcript") or "(인식된 텍스트 없음)"
                                label = (
                                    f"[{created_at.strftime('%H:%M:%S')}] "
                                    f"정답: {reference} → 인식(Raw): {transcript}"
                                )
                                if label in options_map:
                                    label = f"{i + 1}. {label}"
                                options_map[label] = row

                            selected_option = st.selectbox(
                                f"2️⃣ [{selected_date}] 해당 날짜의 세부 연습 기록 선택",
                                list(options_map.keys()), key="manager_history_select",
                            )

                            if selected_option:
                                chosen_record = options_map[selected_option]
                                raw_transcript = chosen_record.get("transcript") or ""
                                reference_text = chosen_record.get(
                                    "ko", chosen_record.get("reference", "정답 문장 정보 없음")
                                )
                                processed_transcript = clean_for_evaluation(raw_transcript)

                                col_info1, col_info2 = st.columns(2)
                                col_info1.metric("조회 날짜", selected_date)

                                cer = chosen_record.get("cer")
                                col_info2.metric(
                                    "CER (오류율)",
                                    f"{float(cer) * 100:.1f}%" if cer is not None else "-",
                                )

                                # 정답 기준 문장 표시
                                st.markdown(f"**정답 기준 문장 (Reference):** {reference_text}")

                                # 전처리 전후 비교
                                col_before, col_after = st.columns(2)
                                with col_before:
                                    st.markdown("#### 🔴 전처리 전 (STT 원본 인식값)")
                                    st.code(raw_transcript or "(인식된 텍스트 없음)", language="text")
                                with col_after:
                                    st.markdown("#### 🟢 전처리 후 (평가 엔진 투입값)")
                                    st.code(processed_transcript or "(결과 없음)", language="text")

            except Exception as e:
                st.error(f"사용자 연습 기록을 불러오지 못했습니다: {e}")

    st.divider()

    # 2. 이용 문장별 연습 횟수
    st.subheader("2. 이용 문장별 연습 횟수")

    with st.container(border=True):
        try:
            sentence_rows = get_sentence_top5()
            df_sentence = pd.DataFrame(sentence_rows) if sentence_rows else pd.DataFrame()

            if df_sentence.empty:
                st.caption("아직 집계할 연습 기록 데이터가 없습니다.")
            else:
                # DB 결과 컬럼명을 화면 표시용으로 변경
                df_sentence = df_sentence.rename(columns={
                    "ko": "문장", "sentence_ko": "문장",
                    "practice_count": "연습 횟수",
                })

                if "문장" not in df_sentence.columns or "연습 횟수" not in df_sentence.columns:
                    st.warning("문장 통계 결과에 필요한 컬럼이 없습니다.")
                else:
                    # 연습 횟수를 정수형(int)으로 유지
                    df_sentence["연습 횟수"] = (
                        pd.to_numeric(df_sentence["연습 횟수"], errors="coerce")
                        .fillna(0).astype(int)
                    )

                    # 문장별 연습 횟수 막대그래프
                    chart_sentence = alt.Chart(df_sentence).mark_bar().encode(
                        x=alt.X("연습 횟수:Q", title="연습 횟수", axis=alt.Axis(format="d")),
                        y=alt.Y("문장:N", sort="-x", title="연습 문장", axis=alt.Axis(labelLimit=300)),
                        tooltip=["문장", "연습 횟수"],
                    ).properties(height=300)

                    st.altair_chart(chart_sentence, use_container_width=True)

                    # 전체 문장별 연습 횟수 표
                    with st.expander("전체 문장별 연습 횟수 표 보기"):
                        st.dataframe(
                            df_sentence,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "sentence_no": st.column_config.TextColumn(
                                    "sentence_no",
                                    alignment="left"
                                ),
                                "연습 횟수": st.column_config.NumberColumn(
                                    "연습 횟수",
                                    format="%d",
                                    alignment="left"  # 연습 횟수 열은 왼쪽 정렬 (기본은 오른쪽)
                                )
                            }
                        )

        except Exception as e:
            st.error(f"문장 통계를 불러오는 중 오류가 발생했습니다: {e}")

    st.divider()

    # 3. 난이도별 연습 횟수
    st.subheader("3. 난이도별 연습 횟수")

    with st.container(border=True):
        try:
            level_rows = get_level_top5()
            df_level = pd.DataFrame(level_rows) if level_rows else pd.DataFrame()

            if df_level.empty:
                st.caption("아직 집계할 난이도 데이터가 없습니다.")
            else:
                # DB 결과 컬럼명을 화면 표시용으로 변경
                df_level = df_level.rename(columns={
                    "level": "난이도", "practice_count": "연습 횟수",
                })

                if "난이도" not in df_level.columns or "연습 횟수" not in df_level.columns:
                    st.warning("난이도 통계 결과에 필요한 컬럼이 없습니다.")
                else:
                    # 연습 횟수를 정수형(int)으로 유지
                    df_level["연습 횟수"] = (
                        pd.to_numeric(df_level["연습 횟수"], errors="coerce")
                        .fillna(0).astype(int)
                    )

                    # 난이도 표시 순서 지정
                    level_order = ["쉬움", "보통", "어려움"]
                    df_level["난이도"] = pd.Categorical(
                        df_level["난이도"], categories=level_order, ordered=True
                    )
                    df_level = df_level.sort_values("난이도")

                    # 난이도별 연습 횟수 막대그래프
                    bars = alt.Chart(df_level).mark_bar().encode(
                        x=alt.X(
                            "난이도:N", title="난이도", sort=level_order,
                            axis=alt.Axis(labelAngle=0),
                        ),
                        y=alt.Y("연습 횟수:Q", title="연습 횟수"),
                        tooltip=["난이도", "연습 횟수"],
                        color=alt.Color("난이도:N", title="난이도"),
                    )

                    # 막대 위에 연습 횟수 표시
                    text = bars.mark_text(
                        align="center", baseline="bottom", dy=-5,
                        fontSize=12, fontWeight="bold",
                    ).encode(text="연습 횟수:Q")

                    st.altair_chart((bars + text).properties(height=250), use_container_width=True)

        except Exception as e:
            st.error(f"난이도 통계를 불러오는 중 오류가 발생했습니다: {e}")

    st.divider()

    # 4. 카테고리별 연습 횟수
    st.subheader("4. 카테고리별 연습 횟수")

    with st.container(border=True):
        try:
            category_rows = get_category_top5()
            df_category = pd.DataFrame(category_rows) if category_rows else pd.DataFrame()

            if df_category.empty:
                st.caption("아직 집계할 카테고리 데이터가 없습니다.")
            else:
                # DB 결과 컬럼명을 화면 표시용으로 변경
                df_category = df_category.rename(columns={
                    "category": "카테고리", "practice_count": "연습 횟수",
                })

                if "카테고리" not in df_category.columns or "연습 횟수" not in df_category.columns:
                    st.warning("카테고리 통계 결과에 필요한 컬럼이 없습니다.")
                else:
                    # 연습 횟수를 정수형(int)으로 유지
                    df_category["연습 횟수"] = (
                        pd.to_numeric(df_category["연습 횟수"], errors="coerce")
                        .fillna(0).astype(int)
                    )
                    total_runs_sum = df_category["연습 횟수"].sum()

                    if total_runs_sum > 0:
                        # 카테고리별 연습 비율 계산
                        df_category["비율"] = df_category["연습 횟수"] / total_runs_sum * 100
                        df_category["비율표시"] = df_category["비율"].round(1).astype(str) + "%"

                        # 카테고리별 연습 비율 도넛 그래프
                        chart_category = alt.Chart(df_category).mark_arc(innerRadius=50).encode(
                            theta=alt.Theta("연습 횟수:Q"),
                            color=alt.Color("카테고리:N", title="카테고리"),
                            tooltip=[
                                "카테고리", "연습 횟수",
                                alt.Tooltip("비율표시:N", title="비율"),
                            ],
                        ).properties(height=300)

                        st.altair_chart(chart_category, use_container_width=True)

                        # 카테고리별 연습 횟수 및 비율 표
                        df_table = df_category[
                            ["카테고리", "연습 횟수", "비율표시"]
                        ].rename(columns={"비율표시": "비율"})

                        with st.expander("카테고리별 연습 횟수 표 보기"):
                            st.dataframe(
                                df_table,
                                column_config={
                                    "카테고리": st.column_config.TextColumn("카테고리", width="medium"),
                                    "연습 횟수": st.column_config.NumberColumn(
                                        "연습 횟수", format="%d회", width="small", alignment="left"
                                    ),
                                    "비율": st.column_config.TextColumn("비율", width="small"),
                                },
                                use_container_width=True, hide_index=True,
                            )
                    else:
                        st.caption("집계할 연습 횟수가 없습니다.")

        except Exception as e:
            st.error(f"카테고리 통계를 불러오는 중 오류가 발생했습니다: {e}")
