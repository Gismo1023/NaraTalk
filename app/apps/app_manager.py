# app_manager.py

import streamlit as st
import pandas as pd
from src.db import get_practice_history, get_sentences

def page_manager():
    st.title("관리자")

    st.subheader("전처리 전후 비교")

    with st.container(border=True):
        st.caption("현재 DB에는 전처리 적용 전·후의 평가 결과가 따로 저장되지 않아 비교할 수 없습니다.")
