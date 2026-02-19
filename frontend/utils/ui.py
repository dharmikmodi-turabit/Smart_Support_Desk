import streamlit as st

def apply_global_style():
    """
    Apply global CSS styling to the Streamlit app.

    This function injects custom CSS to enhance the visual appearance of
    Streamlit components, including:

        - Adds padding to the main block container
        - Styles metric containers with background color, border radius, padding, and shadow
        - Styles DataFrame containers with rounded corners and hides overflow

    UI Impact:
        - Provides a modern, consistent look across all dashboards and forms

    Usage:
        - Call this function at the beginning of a Streamlit page or dashboard
          to apply the styling globally.

    Returns:
        None
    """

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
