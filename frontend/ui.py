import streamlit as st

def apply_global_style():
    st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    div[data-testid="metric-container"] {
        background: #0f172a;
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    div[data-testid="stDataFrame"] {
        border-radius: 14px;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)
