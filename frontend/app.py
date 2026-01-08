import streamlit as st
import requests
import pymysql

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="root",
        database="smart_support_desk",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )
st.set_page_config(page_title="Login")

conn = get_connection()
cursor = conn.cursor()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
st.title("Login")
email = st.text_input("email")
password = st.text_input("Password", type="password")
st.set_page_config(
    page_title="Login",
    # initial_sidebar_state="collapsed"
    
)
if st.button("Login"):
        res = requests.post(
            "http://127.0.0.1:8000/login_admin",
            json={"email": email, "password": password}
        )

if res.status_code == 200:
    st.session_state.logged_in = True
    st.session_state.user_email = email
    st.experimental_rerun()


        
        # if st.session_state.logged_in:

        #     st.sidebar.title("Smart Support Desk")

        #     page = st.sidebar.radio(
        #         "Navigation",
        #         ["Home", "Tickets", "Profile"]
        #     )

        #     if page == "Home":
        #         st.title("Home")
        #         st.write("Welcome,", st.session_state.user_email)

        #     elif page == "Tickets":
        #         st.title("Tickets")

        #     elif page == "Profile":
        #         st.title("Profile")

        #     if st.sidebar.button("Logout"):
        #         st.session_state.logged_in = False
        #         st.experimental_rerun()

else:
    st.error("Invalid credentials")
