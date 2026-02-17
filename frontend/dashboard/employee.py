import streamlit as st
from api import api_call
import pandas as pd
import plotly.express as px

def employee_dashboard(user):
    """
    Render the employee dashboard UI for Admins and Agents.

    This dashboard provides operational visibility into the ticketing system
    and adapts its behavior based on the logged-in employee's role.

    Core capabilities:
    - Fetch and display tickets based on role:
        • Admin / Agent → all tickets
        • Service Person → only assigned tickets
    - Display KPI metrics for ticket status (Total, Open, In Progress, Closed)
    - Visualize ticket data using interactive Plotly charts:
        • Status distribution (donut chart)
        • Ticket status by priority (stacked bar)
        • Service person workload (Admins / Agents only)
    - Present a table of active tickets for quick operational review

    The dashboard communicates with the backend via authenticated API calls
    and renders a responsive analytics-oriented UI using Streamlit and Plotly.

    Args:
        user (dict):
            Authenticated employee payload (JWT-decoded data).
            Expected keys:
                - emp_id (str | int): Employee identifier
                - role (str): One of ["Admin", "Agent", "Service"]

    Side Effects:
        - Performs authenticated API calls to fetch ticket data
        - Renders Streamlit widgets and Plotly visualizations
        - Conditionally displays sections based on user role

    Returns:
        None
    """

    st.title("👨‍💼 Employee Dashboard")

    emp_id = user["emp_id"]
    role = user["role"]


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
    # 🔥 Clean hover
    fig_status.update_traces(
        hovertemplate="%{label}"
    )

    fig_priority = px.bar(
        df,
        x="ticket_status",
        color="priority",
        barmode="stack",
        title="🔥 Ticket Status by Priority",
        labels={
            "ticket_status": "Ticket Status",
            "priority": "Priority"
        }
    )

    col1.plotly_chart(fig_status, use_container_width=True, config={"displayModeBar": False})
    col2.plotly_chart(fig_priority, use_container_width=True, config={"displayModeBar": False})

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


