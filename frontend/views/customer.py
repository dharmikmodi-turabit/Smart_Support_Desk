import streamlit as st
from utils.api import api_call
from utils.ui import apply_global_style

def customer_view():
    """
    Display the customer management view.

    This function renders a table of all registered customers by fetching
    customer data from the backend API. It applies the global UI styling
    and presents the customer list in a read-only tabular format for
    administrative review.

    API Calls:
        - GET /all_customers

    UI Behavior:
        - Applies global UI styles
        - Displays customer data in a Streamlit dataframe

    Access Control:
        - Requires a valid authentication token in session state

    Returns:
        None
    """

    apply_global_style()
    st.header("👨‍💼 Customer Management")

    data = api_call("GET", "/all_customers", st.session_state["token"])
    if data:
        st.dataframe(data)


def customer_add():
    """
    Render the customer registration form and create a new customer.

    This function provides a form-based interface to register a new customer.
    It collects personal, contact, and company details and submits them to
    the backend customer registration endpoint. Existing customers are fetched
    in advance to support validation logic (email/mobile uniqueness).

    API Calls:
        - GET /all_customers
        - POST /customer_registration

    UI Behavior:
        - Applies global UI styles
        - Displays input fields grouped using columns
        - Shows success feedback on successful creation

    Validation Notes:
        - Email and mobile uniqueness checks are prepared but currently commented out

    Side Effects:
        - Creates a new customer record in the backend system

    Returns:
        None
    """

    apply_global_style()
    st.header("➕ Customer Registration")

    # Fetch existing customers
    customers = api_call("GET", "/all_customers", st.session_state["token"]) or []

    existing_emails = [c["customer_email"] for c in customers]
    existing_mobiles = [c["customer_mobile_number"] for c in customers]

    # ---- INPUTS ----
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

    # ---- FORM SUBMIT ----
    with st.form("customer_registration_form"):
        submitted = st.form_submit_button("Register")

    if submitted:
        api_call(
            "POST",
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
        st.success("Customer created successfully ✅")

def customer_update():
    """
    Render the customer update interface and modify existing customer data.

    This function allows an administrator to update customer details by
    selecting a customer via email. Immutable fields such as email and
    mobile number are displayed but disabled to prevent modification.
    Updated customer information is submitted to the backend update endpoint.

    API Calls:
        - GET /all_customers
        - PUT /update_customer

    UI Behavior:
        - Applies global UI styles
        - Displays a customer selection dropdown
        - Pre-fills form fields with existing customer data
        - Clears form fields upon successful submission

    Access Control:
        - Requires authenticated session with appropriate privileges

    Side Effects:
        - Updates customer record in the backend database

    Returns:
        None
    """

    apply_global_style()
    st.subheader("👤 Update Customer")

    customers = api_call("GET", "/all_customers", st.session_state["token"]) or []

    email_map = {
        c["customer_email"]: c for c in customers
    }

    selected_email = st.selectbox(
        "Select Customer Email",
        ["Select Email"] + list(email_map.keys())
    )

    if selected_email != "Select Email":
        customer = email_map[selected_email]

        with st.form("customer_update_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Name", customer["customer_name"])
                mobile = st.text_input("Name", customer["customer_mobile_number"], disabled=True)

            with col2:
                company_name = st.text_input("Company", customer["customer_company_name"])
                email = st.text_input("Email", customer["customer_email"], disabled=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                city = st.text_input("City", customer["customer_city"])
            with col2:
                state = st.text_input("State", customer["customer_state"])
            with col3:
                country = st.text_input("Country", customer["customer_country"])

            address = st.text_area("Address", customer["customer_address"])

            submitted = st.form_submit_button("Update")

            if submitted:
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
                st.success("Customer updated successfully ✅")
