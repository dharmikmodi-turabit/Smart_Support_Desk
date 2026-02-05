import streamlit as st
from api import api_call
# from ..backend.ai_engine import run_ai_chat

def ai_chatbot_page():
    st.subheader("🤖 AI CRM Assistant")
    st.caption("Ask questions about tickets, customers, and support operations")

    # Optional: role-based hint
    # st.markdown(f"**Logged in as:** `{user['role']}`")S

    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    # Show chat history
    for msg in st.session_state.ai_chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_prompt = st.chat_input("Ask something...")

    if user_prompt:
        # Store user message
        st.session_state.ai_chat_history.append({
            "role": "user",
            "content": user_prompt
        })

        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Call AI
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ai_response = api_call(
            "GET",
            "/ai/chat",
            st.session_state["token"],

        )
                st.markdown(ai_response)

        # Store AI message
        st.session_state.ai_chat_history.append({
            "role": "assistant",
            "content": ai_response
        })
