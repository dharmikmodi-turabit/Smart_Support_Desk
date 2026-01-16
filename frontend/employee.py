import streamlit as st
from api import api_call

# def employee_page(role):
#     st.header("Employee Management")

#     if st.button("Fetch Employees"):
#         data = api_call("GET", "/all_employees", st.session_state["token"])
#         if data:
#             st.dataframe(data)

def employee_view():
    st.header("Employee Management")

    if st.button("Fetch Employees"):
        data = api_call("GET", "/all_employees", st.session_state["token"])
        if data:
            st.dataframe(data)

def employee_add(role):
    st.header("Register Employee")
    with st.form("employee_registration_form",clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name")
        with col2:
            roles = ["Admin", "Agent", "Service Person"]
            employee_type = st.selectbox("Employee Type", roles)
        col1, col2, col3 = st.columns(3)
        with col1:
            email = st.text_input("Email")
        with col2:
            mobile = st.text_input("Mobile")
        with col3:
            password = st.text_input("Password", type="password")

        submitted = st.form_submit_button("Register")
        if submitted:
            if not email:
                st.warning("Email is required")
            else:
                api_call(
                    "POST",
                    "/employee_registration",
                    st.session_state["token"],
                    {
                        "name": name,
                        "email": email,
                        "mobile_number": mobile,
                        "password": password,
                        "type": employee_type
                    }
                )
                st.success("Employee registered succefully!!")

def employee_update():
    st.header("Update Employee")

    if st.button("Fetch Employees emails"):
        data = api_call("GET", "/all_employees", st.session_state["token"])
        if data:
            emails = []
            for x in data:
                emails.append(x['employee_email'])
            st.dataframe({'Employee Emails':emails})
    with st.form("employee_update_form",clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name")
        with col2:
            roles = ["Admin", "Agent", "Service Person"]
            employee_type = st.selectbox("Employee Type", roles)
        col1, col2, col3 = st.columns(3)
        with col1:
            email = st.text_input("Email")
        with col2:
            mobile = st.text_input("Mobile")
        with col3:
            password = st.text_input("Password", type="password")

        submitted = st.form_submit_button("Update")

        if submitted:
            if not email:
                st.warning("Email is required")
            else:
                api_call(
                    "PUT",
                    "/employee_update",
                    st.session_state["token"],
                    {
                        "name": name,
                        "email": email,
                        "mobile_number": mobile,
                        "password": password,
                        "type": employee_type
                    }
                )
                st.success("Employee updated succefully!!")

def service_person_tickets():
    st.title("My Assigned Tickets")
    data = api_call("GET", "/my_tickets", st.session_state["token"])
    st.dataframe(data)


