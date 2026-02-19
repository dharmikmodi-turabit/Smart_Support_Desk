import streamlit as st
from utils.api import api_call
import pandas as pd
import plotly.express as px


def ai_chatbot_page():
    """
    Render and manage the AI CRM Assistant chat interface in Streamlit.

    This function provides a complete frontend workflow for:
        - Session management
        - Message persistence
        - AI interaction
        - Dynamic rendering of text, tabular, and analytical responses

    Core Responsibilities:
        1. Fetch existing chat sessions for the authenticated user.
        2. Allow creation of new chat sessions.
        3. Load and render historical messages per session.
        4. Persist user and assistant messages to backend.
        5. Invoke the AI backend (/ai/chat) for CRM automation.
        6. Render structured responses (analytics, tables, plain text).
        7. Maintain state synchronization using Streamlit session_state.

    Session Workflow:
        - Sessions are fetched via GET /ai/sessions.
        - New sessions are created via POST /ai/session.
        - Messages are loaded via GET /ai/messages/{session_id}.
        - Session switching triggers history reload.
        - State variables used:
            • session_id
            • ai_chat_history
            • loaded_session_id
            • user_id
            • token

    Message Persistence:
        - User messages saved via POST /ai/message.
        - Assistant responses saved after backend processing.
        - Messages include:
            • role ("user" | "assistant")
            • content (text)
            • optional analysis (analytics data)
            • optional data (table results)

    Response Rendering Modes:
        1. Analytics Response:
            - Displays summary message.
            - Renders donut pie chart using Plotly.
            - Uses ticket status counts:
                • Open
                • In Progress
                • Closed

        2. Table Response:
            - Displays summary message.
            - Renders structured data using st.dataframe.

        3. Text Response:
            - Displays plain markdown message.

    State Management:
        - Ensures session exists before saving messages.
        - Prevents duplicate history loading.
        - Uses st.rerun() for consistent UI refresh after updates.
        - Handles empty or failed backend responses gracefully.

    Backend Endpoints Used:
        - GET  /ai/sessions
        - POST /ai/session
        - GET  /ai/messages/{session_id}
        - POST /ai/message
        - POST /ai/chat

    Error Handling:
        - Displays Streamlit error messages on API failures.
        - Stops execution if session creation fails.
        - Handles None responses from backend safely.

    Security:
        - JWT token retrieved from st.session_state.
        - All API calls include authenticated token.
        - Session ownership enforced server-side.

    Notes:
        - Designed for deterministic CRM automation workflows.
        - Fully state-driven UI behavior.
        - Optimized for multi-session conversational CRM control.
    """

    st.subheader("🤖 AI CRM Assistant")
    st.caption("Ask questions about tickets, customers, and support operations")
    user_id = st.session_state["user_id"]   # adjust if different
    token = st.session_state["token"]

    # -------- Fetch Sessions FIRST --------
    sessions = api_call(
        "GET",
        "/ai/sessions",
        token
    )
    

    if sessions is None:
        sessions = []

    # -------- Initialize session_id safely --------
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = None

    if st.sidebar.button("➕ New Chat", use_container_width=True):

        new_session = api_call("POST", "/ai/session", token, {})

        if not new_session or "session_id" not in new_session:
            st.error("Failed to create session")
            st.stop()

        st.session_state["session_id"] = new_session["session_id"]
        st.session_state["ai_chat_history"] = []
        st.session_state["loaded_session_id"] = None

        st.rerun()

    st.sidebar.markdown("### Your Chats")
    sessions = sorted(
        sessions,
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )

    if sessions:
        for s in sessions:

            is_active = (
                s["_id"] == st.session_state.get("session_id")
            )

            button_label = f"🟢 {s['title']}" if is_active else s["title"]

            if st.sidebar.button(
                button_label,
                key=f"session_{s['_id']}",
                use_container_width=True
            ):
                st.session_state["session_id"] = s["_id"]
                st.session_state["loaded_session_id"] = None
                st.rerun()

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

        st.rerun()


    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    # -------- Render history --------

    for i, msg in enumerate(st.session_state.ai_chat_history):
        with st.chat_message(msg["role"]):

            analysis_data = msg.get("analysis")
            table_data = msg.get("data")

            # -------- ANALYTICS HISTORY --------
            if analysis_data:
                st.markdown(msg.get("content", ""))

                chart_df = pd.DataFrame({
                    "Status": ["Open", "In Progress", "Closed"],
                    "Count": [
                        analysis_data.get("Opened_ticket_count", 0),
                        analysis_data.get("in_progress_ticket_count", 0),
                        analysis_data.get("Closed_ticket_count", 0)
                    ]
                })

                fig = px.pie(chart_df, names="Status", values="Count", hole=0.55)
                st.plotly_chart(fig, width="stretch",key=f"history_chart_{st.session_state['session_id']}_{i}")

            # -------- TABLE HISTORY --------
            elif table_data:
                st.markdown(msg.get("content", ""))
                st.dataframe(
                    pd.DataFrame(table_data),
                    width="stretch",
                    hide_index=True
                )

            # -------- NORMAL TEXT HISTORY --------
            else:
                st.markdown(msg.get("content", ""))

    # -------- Chat input --------
    user_prompt = st.chat_input("Ask something...")

    if user_prompt:
        # ✅ Ensure session exists BEFORE saving message
        if not st.session_state.get("session_id"):
            new_session = api_call(
                "POST",
                "/ai/session",
                token,
                {"title": "New Chat"}
            )

            if not new_session or "session_id" not in new_session:
                st.error("Failed to create session")
                st.stop()

            st.session_state["session_id"] = new_session["session_id"]

        # Now session_id is guaranteed valid
        session_id = st.session_state["session_id"]

        # Save user message
        api_call(
            "POST",
            "/ai/message",
            token,
            {
                "session_id": session_id,
                "user_id": user_id,
                "role": "user",
                "content": user_prompt
            }
        )

        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
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
                if isinstance(data, dict) and data.get("Opened_ticket_count"):
                    chart_df = pd.DataFrame({
                        "Status": ["Open", "In Progress", "Closed"],
                        "Count": [
                            data.get("Opened_ticket_count", 0),
                            data.get("in_progress_ticket_count", 0),
                            data.get("Closed_ticket_count", 0)
                        ]
                    })

                    st.markdown(message)
                    fig = px.pie(chart_df, names="Status", values="Count", hole=0.55)
                    st.plotly_chart(fig, width="stretch",key=f"ticket_analysis_{st.session_state['session_id']}")

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
                    messages = api_call(
                        "GET",
                        f"/ai/messages/{st.session_state['session_id']}",
                        token
                    )

                    st.session_state.ai_chat_history = messages
                    st.session_state.loaded_session_id = st.session_state["session_id"]

                    # st.rerun()

                # -------- TABLE RESPONSE --------
                elif isinstance(data, list):
                    st.markdown(message)
                    st.dataframe(pd.DataFrame(data), width="stretch", hide_index=True)

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
                    messages = api_call(
                        "GET",
                        f"/ai/messages/{st.session_state['session_id']}",
                        token
                    )

                    st.session_state.ai_chat_history = messages
                    st.session_state.loaded_session_id = st.session_state["session_id"]

                    # st.rerun()

                # -------- TEXT RESPONSE --------
                else:
                    st.markdown(message)

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
                    messages = api_call(
                        "GET",
                        f"/ai/messages/{st.session_state['session_id']}",
                        token
                    )

                    st.session_state.ai_chat_history = messages
                    st.session_state.loaded_session_id = st.session_state["session_id"]

                st.rerun()
