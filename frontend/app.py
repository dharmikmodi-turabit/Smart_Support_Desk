import streamlit as st
import jwt

from auth import login, logout, customer_login
from employee import employee_add, service_person_tickets, employee_view, employee_update
from customer import customer_view, customer_add, customer_update
from dashboard.employee import employee_dashboard
from dashboard.customer import customer_dashboard
from ticket import ticket_update, ticket_view, ticket_create, customer_ticket_view
from employee import employee_chat_dashboard   # 👈 ADD THIS IMPORT
from ai_chat_page import ai_chatbot_page



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
            ("🤖 Chatbot", "chatbot"),
            ("🚪 Logout", "logout"),
        ],
        "Agent": [
            ("📊 Dashboard", "dashboard"),
            ("👥 Customers", "customers"),
            ("🎫 Tickets", "tickets"),
            ("🤖 Chatbot", "chatbot"),
            ("🚪 Logout", "logout"),
        ],
        "Service Person": [
            ("📊 Dashboard", "dashboard"),
            ("🎫 Tickets", "tickets"),
            ("🤖 Chatbot", "chatbot"),
            ("🚪 Logout", "logout"),
        ],
        "Customer": [
            ("📊 Dashboard", "dashboard"),
            ("🤖 Chatbot", "chatbot"),
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
            tab = st.tabs(["👁 View", "💬 Conversations", "➕ Create","✏ Update"])

            with tab[0]:
                ticket_view()

            with tab[1]:
                employee_chat_dashboard()   # 👈 THIS IS THE CONNECTION

            with tab[2]:
                ticket_create()

            with tab[3]:
                ticket_update(role)


        elif role == "Service Person":
            tab = st.tabs(["📋 Assigned", "✏ Update"])
            with tab[0]:
                service_person_tickets()
            with tab[1]:
                ticket_update(role)


    elif menu == "my_tickets":
        if role == "Customer":
            customer_ticket_view()
        else:
            ticket_view()

    elif menu == "chatbot":
        ai_chatbot_page()

    elif menu == "create_ticket":
        ticket_create()


    elif menu == "logout":
        logout()
