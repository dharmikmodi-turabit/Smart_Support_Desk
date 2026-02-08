import streamlit as st
from api import api_call
import pandas as pd
# from ..backend.ai_engine import run_ai_chat

def ai_chatbot_page():
    st.subheader("🤖 AI CRM Assistant")
    st.caption("Ask questions about tickets, customers, and support operations")

    # Optional: role-based hint
    # st.markdown(f"**Logged in as:** `{user['role']}`")S

    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    # Show chat history
    # for msg in st.session_state.ai_chat_history:
    #     with st.chat_message(msg["role"]):
    #         st.markdown(msg["content"])
    # print("----------000000000------------",st.session_state.ai_chat_history)
    for msg in st.session_state.ai_chat_history:
        with st.chat_message(msg["role"]):
            # print("----------------------777777777777777777::::::::::",msg)
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
            # with st.spinner("Thinking..."):
            ai_response = api_call(
            "POST",
            "/ai/chat",
            st.session_state["token"],
            {
                "prompt" : user_prompt
            }
            )
                

            # CASE 1: API returns structured table
            # if isinstance(ai_response, dict) and ai_response.get("data"):
            #     df = pd.DataFrame(ai_response)

            #     st.dataframe(
            #         df,
            #         use_container_width=True,
            #         hide_index=True
            #     )

            #     st.session_state.ai_chat_history.append({
            #         "role": "assistant",
            #         "content": ai_response.get("message", ""),
            #         "table": ai_response["data"]
            #     })
            # if isinstance(ai_response, dict) and ai_response.get("data"):

            #     rows = ai_response["data"]   # ✅ real DB rows
            #     df = pd.DataFrame(rows)

            #     st.dataframe(
            #         df,
            #         use_container_width=True,
            #         hide_index=True
            #     )

            #     st.session_state.ai_chat_history.append({
            #         "role": "assistant",
            #         "content": "Here are the customers",
            #         "data": rows
            #     })
            # ---------------- AI RESPONSE HANDLING ----------------

            if isinstance(ai_response, dict) and ai_response.get("data"):
                # Tool / table response
                rows = ai_response["data"]

                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True)

                st.session_state.ai_chat_history.append({
                    "role": "assistant",
                    "content": "Here are the customers",
                    "data": rows
                })

            else:
                # Normal text response
                text = ai_response if isinstance(ai_response, str) else ""

                st.markdown(text)

                st.session_state.ai_chat_history.append({
                    "role": "assistant",
                    "content": text
                })



            # # CASE 2: Normal text response
            # else:
            #     print("^^^^^^^^^^^^^^^^^^^^^^>>>>>>>>>>>>>>>>>>>>>>")
            #     print(ai_response)
            #     if ai_response is None:
            #         print(ai_response)

            # # Store AI message
            # st.session_state.ai_chat_history.append({
            #     "role": "assistant",
            #     "content": ai_response or ""
            # })
