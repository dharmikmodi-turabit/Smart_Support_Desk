import streamlit as st
from api import api_call

def login():
    st.subheader("Employee Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login", key="employee_login"):
        res = api_call(
            "POST",
            "/employee_login",
            json={"email": email, "password": password}
        )
        print("---------------------------------------")
        print(res)
        print("---------------------------------------")

        if res:
            st.session_state["token"] = res["access_token"]
            st.session_state["user_id"] = res["emp_id"]
            st.session_state["role"] = res["role"]
            st.success("Login successful")
            st.rerun()
def customer_login():
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
    api_call("POST", "/logout", st.session_state["token"])
    st.session_state.clear()
    st.success("Logged out")
    st.rerun()
