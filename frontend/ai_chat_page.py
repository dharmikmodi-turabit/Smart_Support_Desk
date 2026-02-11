import streamlit as st
from api import api_call
import pandas as pd
import plotly.express as px


def ai_chatbot_page():
    st.subheader("🤖 AI CRM Assistant")
    st.caption("Ask questions about tickets, customers, and support operations")
    user_id = st.session_state["user_id"]   # adjust if different
    token = st.session_state["token"]

    sessions = api_call(
        "GET",
        "/ai/sessions",
        token
    )
    # ---------- INITIALIZE SESSION SAFELY ----------
    if "session_id" not in st.session_state:

        if sessions and len(sessions) > 0:
            # Load first existing session
            st.session_state["session_id"] = sessions[0]["_id"]
        else:
            # No session exists yet
            st.session_state["session_id"] = None

    if st.sidebar.button("➕ New Chat"):
        if not st.session_state["session_id"]:

            new_session = api_call(
                "POST",
                "/ai/session",
                token,
                {"title": "New Chat"}
            )


            if new_session and "session_id" in new_session:
                st.session_state["session_id"] = new_session["session_id"]
            else:
                st.error("Failed to create session")
                st.stop()

        # new_session = api_call(
        #     "POST",
        #     "/ai/session",
        #     token,
        #     {
        #         "user_id": user_id,
        #         "role": st.session_state["role"]
        #     }
        # )

        # st.session_state["session_id"] = new_session["session_id"]
        st.session_state.ai_chat_history = []
        st.rerun()

    if sessions:

        session_titles = {
            s["title"]: s["_id"] for s in sessions
        }

        selected_title = st.sidebar.selectbox(
            "Your Chats",
            list(session_titles.keys())
        )

        selected_session_id = session_titles[selected_title]
        st.session_state["session_id"] = selected_session_id

    if st.session_state["session_id"] and (
        "loaded_session_id" not in st.session_state or
        st.session_state.loaded_session_id != st.session_state["session_id"]
    ):


        messages = api_call(
            "GET",
            f"/ai/messages/{st.session_state['session_id']}",
            token
        )

        st.session_state.ai_chat_history = messages
        st.session_state.loaded_session_id = st.session_state["session_id"]




    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    # -------- Render history --------
    
    for msg in st.session_state.ai_chat_history:
        with st.chat_message(msg["role"]):

            # -------- ANALYTICS HISTORY --------
            if "analysis" in msg:
                st.markdown(msg["content"])

                data = msg["analysis"]

                chart_df = pd.DataFrame({
                    "Status": ["Open", "In Progress", "Closed"],
                    "Count": [
                        data["Opened_ticket_count"],
                        data["in_progress_ticket_count"],
                        data["Closed_ticket_count"]
                    ]
                })

                fig = px.pie(chart_df, names="Status", values="Count", hole=0.55)
                st.plotly_chart(fig, width="stretch")

            # -------- TABLE HISTORY --------
            elif "data" in msg:
                st.markdown(msg["content"])
                st.dataframe(pd.DataFrame(msg["data"]), width="stretch", hide_index=True)

            else:
                st.markdown(msg["content"])

    # -------- Chat input --------
    user_prompt = st.chat_input("Ask something...")

    if user_prompt:
        payload = {
                "session_id": st.session_state["session_id"],
                "user_id": user_id,
                "role": "user",
                "content": user_prompt
            }
        print("--------------------------",payload)
        api_call(
            "POST",
            "/ai/message",
            token,
            {
                "session_id": st.session_state["session_id"],
                "user_id": user_id,
                "role": "user",
                "content": user_prompt
            }
        )
        st.session_state.ai_chat_history.append({
            "role": "user",
            "content": user_prompt
        })

        with st.chat_message("user"):
            st.markdown(user_prompt)

        # with st.chat_message("assistant"):
        #     with st.spinner("Thinking..."):
        #         ai_response = api_call(
        #             "POST",
        #             "/ai/chat",
        #             st.session_state["token"],
        #             {"prompt": user_prompt}
        #         )

        #     if ai_response is None:
        #         st.error("Backend returned no response")
        #         return

        #     message = ai_response.get("message", "")
        #     data = ai_response.get("data")
        #     print("_______________-------------------",ai_response)
        #     print("_______________-------------------",data)

        #     # -------- ANALYTICS RESPONSE --------
        #     if "analytics" in message:
        #         print("1",data)
        #         # if backend sends list -> take first item
        #         if isinstance(data, list):
        #             data = data[0]
        #         print("2",data)

        #         st.markdown(message)

        #         chart_df = pd.DataFrame({
        #             "Status": ["Open", "In Progress", "Closed"],
        #             "Count": [
        #                 data["Opened_ticket_count"],
        #                 data["in_progress_ticket_count"],
        #                 data["Closed_ticket_count"]
        #             ]
        #         })

        #         fig = px.pie(chart_df, names="Status", values="Count", hole=0.55)
        #         st.plotly_chart(fig, use_container_width=True)

        #         st.session_state.ai_chat_history.append({
        #             "role": "assistant",
        #             "content": message,
        #             "analysis": data
        #         })


        #     # -------- TABLE RESPONSE --------
        #     elif isinstance(data, list):
        #         st.markdown(message)
        #         st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

        #         st.session_state.ai_chat_history.append({
        #             "role": "assistant",
        #             "content": message,
        #             "data": data
        #         })

        #     # -------- TEXT RESPONSE --------
        #     else:
        #         st.markdown(message)

        #         st.session_state.ai_chat_history.append({
        #             "role": "assistant",
        #             "content": message
        #         })

        with st.spinner("Thinking..."):
            ai_response = api_call(
                "POST",
                "/ai/chat",
                token,
                {"prompt": user_prompt}
            )

        if ai_response is None:
            st.error("Backend returned no response")
            return

        message = ai_response.get("message", "")
        data = ai_response.get("data")

        # -------- ANALYTICS RESPONSE --------
        if "analytics" in message:
            if st.session_state["session_id"]:

                api_call(
                    "POST",
                    "/ai/message",
                    token,
                    {
                        "session_id": st.session_state["session_id"],
                        "user_id": user_id,
                        "role": "assistant",
                        "content": message,
                        "analysis": data
                    }
                )
                if isinstance(data, list):
                    data = data[0]

                st.session_state.ai_chat_history.append({
                    "role": "assistant",
                    "content": message,
                    "analysis": data
                })

        # -------- TABLE RESPONSE --------
        elif isinstance(data, list):
            if st.session_state["session_id"]:
                api_call(
                    "POST",
                    "/ai/message",
                    token,
                    {
                        "session_id": st.session_state["session_id"],
                        "user_id": user_id,
                        "role": "assistant",
                        "content": message,
                        "data": data
                    }
                )
                st.session_state.ai_chat_history.append({
                    "role": "assistant",
                    "content": message,
                    "data": data
                })

        # -------- TEXT RESPONSE --------
        else:
            if st.session_state["session_id"]:
                api_call(
                    "POST",
                    "/ai/message",
                    token,
                    {
                        "session_id": st.session_state["session_id"],
                        "user_id": user_id,
                        "role": "assistant",
                        "content": message
                    }
                )
                st.session_state.ai_chat_history.append({
                    "role": "assistant",
                    "content": message
                })

        st.rerun()
