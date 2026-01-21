import streamlit as st
from api import api_call
from datetime import datetime
import pandas as pd
from ui import apply_global_style
@st.cache_data(ttl=30)
def get_all_tickets(token):
    return api_call("GET", "/all_tickets", token)
def get_customer_tickets(token):
    return api_call("GET", "/customer_my_tickets", token)
def ticket_view():
    apply_global_style()
    st.header("Ticket Management")

    data = get_all_tickets(st.session_state["token"])
    if data:
        df = pd.DataFrame(data)[
            ["ticket_id", "customer_id", "service_person_emp_id", "issue_title","issue_type", "priority", "ticket_status"]
        ]

        df = df.rename(columns={
            "ticket_id": "Ticket ID",
            "issue_title": "Title",
            "priority": "Priority",
            "ticket_status": "Status",
            "service_person_emp_id" : "Service person ID",
            "customer_id" : "Customer ID",
            "issue_type":"Issue Type"
        })

        st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ticket ID": st.column_config.NumberColumn(width="small"),
                "Title": st.column_config.TextColumn(width="large"),
                "Issue Type": st.column_config.TextColumn(width="medium"),
                "Priority": st.column_config.TextColumn(width="small"),
                "Status": st.column_config.TextColumn(width="small"),
                "Service person ID": st.column_config.NumberColumn(width="small"),
                "Customer ID": st.column_config.NumberColumn(width="small"),
            },
            disabled=True
        )
def customer_ticket_view():
    apply_global_style()
    st.header("Ticket Management")

    data = get_customer_tickets(st.session_state["token"])
    if data:
        df = pd.DataFrame(data)[
            ["ticket_id", "customer_id", "service_person_emp_id", "issue_title","issue_type", "priority", "ticket_status"]
        ]

        df = df.rename(columns={
            "ticket_id": "Ticket ID",
            "issue_title": "Title",
            "priority": "Priority",
            "ticket_status": "Status",
            "service_person_emp_id" : "Service person ID",
            "customer_id" : "Customer ID",
            "issue_type":"Issue Type"
        })

        st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ticket ID": st.column_config.NumberColumn(width="small"),
                "Title": st.column_config.TextColumn(width="large"),
                "Issue Type": st.column_config.TextColumn(width="medium"),
                "Priority": st.column_config.TextColumn(width="small"),
                "Status": st.column_config.TextColumn(width="small"),
                "Service person ID": st.column_config.NumberColumn(width="small"),
                "Customer ID": st.column_config.NumberColumn(width="small"),
            },
            disabled=True
        )




def ticket_create():
    apply_global_style()
    st.header("Create Ticket")
    customer_email = st.text_input("Customer Email")
    title = st.text_input("Issue Title")
    issue_type = st.text_input("Issue Type")
    desc = st.text_area("Description")
    priority = st.selectbox("Priority", ["Low", "Medium", "High"])

    if st.button("Create Ticket"):
        api_call(
            "POST",
            "/ticket_registration",
            st.session_state["token"],
            {
                "customer_email": customer_email,
                "issue_title": title,
                "issue_type": issue_type,
                "issue_description": desc,
                "priority": priority,
                "generate_datetime": datetime.utcnow().isoformat()
            }
        )




def ticket_update():
    apply_global_style()
    st.header("🛠 Update Assigned Ticket")

    # 1️⃣ Fetch assigned tickets
    tickets = api_call(
        "GET",
        "/my_tickets",
        st.session_state["token"]
    ) or []

    if not tickets:
        st.warning("No tickets assigned")
        return

    # 2️⃣ Ticket ID dropdown
    ticket_map = {t["ticket_id"]: t for t in tickets}

    selected_ticket_id = st.selectbox(
        "Select Ticket ID",
        list(ticket_map.keys())
    )

    selected_ticket = ticket_map[selected_ticket_id]


    title = st.text_input(
        "Issue Title",
        selected_ticket["issue_title"]
    )

    issue_type = st.text_input(
        "Issue Type",
        selected_ticket["issue_type"]
    )

    desc = st.text_area(
        "Description",
        selected_ticket["issue_description"]
    )

    priority = st.selectbox(
        "Priority",
        ["Low", "Medium", "High"],
        index=["Low", "Medium", "High"].index(selected_ticket["priority"])
    )

    ticket_status = st.selectbox(
        "Status",
        ["Open", "In_Progress", "Close"],
        index=["Open", "In_Progress", "Close"].index(selected_ticket["ticket_status"])
    )

    # 4️⃣ Update button
    if st.button("✅ Update Ticket"):
        api_call(
            "PUT",
            "/update_ticket",
            st.session_state["token"],
            {
                "ticket_id": selected_ticket_id,
                "issue_title": title,
                "issue_type": issue_type,
                "issue_description": desc,
                "priority": priority,
                "ticket_status": ticket_status,
                "generate_datetime": datetime.utcnow().isoformat()
            }
        )
        st.success("Ticket updated successfully 🎉")

def agent_ticket_list():
    st.subheader("🎫 Assigned Tickets")

    tickets = api_call(
        "GET",
        "/agent_tickets",
        st.session_state["token"]
    ) or []

    if not tickets:
        st.info("No tickets")
        return

    df = pd.DataFrame(tickets)

    # visual indicator
    df["🔔 New Msg"] = df["needs_reply"].apply(
        lambda x: "🔴 New" if x else ""
    )

    st.data_editor(
        df[
            [
                "🔔 New Msg",
                "ticket_id",
                "issue_title",
                "priority",
                "ticket_status",
            ]
        ],
        hide_index=True,
        disabled=True,
        use_container_width=True
    )

    return df
