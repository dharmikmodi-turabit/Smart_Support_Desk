import streamlit as st
from api import api_call

def customer_view():
    st.header("Customer Management")

    if st.button("Fetch Customers"):
        data = api_call("GET", "/all_customers", st.session_state["token"])
        if data:
            st.dataframe(data)


def customer_add():
    st.header("Customer Registation")
    with st.form("customer_registration_form",clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name")
            mobile = st.text_input("Mobile")
        with col2:
            company_name = st.text_input("Company")
            email = st.text_input("Email")
        col1, col2, col3 = st.columns(3)
        with col1:
            city = st.text_input("City")
        with col2:
            state = st.text_input("State")
        with col3:
            country = st.text_input("Country")
        address = st.text_area("Address")

        submitted = st.form_submit_button("Register")
        if submitted:
            if not email or not mobile:
                st.warning("Email or mobile is required")
            else:
                api_call(
                    "Post",
                    "/customer_registration",
                    st.session_state["token"],
                    {
                        "name": name,
                        "email": email,
                        "mobile_number": mobile,
                        "company_name": company_name,
                        "city": city,
                        "state": state,
                        "country": country,
                        "address": address  
                    }
                )
                st.success("Customer registered succefully!!")

def customer_update():
    st.subheader("Update Customer")

    if st.button("Fetch Customers"):
        data = api_call("GET", "/all_customers", st.session_state["token"])
        if data:
            st.dataframe(data)
    with st.form("customer_update_form",clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name")
            mobile = st.text_input("Mobile")
        with col2:
            company_name = st.text_input("Company")
            email = st.text_input("Email")
        col1, col2, col3 = st.columns(3)
        with col1:
            city = st.text_input("City")
        with col2:
            state = st.text_input("State")
        with col3:
            country = st.text_input("Country")
        address = st.text_area("Address")

        submitted = st.form_submit_button("Update")
        if submitted:
            if not email or mobile:
                st.warning("Email or Mobile is required")
            else:
                api_call(
                    "PUT",
                    "/update_customer",
                    st.session_state["token"],
                    {
                        "name": name,
                        "email": email,
                        "mobile_number": mobile,
                        "company_name": company_name,
                        "city": city,
                        "state": state,
                        "country": country,
                        "address": address  
                    }
                )
                st.success("Customer updated succefully!!")