# import streamlit as st
# from auth import login, logout, customer_login
# from employee import employee_add, service_person_tickets, employee_view, employee_update
# from customer import customer_view, customer_add, customer_update
# from dashboard.employee import employee_dashboard
# from dashboard.customer import customer_dashboard
# from ticket import ticket_update, ticket_view, ticket_create
# import jwt
# st.title("Smart Support Desk")

# def get_role(token):
#     payload = jwt.decode(token, options={"verify_signature": False})
#     return payload["role"]

# def get_user(token):
#     return jwt.decode(token, options={"verify_signature": False})

# st.set_page_config(page_title="Smart Support Desk", layout="wide")

# if "token" not in st.session_state:
#     st.header("Login")
#     # login_type = st.radio("Login As", ["Employee", "Customer"])

#     # if login_type == "Employee":
#     #     login()
#     # else:
#     #     customer_login()

#     tab1, tab2  = st.tabs(["Employee", "Customer"])

#     with tab1:
#         login()

#     with tab2:
#         customer_login()
# else:
#     user = get_user(st.session_state["token"])
#     role = get_role(st.session_state["token"])

#     st.sidebar.title("Menu")

#     if role == "Admin":
#         menu = st.sidebar.radio(
#         "Main",["Dashboard","Employees", "Customers", "Tickets", "Logout"])

#     elif role == "Agent":
#         menu = st.sidebar.radio(
#         "Main",["Dashboard","Customers", "Tickets", "Logout"])

#     elif role == "Service Person":
#         menu = st.sidebar.radio(
#         "Main",["Dashboard","Tickets", "Logout"])
    
#     else:
#         menu = st.sidebar.radio("Menu", ["My Tickets", "Create Ticket", "Logout"])

#         if menu == "My Tickets":
#             ticket_view()
#         elif menu == "Create Ticket":
#             ticket_create() 
#         elif menu == "Logout":
#             logout()


#     sub_menu = None

#     if menu == "Employees":
#         sub_menu = st.sidebar.radio("Employees", ["View", "Add", "Update"])

#     elif menu == "Customers" and role in ["Admin", "Agent"]:
#         sub_menu = st.sidebar.radio("Customers", ["View", "Add", "Update"])

#     elif menu == "Tickets":
#         if role in ["Admin", "Agent"]:
#             sub_menu = st.sidebar.radio("Tickets", ["View", "Create"])
#         elif role == "Service Person":
#             sub_menu = st.sidebar.radio("Tickets", ["Assigned", "Update"])


#     if menu == "Dashboard":
#         if role == "Customer":
#             customer_dashboard(user)
#         else:
#             employee_dashboard(user)
#     elif menu == "Employees":
#         if sub_menu == "View":
#             employee_view()
#         elif sub_menu == "Add":
#             employee_add(role)
#         elif sub_menu == "Update":
#             employee_update()

#     elif menu == "Customers":
#         if sub_menu == "View":
#             customer_view()
#         elif sub_menu == "Add":
#             customer_add()
#         elif sub_menu == "Update":
#             customer_update()
        

#     elif menu == "Tickets":
#         if sub_menu == "Assigned":
#             service_person_tickets()
#         elif sub_menu == "Update":
#             ticket_update()
#         elif sub_menu == "View":
#             ticket_view()
#         elif sub_menu == "Create":
#             ticket_create()
    
#     elif menu == "Logout":
#         logout()

import streamlit as st
import jwt

from auth import login, logout, customer_login
from employee import employee_add, service_person_tickets, employee_view, employee_update
from customer import customer_view, customer_add, customer_update
from dashboard.employee import employee_dashboard
from dashboard.customer import customer_dashboard
from ticket import ticket_update, ticket_view, ticket_create, customer_ticket_view
from employee import employee_chat_dashboard   # 👈 ADD THIS IMPORT


# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Smart Support Desk",
    page_icon="🎫",
    layout="wide"
)

st.title("🎫 Smart Support Desk")


# ---------------- HELPERS ----------------
def get_user(token):
    return jwt.decode(token, options={"verify_signature": False})


def get_role(token):
    return get_user(token)["role"]


# ---------------- AUTH ----------------
if "token" not in st.session_state:

    st.markdown("### 🔐 Login")
    tab1, tab2 = st.tabs(["👨‍💼 Employee Login", "👤 Customer Login"])

    with tab1:
        login()

    with tab2:
        customer_login()
    # st.stop()

else:
    # ---------------- USER ----------------
    user = get_user(st.session_state["token"])
    role = get_role(st.session_state["token"])

    # ---------------- SIDEBAR ----------------
    st.sidebar.title("📌 Navigation")
    st.sidebar.markdown(f"**Role:** `{role}`")

    MENU = {
        "Admin": [
            ("📊 Dashboard", "dashboard"),
            ("👨‍💼 Employees", "employees"),
            ("👥 Customers", "customers"),
            ("🎫 Tickets", "tickets"),
            ("🚪 Logout", "logout"),
        ],
        "Agent": [
            ("📊 Dashboard", "dashboard"),
            ("👥 Customers", "customers"),
            ("🎫 Tickets", "tickets"),
            ("🚪 Logout", "logout"),
        ],
        "Service Person": [
            ("📊 Dashboard", "dashboard"),
            ("🎫 Tickets", "tickets"),
            ("🚪 Logout", "logout"),
        ],
        "Customer": [
            ("📊 Dashboard", "dashboard"),
            ("🎫 My Tickets", "my_tickets"),
            ("🚪 Logout", "logout"),
        ],
    }

    menu_labels = [item[0] for item in MENU[role]]
    menu_keys = [item[1] for item in MENU[role]]

    if "menu" not in st.session_state:
        st.session_state.menu = menu_labels[0]

    selected = st.sidebar.radio(
        "Menu",
        menu_labels,
        index=menu_labels.index(st.session_state.menu)
    )

    st.session_state.menu = selected
    menu = dict(zip(menu_labels, menu_keys))[selected]
    # ---------------- ROUTING ----------------
    if menu == "dashboard":
        if role == "Customer":
            print(1)
            customer_dashboard(user)
        else:
            employee_dashboard(user)


    elif menu == "employees":
        tab = st.tabs(["👁 View", "➕ Add", "✏ Update"])
        with tab[0]:
            employee_view()
        with tab[1]:
            employee_add(role)
        with tab[2]:
            employee_update()


    elif menu == "customers":
        tab = st.tabs(["👁 View", "➕ Add", "✏ Update"])
        with tab[0]:
            customer_view()
        with tab[1]:
            customer_add()
        with tab[2]:
            customer_update()



    elif menu == "tickets":
        if role in ["Admin", "Agent"]:
            tab = st.tabs(["👁 View", "💬 Conversations", "➕ Create"])

            with tab[0]:
                ticket_view()

            with tab[1]:
                employee_chat_dashboard()   # 👈 THIS IS THE CONNECTION

            with tab[2]:
                ticket_create()


        elif role == "Service Person":
            tab = st.tabs(["📋 Assigned", "✏ Update"])
            with tab[0]:
                service_person_tickets()
            with tab[1]:
                ticket_update()


    elif menu == "my_tickets":
        if role == "Customer":
            customer_ticket_view()
        else:
            ticket_view()


    elif menu == "create_ticket":
        ticket_create()


    elif menu == "logout":
        logout()
