import streamlit as st
import pandas as pd
from api import api_call
from ui import apply_global_style


def customer_dashboard(user):
    apply_global_style()

    st.title("👤 Customer Dashboard")
    # st.caption(f"Welcome back, **Customer #{user.get('emp_id')}**")

    # ---------------- FETCH DATA ----------------
    tickets = api_call(
        "GET",
        "/customer_my_tickets",
        st.session_state["token"]
    ) or []

    if not tickets:
        st.info("🎫 No tickets created yet")
        return

    df = pd.DataFrame(tickets)

    # ---------------- KPIs ----------------
    open_count = len(df[df["ticket_status"] == "Open"])
    in_progress_count = len(df[df["ticket_status"] == "In_Progress"])
    closed_count = len(df[df["ticket_status"] == "Close"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🎫 Total Tickets", len(df))
    c2.metric("🟢 Open Tickets", open_count)
    c3.metric("🟢 In Progress Tickets", in_progress_count)
    c4.metric("✅ Closed Tickets", closed_count)

    st.divider()

    # ---------------- FILTERS ----------------
    st.subheader("🔎 Filter Tickets")

    f1, f2, f3 = st.columns(3)

    with f1:
        status_filter = st.selectbox(
            "Status",
            ["All", "Open", "Close"]
        )

    with f2:
        priority_filter = st.selectbox(
            "Priority",
            ["All"] + sorted(df["priority"].dropna().unique().tolist())
        )

    with f3:
        search = st.text_input("Search (title / description)")

    # ---------------- APPLY FILTERS ----------------
    filtered_df = df.copy()

    if status_filter != "All":
        filtered_df = filtered_df[
            filtered_df["ticket_status"] == status_filter
        ]

    if priority_filter != "All":
        filtered_df = filtered_df[
            filtered_df["priority"] == priority_filter
        ]

    if search:
        filtered_df = filtered_df[
            filtered_df["issue_title"].str.contains(search, case=False, na=False) |
            filtered_df["issue_description"].str.contains(search, case=False, na=False)
        ]

    # ---------------- TABLE ----------------
    st.subheader("📋 My Tickets")

    st.data_editor(
        filtered_df[
            [
                "ticket_id",
                "issue_title",
                "priority",
                "ticket_status",
                "generate_datetime",
            ]
        ],
        hide_index=True,
        disabled=True,
        use_container_width=True,
    )

    # ---------------- DETAILS VIEW ----------------
    st.divider()
    st.subheader("🔍 Ticket Details")

    ticket_ids = filtered_df["ticket_id"].tolist()

    selected_ticket = st.selectbox(
        "Select a ticket to view details",
        ticket_ids
    )

    ticket = df[df["ticket_id"] == selected_ticket].iloc[0]

    st.markdown(f"""
    **🆔 Ticket ID:** {ticket.ticket_id}  
    **📌 Title:** {ticket.issue_title}  
    **🔥 Priority:** {ticket.priority}  
    **📊 Status:** {ticket.ticket_status}  
    **🕒 Created:** {ticket.generate_datetime}  

    **📝 Description:**  
    {ticket.issue_description}
    """)

    ticket_chat_view(selected_ticket)


def ticket_chat_view(ticket_id):

    messages = api_call(
        "GET",
        f"/customer_ticket_messages/{ticket_id}",
        st.session_state["token"]
    ) or []
    if messages:
        st.subheader("💬 Ticket Conversation")
        # ---------------- CHAT HISTORY ----------------
        for msg in messages:
            if msg["sender_role"] == "Customer":
                with st.chat_message("user"):
                    st.write(msg["message"])
            else:
                with st.chat_message("assistant"):
                    st.write(msg["message"])
    else:
        pass

    # ---------------- SEND MESSAGE ----------------
    new_msg = st.chat_input("Type your message...")

    if new_msg:
        api_call(
            "POST",
            f"/customer_ticket_message/{ticket_id}",
            st.session_state["token"],
            json={"message": new_msg}
        )
        st.rerun()
