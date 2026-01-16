import streamlit as st
from api import api_call

def customer_dashboard(user):
    st.title("👤 Customer Dashboard")

    st.info("Logged in as: **Customer**")

    col1, col2 = st.columns(2)

    tickets = api_call("GET", "/my_tickets", st.session_state["token"]) or []

    with col1:
        st.metric("Open Tickets", len([t for t in tickets if t["status"] == "Open"]))

    with col2:
        st.metric("Closed Tickets", len([t for t in tickets if t["status"] == "Closed"]))

    st.divider()

    st.subheader("My Tickets")
    st.dataframe(tickets)
