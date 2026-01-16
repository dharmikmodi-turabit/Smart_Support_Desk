import streamlit as st
from api import api_call
from datetime import datetime


def ticket_view():
    st.header("Ticket Management")

    if st.button("Fetch Tickets"):
        data = api_call("GET", "/all_tickets", st.session_state["token"])
        if data:
            st.dataframe(data)

def ticket_create():
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
    st.header("Update Ticket")
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