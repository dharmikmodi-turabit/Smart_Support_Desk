import streamlit as st
from utils.api import api_call

def login():
    """
    Render the employee login form and authenticate the user.

    This function displays a login UI for employees, collects email and
    password credentials, and submits them to the backend authentication
    endpoint. On successful authentication, the returned JWT access token
    is stored in the Streamlit session state and the application is rerun
    to load the authenticated views.

    UI Elements:
        - Email input field
        - Password input field (masked)
        - Login button

    Side Effects:
        - Calls `/employee_login` API endpoint
        - Stores JWT token in `st.session_state["token"]`
        - Displays success message on successful login
        - Triggers `st.rerun()` to refresh the app state

    Returns:
        None
    """

    st.subheader("Employee Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login", key="employee_login"):
        res = api_call(
            "POST",
            "/employee_login",
            json={"email": email, "password": password}
        )

        if res:
            st.session_state["token"] = res["access_token"]
            st.session_state["user_id"] = res["emp_id"]
            st.session_state["role"] = res["role"]
            st.success("Login successful")
            st.rerun()

def customer_login():
    """
    Render the customer login form and authenticate the customer.

    This function provides a simplified login interface for customers,
    allowing authentication using either email or mobile number.
    Upon successful authentication, the JWT access token is saved in
    the session state and the application reruns to load the customer
    dashboard.

    UI Elements:
        - Email or mobile number input field
        - Login button

    Side Effects:
        - Calls `/customer_login` API endpoint
        - Stores JWT token in `st.session_state["token"]`
        - Displays success message on successful login
        - Triggers `st.rerun()` to refresh the app state

    Returns:
        None
    """

    st.subheader("Customer Login")

    email_or_mobile = st.text_input("Email or Mobile Number")

    if st.button("Login", key="customer_login"):
        res = api_call(
            "POST",
            "/customer_login",
            json={"email_or_mobile": email_or_mobile}
        )
        if res:
            st.session_state["token"] = res["access_token"]
            st.success("Login successful")
            st.rerun()

def logout():
    """
    Log out the currently authenticated user.

    This function invalidates the user session by calling the backend
    logout endpoint, clears all Streamlit session state, and forces
    an application rerun to redirect the user back to the login screen.

    Side Effects:
        - Calls `/logout` API endpoint
        - Clears `st.session_state`
        - Displays logout success message
        - Triggers `st.rerun()` to reset the application

    Returns:
        None
    """

    api_call("POST", "/logout", st.session_state["token"])
    st.session_state.clear()
    st.success("Logged out")
    st.rerun()
