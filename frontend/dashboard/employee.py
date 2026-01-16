import streamlit as st
from api import api_call

# def employee_dashboard(user):
#     st.title("👨‍💼 Employee Dashboard")

#     role = user["role"]

#     st.info(f"Logged in as: **{role}**")

#     col1, col2, col3 = st.columns(3)

#     if role in ["Admin", "Agent"]:
#         with col1:
#             tickets = api_call("GET", "/all_tickets", st.session_state["token"])
#             st.metric("Total Tickets", len(tickets or []))


#     if role == "Service Person":
#         with col2:
#             st.metric(
#                 "Assigned Tickets",
#                 len(api_call("GET", "/my_tickets", st.session_state["token"]) or [])
#             )

#     with col3:
#         st.metric(
#             "Closed Tickets",
#             len(api_call("GET", "/closed_tickets", st.session_state["token"]) or [])
#         )

#     st.divider()

#     if role == "Service Person":
#         st.subheader("My Assigned Tickets")
#         data = api_call("GET", "/my_tickets", st.session_state["token"])
#         st.dataframe(data)

def employee_dashboard(user):
    st.title("👨‍💼 Employee Dashboard")
    emp_id = user["emp_id"]
    role = user["role"]
    st.info(f"Logged in as: **{emp_id}**")

    col1, col2 = st.columns(2)

    all_tickets = []
    my_tickets = []

    if role in ["Admin", "Agent"]:
        all_tickets = api_call(
            "GET",
            "/all_tickets",
            st.session_state["token"]
        ) or []

        with col1:
            st.metric("Total Tickets", len(all_tickets))

    else:
        my_tickets = api_call(
            "GET",
            "/my_tickets",
            st.session_state["token"]
        ) or []

        with col1:
            st.metric("Assigned Tickets", len(my_tickets))

    closed = [
        t for t in (all_tickets or my_tickets)
        if t["ticket_status"] == "Close"
    ]

    with col2:
        st.metric("Closed Tickets", len(closed))

    st.divider()

    if role == "Service Person":
        st.subheader("My Assigned Tickets")
        st.dataframe(my_tickets)

