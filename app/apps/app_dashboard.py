# app_dashboard.py

import streamlit as st

# 분석 대시보드 화면
def page_dashboard():
    st.title("분석 대시보드")

    # 요약 지표
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("총 연습 횟수", "-")

    with col2:
        st.metric("평균 점수", "-")

    with col3:
        st.metric("학습 문장 수", "-")

    with col4:
        st.metric("학습 진행률", "-")

    # 요약지표 데이터 결과 수정하기

    st.divider()

    # 결과 값에 따라 그래프 넣기
    st.subheader("오류 유형 분석")

    with st.container(border=True):
        st.caption("오류 유형별 분석 결과가 표시될 영역입니다.")

    st.divider()

    st.subheader("난이도별 결과")

    with st.container(border=True):
        st.caption("난이도별 학습 현황이 표시될 영역입니다.")

    st.divider()

    st.subheader("전처리 전후 비교")

    with st.container(border=True):
        st.caption("전처리 전후 비교 결과가 표시될 영역입니다.")
