# import streamlit as st
# from api import api_call

# def customer_dashboard(user):
#     st.title("👤 Customer Dashboard")

#     st.info("Logged in as: **Customer**")

#     col1, col2 = st.columns(2)

#     tickets = api_call("GET", "/my_tickets", st.session_state["token"]) or []

#     with col1:
#         st.metric("Open Tickets", len([t for t in tickets if t["status"] == "Open"]))

#     with col2:
#         st.metric("Closed Tickets", len([t for t in tickets if t["status"] == "Closed"]))

#     st.divider()

#     st.subheader("My Tickets")
#     st.dataframe(tickets)
import streamlit as st
from api import api_call
import pandas as pd
from ui import apply_global_style

def customer_dashboard(user):
    apply_global_style()

    st.title("👤 Customer Dashboard")
    st.caption(f"Welcome back, **{user.get('email','Customer')}**")

    tickets = api_call("GET", "/my_tickets", st.session_state["token"]) or []

    open_tickets = [t for t in tickets if t["ticket_status"] == "Open"]
    closed_tickets = [t for t in tickets if t["ticket_status"] == "Close"]

    col1, col2, col3 = st.columns(3)
    col1.metric("🎫 Total Tickets", len(tickets))
    col2.metric("🟢 Open", len(open_tickets))
    col3.metric("✅ Closed", len(closed_tickets))

    st.divider()

    st.subheader("📋 My Tickets")

    if tickets:
        df = pd.DataFrame(tickets)
        st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            disabled=True
        )
    else:
        st.info("No tickets created yet")
