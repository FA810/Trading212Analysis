import streamlit as st
from theme_manager import inject_theme_sidebar

st.set_page_config(layout="wide")
TEMA_ATTIVO = inject_theme_sidebar()
st.title("Real Dividends Analysis")
st.markdown("---")
st.info("You can input your exclusive queries for dividends and tax withholdings here.")