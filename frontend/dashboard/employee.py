# import streamlit as st
# from api import api_call
# import pandas as pd
# import plotly.express as px


# def employee_dashboard(user):   
#     st.title("👨‍💼 Employee Dashboard")
#     emp_id = user["emp_id"]
#     role = user["role"]
#     st.info(f"Logged in as: **{emp_id}**")


#     st.subheader("📊 Ticket Status Distribution")
#     col1, col2 = st.columns([1, 3])

#     all_tickets = []
#     my_tickets = []

#     if role in ["Admin", "Agent"]:
#         all_tickets = api_call(
#             "GET",
#             "/all_tickets",
#             st.session_state["token"]
#         ) or []

#         with col1:
#             st.metric("", "")
#             st.metric("Total Tickets", len(all_tickets))

#     else:
#         my_tickets = api_call(
#             "GET",
#             "/my_tickets",
#             st.session_state["token"]
#         ) or []

#         with col1:
#             st.metric("", "")
#             st.metric("Assigned Tickets", len(my_tickets))

#     # if role == "Service Person":
#     #     st.subheader("My Assigned Tickets")
#     #     st.dataframe(my_tickets)
#     closed = [
#         t for t in (all_tickets or my_tickets)
#         if t["ticket_status"] == "Close"
#     ]
    
#     In_progress = [
#         t for t in (all_tickets or my_tickets)
#         if t["ticket_status"] == "In_Progress"
#     ]

#     with col1:
#         st.metric("In Progress Tickets", len(In_progress))
#         st.metric("Closed Tickets", len(closed))

#     st.divider()



#     with col2:
#         tickets = all_tickets if role in ["Admin", "Agent"] else my_tickets

#         if tickets:
#             df = pd.DataFrame(tickets)

#             # status_count = df["ticket_status"].value_counts()

#             fig = px.pie(
#                 df,
#                 names="ticket_status",
#                 hole=0.5,
#                 title="Ticket Status Breakdown"
#             )

#             st.plotly_chart(fig, use_container_width=True,height=450 )

import streamlit as st
from api import api_call
import pandas as pd
import plotly.express as px


def employee_dashboard(user):
    st.title("👨‍💼 Employee Dashboard")

    emp_id = user["emp_id"]
    role = user["role"]

    st.info(f"Logged in as: **{emp_id}**")

    # =========================
    # Fetch tickets
    # =========================
    if role in ["Admin", "Agent"]:
        tickets = api_call("GET", "/all_tickets", st.session_state["token"]) or []
    else:
        tickets = api_call("GET", "/my_tickets", st.session_state["token"]) or []

    if not tickets:
        st.warning("No tickets found")
        return

    df = pd.DataFrame(tickets)
    df["generate_datetime"] = pd.to_datetime(df["generate_datetime"])

    # =========================
    # KPI CARDS
    # =========================
    total = len(df)
    open_cnt = len(df[df["ticket_status"] == "Open"])
    progress_cnt = len(df[df["ticket_status"] == "In_Progress"])
    close_cnt = len(df[df["ticket_status"] == "Close"])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🎫 Total Tickets", total)
    k2.metric("🟢 Open", open_cnt)
    k3.metric("🟡 In Progress", progress_cnt)
    k4.metric("✅ Closed", close_cnt)

    st.divider()

    # =========================
    # STATUS DONUT + PRIORITY BAR
    # =========================
    col1, col2 = st.columns(2)

    fig_status = px.pie(
        df,
        names="ticket_status",
        hole=0.55,
        title="📊 Ticket Status Distribution",
        color="ticket_status",
        color_discrete_map={
            "Open": "#4f6df5",
            "In_Progress": "#ff4d4d",
            "Close": "#00d084"
        }
    )

    fig_priority = px.bar(
        df,
        x="ticket_status",
        color="priority",
        barmode="stack",
        title="🔥 Ticket Status by Priority"
    )

    col1.plotly_chart(fig_status, use_container_width=True, config={"displayModeBar": False})
    col2.plotly_chart(fig_priority, use_container_width=True, config={"displayModeBar": False})

    st.divider()

    # =========================
    # TICKETS OVER TIME
    # =========================
    daily = (
        df.groupby(df["generate_datetime"].dt.date)
        .size()
        .reset_index(name="Tickets")
    )

    fig_time = px.line(
        daily,
        x="generate_datetime",
        y="Tickets",
        markers=True,
        title="📈 Tickets Created Over Time"
    )

    st.plotly_chart(fig_time, use_container_width=True, config={"displayModeBar": False})

    st.divider()

    # =========================
    # SERVICE PERSON WORKLOAD
    # =========================
    if role in ["Admin", "Agent"]:
        workload = (
            df["service_person_emp_id"]
            .value_counts()
            .reset_index()
        )
        workload.columns = ["Service Person ID", "Assigned Tickets"]

        fig_workload = px.bar(
            workload,
            x="Service Person ID",
            y="Assigned Tickets",
            title="👨‍🔧 Service Person Workload"
        )

        st.plotly_chart(fig_workload, use_container_width=True, config={"displayModeBar": False})

        st.divider()

    # =========================
    # ACTIVE TICKETS TABLE
    # =========================
    st.subheader("📌 Active Tickets")

    display_df = df[
        ["ticket_id", "issue_title", "issue_type", "priority", "ticket_status", "service_person_emp_id"]
    ].rename(columns={
        "ticket_id": "Ticket ID",
        "issue_title": "Title",
        "issue_type": "Issue Type",
        "priority": "Priority",
        "ticket_status": "Status",
        "service_person_emp_id": "Service Person ID"
    })

    st.dataframe(display_df, use_container_width=True, hide_index=True)


