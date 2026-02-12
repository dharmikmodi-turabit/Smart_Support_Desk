import streamlit as st
from api import api_call
from ui import apply_global_style
import pandas as pd



def employee_view():
    """
    Display the employee management view.

    Fetches all registered employees from the backend and displays them
    in a read-only data editor. Applies global UI styling for consistency.

    API Calls:
        - GET /all_employees

    UI Behavior:
        - Applies global styles
        - Shows employee list in a Streamlit data editor (read-only)

    Access Control:
        - Requires valid session token

    Returns:
        None
    """

    apply_global_style()
    st.title("👨‍💼 Employee Management")

    data = api_call("GET", "/all_employees", st.session_state["token"]) or []

    st.data_editor(
        data,
        use_container_width=True,
        hide_index=True,
        disabled=True
    )



def employee_add(role):
    """
    Render the employee registration form and add a new employee.

    Provides a form to register a new employee with fields for name, email,
    mobile, password, and role type. Validates email and mobile for uniqueness
    before submitting to the backend.

    API Calls:
        - GET /all_employees (to fetch existing employees)
        - POST /employee_registration (to create a new employee)

    UI Behavior:
        - Applies global UI styling
        - Shows warnings/errors for duplicate email/mobile
        - Displays success message on successful registration

    Validation:
        - Blocks registration if email or mobile already exists

    Side Effects:
        - Creates a new employee record in the backend

    Parameters:
        role (str): Role of the current logged-in user (used for UI logic)

    Returns:
        None
    """

    apply_global_style()
    st.title("➕ Register Employee")

    # Fetch existing employees once
    employees = api_call("GET", "/all_employees", st.session_state["token"]) or []
    existing_emails = [e["employee_email"] for e in employees]
    existing_mobiles = [e["employee_mobile_number"] for e in employees]

    # 🔹 LIVE INPUTS (outside form)
    col1, col2, col3 = st.columns(3)

    with col1:
        name = st.text_input("Name")

    with col2:
        roles = ["Admin", "Agent", "Service Person"]
        employee_type = st.selectbox("Employee Type", roles)

    with col3:
        password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        email = st.selectbox(
                "Email",
                options=[""] + existing_emails
            )

        email_exists = email in existing_emails
        if email and email_exists:
            st.error("❌ Email already exists")

    with col2:
        mobile = st.selectbox(
                "Mobile",
                options=[""] + existing_mobiles
            )

        mobile_exists = mobile in existing_mobiles
        if mobile and mobile_exists:
            st.error("❌ Mobile number already exists")

    # 🔹 SUBMIT FORM
    with st.form("employee_registration_form"):
        submitted = st.form_submit_button("Register")

    # 🔹 BLOCK SUBMIT
    if submitted:
        if not email:
            st.warning("Email is required")
        elif email_exists:
            st.error("Cannot register: Email already exists")
        elif mobile_exists:
            st.error("Cannot register: Mobile number already exists")
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
            st.success("Employee registered successfully 🎉")



def employee_update():
    """
    Render the employee update form and modify existing employee details.

    Allows updating employee details such as name, mobile, password, and type.
    Email is immutable and shown as read-only. Fetches all employees to populate
    a dropdown for selection. Updates backend via API upon form submission.

    API Calls:
        - GET /all_employees
        - PUT /employee_update

    UI Behavior:
        - Applies global UI styles
        - Pre-fills form with selected employee details
        - Supports updating fields and leaving password blank to retain old password

    Access Control:
        - Requires valid session token

    Side Effects:
        - Updates employee record in backend

    Returns:
        None
    """

    apply_global_style()
    st.header("👤 Update Employee")

    # Fetch all employees
    employees = api_call("GET", "/all_employees", st.session_state["token"]) or []

    if not employees:
        st.warning("No employees found")
        return

    # Build lookup by email
    emp_map = {e["employee_email"]: e for e in employees}

    selected_email = st.selectbox(
        "Select Employee Email",
        options=list(emp_map.keys())
    )

    selected_emp = emp_map[selected_email]

    ROLE_MAP = {
        1: "Admin",
        2: "Agent",
        3: "Service Person"
    }

    if st.session_state.get("selected_email") != selected_email:
        st.session_state.selected_email = selected_email
        st.session_state.name = selected_emp["employee_name"]
        st.session_state.email = selected_emp["employee_email"]
        st.session_state.mobile = selected_emp["employee_mobile_number"]
        st.session_state.type = ROLE_MAP[selected_emp["employee_type"]]
        st.session_state.password = ""


    roles = ["Admin", "Agent", "Service Person"]

    # ✅ FORM STARTS HERE
    with st.form("employee_update_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            st.session_state.name = st.text_input(
                "Name",
                value=st.session_state.name
            )

        with col2:
            st.session_state.type = st.selectbox(
                "Employee Type",
                roles,
                index=roles.index(st.session_state.type)
            )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.text_input(
                "Email",
                value=st.session_state.email,
                disabled=True
            )

        with col2:
            st.session_state.mobile = st.text_input(
                "Mobile",
                value=st.session_state.mobile
            )

        with col3:
            st.session_state.password = st.text_input(
                "Password (leave blank to keep same)",
                value=st.session_state.password,
                type="password"
            )

        submitted = st.form_submit_button("✅ Update")

    # ✅ SUBMIT HANDLING (OUTSIDE FORM)
    if submitted:
        api_call(
            "PUT",
            "/employee_update",
            st.session_state["token"],
            {
                "name": st.session_state.name,
                "email": st.session_state.email,
                "mobile_number": st.session_state.mobile,
                "password": st.session_state.password,
                "type": st.session_state.type
                }
            )
        st.success("Employee updated successfully 🎉")


