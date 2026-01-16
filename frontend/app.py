import streamlit as st
from auth import login, logout, customer_login
from employee import employee_add, service_person_tickets, employee_view, employee_update
from customer import customer_view, customer_add, customer_update
from dashboard.employee import employee_dashboard
from dashboard.customer import customer_dashboard
from ticket import ticket_update, ticket_view, ticket_create
import jwt

def get_role(token):
    payload = jwt.decode(token, options={"verify_signature": False})
    return payload["role"]

def get_user(token):
    return jwt.decode(token, options={"verify_signature": False})

st.set_page_config(page_title="Smart Support Desk", layout="wide")

if "token" not in st.session_state:
    login_type = st.radio("Login As", ["Employee", "Customer"])

    if login_type == "Employee":
        login()
    else:
        customer_login()

else:
    user = get_user(st.session_state["token"])
    role = get_role(st.session_state["token"])

    # menu = []

    # else:
    #     st.error("Invalid role")
    #     st.stop()
    # page = st.sidebar.selectbox("Menu", menu)

    # # ---------------- RENDER ----------------
    # if page == "Customers":
    #     customer_page()

    # elif page == "Employees":
    #     employee_page()

    # elif page == "Tickets":
    #     ticket_page()

    # elif page == "Logout":
    #     logout()

    st.sidebar.title("Menu")

    if role == "Admin":
        menu = st.sidebar.radio(
        "Main",["Dashboard","Employees", "Customers", "Tickets", "Logout"])

    elif role == "Agent":
        menu = st.sidebar.radio(
        "Main",["Dashboard","Customers", "Tickets", "Logout"])

    elif role == "Service Person":
        menu = st.sidebar.radio(
        "Main",["Dashboard","Tickets", "Logout"])
    
    else:
        menu = st.sidebar.radio("Menu", ["My Tickets", "Create Ticket", "Logout"])

        if menu == "My Tickets":
            ticket_view()
        elif menu == "Create Ticket":
            ticket_create() 
        elif menu == "Logout":
            logout()
    # menu = st.sidebar.radio(
    #     "Main",
    #     ["Dashboard", "Employees", "Customers", "Tickets", "Profile", "Logout"]
    # )

    sub_menu = None

    if menu == "Employees":
        sub_menu = st.sidebar.radio("Employees", ["View", "Add", "Update"])

    elif menu == "Customers" and role in ["Admin", "Agent"]:
        sub_menu = st.sidebar.radio("Customers", ["View", "Add", "Update"])

    elif menu == "Tickets":
        if role in ["Admin", "Agent"]:
            sub_menu = st.sidebar.radio("Tickets", ["View", "Create"])
        elif role == "Service Person":
            sub_menu = st.sidebar.radio("Tickets", ["Assigned", "Update"])


    if menu == "Dashboard":
        if role == "Customer":
            customer_dashboard(user)
        else:
            employee_dashboard(user)
    elif menu == "Employees":
        if sub_menu == "View":
            employee_view()
        elif sub_menu == "Add":
            employee_add(role)
        elif sub_menu == "Update":
            employee_update()

    elif menu == "Customers":
        if sub_menu == "View":
            customer_view()
        elif sub_menu == "Add":
            customer_add()
        elif sub_menu == "Update":
            customer_update()
        

    elif menu == "Tickets":
        if sub_menu == "Assigned":
            service_person_tickets()
        elif sub_menu == "Update":
            ticket_update()
        elif sub_menu == "View":
            ticket_view()
        elif sub_menu == "Create":
            ticket_create()
    
    elif menu == "Logout":
        logout()

