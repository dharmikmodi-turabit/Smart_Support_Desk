import streamlit as st
from api import api_call
import pandas as pd
# from ..backend.ai_engine import run_ai_chat

def ai_chatbot_page():
    st.subheader("🤖 AI CRM Assistant")
    st.caption("Ask questions about tickets, customers, and support operations")

    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []
    for msg in st.session_state.ai_chat_history:
        with st.chat_message(msg["role"]):
            if "table" in msg.keys():
                st.markdown(msg["content"])
                st.dataframe(
                    pd.DataFrame(msg["table"]),
                    use_container_width=True,
                    hide_index=True
                )
            elif "data" in msg.keys():
                st.markdown(msg["content"])
                st.dataframe(
                    pd.DataFrame(msg["data"]),
                    use_container_width=True,
                    hide_index=True
                )

            else:
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
                "POST",
                "/ai/chat",
                st.session_state["token"],
                {
                    "prompt" : user_prompt
                }
                )
                if ai_response is None:
                    st.error("Backend returned no response")
                    return
                if isinstance(ai_response, dict) and ai_response.get("data"):
                    # Tool / table response
                    rows = ai_response["data"]
                    message = ai_response["message"]

                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    st.session_state.ai_chat_history.append({
                        "role": "assistant",
                        "content": message,
                        "data": rows
                    })

                else:
                    # Normal text response
                    message = ai_response['message']

                    st.markdown(message)

                    st.session_state.ai_chat_history.append({
                        "role": "assistant",
                        "content": message
                    })