def service_person_tickets():
    """
    Display tickets assigned to the currently logged-in service person.

    Fetches all tickets assigned to the current employee (service person) from
    the backend and displays them in a read-only data editor.

    API Calls:
        - GET /my_tickets

    UI Behavior:
        - Applies global UI styling
        - Shows assigned tickets in a Streamlit data editor (read-only)

    Access Control:
        - Requires valid session token

    Returns:
        None
    """

    apply_global_style()
    st.title("🛠 My Assigned Tickets")

    data = api_call("GET", "/my_tickets", st.session_state["token"]) or []

    st.data_editor(
        data,
        use_container_width=True,
        hide_index=True,
        disabled=True
    )



import streamlit as st
import pandas as pd
from api import api_call


def employee_chat_dashboard():
    """
    Display the agent ticket inbox for support personnel.

    Fetches all tickets for which the agent may respond, marks tickets that
    require a reply, and allows selection of a ticket to view conversation history.

    API Calls:
        - GET /agent_tickets

    UI Behavior:
        - Shows tickets in a data editor with a "New" indicator for pending replies
        - Allows selecting a ticket to open chat interface

    Access Control:
        - Requires valid session token for Admin/Agent

    Returns:
        None
    """


    st.header("🎧 Agent Ticket Inbox")

    tickets = api_call(
        "GET",
        "/agent_tickets",
        st.session_state["token"]
    ) or []

    if not tickets:
        st.info("No tickets")
        return

    df = pd.DataFrame(tickets)

    df["🔔"] = df["needs_reply"].apply(
        lambda x: "🔴 New" if x else ""
    )

    st.data_editor(
        df[["🔔", "ticket_id", "issue_title", "priority", "ticket_status"]],
        hide_index=True,
        disabled=True,
        use_container_width=True
    )

    ticket_id = st.selectbox(
        "Open Ticket",
        df["ticket_id"].tolist()
    )

    agent_ticket_chat(ticket_id)


def agent_ticket_chat(ticket_id):
    """
    Display and manage conversation for a specific ticket.

    Fetches the chat messages associated with the given ticket ID and displays
    them in a chat interface. Allows the agent to send a reply, which is posted
    to the backend.

    API Calls:
        - GET /customer_ticket_messages/{ticket_id}
        - POST /agent_ticket_message/{ticket_id}

    UI Behavior:
        - Shows chat history using Streamlit chat components
        - Supports sending new messages via chat input
        - Refreshes the view after sending a reply

    Parameters:
        ticket_id (int): ID of the ticket to display and respond to

    Access Control:
        - Requires valid session token

    Returns:
        None
    """


    st.subheader("💬 Conversation")

    messages = api_call(
        "GET",
        f"/customer_ticket_messages/{ticket_id}",
        st.session_state["token"]
    ) or []

    for msg in messages:
        if msg["sender_role"] == "Customer":
            with st.chat_message("user"):
                st.write(msg["message"])
        else:
            with st.chat_message("assistant"):
                st.write(msg["message"])

    reply = st.chat_input("Reply to customer...")

    if reply:
        api_call(
            "POST",
            f"/agent_ticket_message/{ticket_id}",
            st.session_state["token"],
            json={"message": reply}
        )
        st.rerun()
