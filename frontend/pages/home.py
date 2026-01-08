import streamlit as st

st.title("Home Page")

st.write("Welcome to Smart Support Desk")

if st.button("View Tickets"):
    st.switch_page("pages/2_Tickets.py")

# page = st.sidebar.radio(
#     "Navigation",
#     ["Home", "Profile"]
# )

# if page == "Home":
#     st.switch_page("pages/home.py")
# elif page == "Profile":
#     st.switch_page("pages/profile.py")
