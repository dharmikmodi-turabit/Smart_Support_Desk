import streamlit as st
from api import api_call
from datetime import datetime
import pandas as pd
from ui import apply_global_style

@st.cache_data(ttl=30)
def get_all_tickets(token):
    """
    Fetch all tickets from the backend API and cache the result for 30 seconds.

    Args:
        token (str): JWT access token for authentication.

    Returns:
        list[dict]: List of ticket objects, or None if API call fails.
    """
    return api_call("GET", "/all_tickets", token)


def get_customer_tickets(token):
    """
    Fetch tickets associated with the logged-in customer.

    Args:
        token (str): JWT access token for authentication.

    Returns:
        list[dict]: List of customer tickets, or None if API call fails.
    """
    return api_call("GET", "/customer_my_tickets", token)


def ticket_view():
    """
    Display a Streamlit table of all tickets for employees/admins.

    Features:
        - Fetches all tickets from the backend
        - Displays a DataFrame with Ticket ID, Customer ID, Service Person, Title, Issue Type, Priority, Status
        - Columns are formatted for readability
        - Read-only data editor for visual inspection

    Returns:
        None
    """
    apply_global_style()
    st.header("Ticket Management")
    data = get_all_tickets(st.session_state["token"])
    if data:
        df = pd.DataFrame(data)[
            ["ticket_id", "customer_id", "service_person_emp_id", "issue_title","issue_type", "priority", "ticket_status"]
        ]
        df = df.rename(columns={
            "ticket_id": "Ticket ID",
            "issue_title": "Title",
            "priority": "Priority",
            "ticket_status": "Status",
            "service_person_emp_id" : "Service person ID",
            "customer_id" : "Customer ID",
            "issue_type":"Issue Type"
        })
        st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ticket ID": st.column_config.NumberColumn(width="small"),
                "Title": st.column_config.TextColumn(width="large"),
                "Issue Type": st.column_config.TextColumn(width="medium"),
                "Priority": st.column_config.TextColumn(width="small"),
                "Status": st.column_config.TextColumn(width="small"),
                "Service person ID": st.column_config.NumberColumn(width="small"),
                "Customer ID": st.column_config.NumberColumn(width="small"),
            },
            disabled=True
        )


def customer_ticket_view():
    """
    Display a Streamlit table of tickets for the logged-in customer.

    Features:
        - Fetches tickets specific to the current customer
        - Shows Ticket ID, Customer ID, Service Person, Title, Issue Type, Priority, Status
        - Read-only DataFrame with formatted columns

    Returns:
        None
    """
    apply_global_style()
    st.header("Ticket Management")
    data = get_customer_tickets(st.session_state["token"])
    if data:
        df = pd.DataFrame(data)[
            ["ticket_id", "customer_id", "service_person_emp_id", "issue_title","issue_type", "priority", "ticket_status"]
        ]
        df = df.rename(columns={
            "ticket_id": "Ticket ID",
            "issue_title": "Title",
            "priority": "Priority",
            "ticket_status": "Status",
            "service_person_emp_id" : "Service person ID",
            "customer_id" : "Customer ID",
            "issue_type":"Issue Type"
        })
        st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ticket ID": st.column_config.NumberColumn(width="small"),
                "Title": st.column_config.TextColumn(width="large"),
                "Issue Type": st.column_config.TextColumn(width="medium"),
                "Priority": st.column_config.TextColumn(width="small"),
                "Status": st.column_config.TextColumn(width="small"),
                "Service person ID": st.column_config.NumberColumn(width="small"),
                "Customer ID": st.column_config.NumberColumn(width="small"),
            },
            disabled=True
        )


def ticket_create():
    """
    Streamlit form to create a new ticket.

    Features:
        - Input fields for Customer Email, Title, Issue Type, Description, and Priority
        - Two options for creation:
            1. Normal ticket creation (saved in backend DB)
            2. HubSpot-only ticket creation
        - Sends POST requests to backend with appropriate payload

    Returns:
        None
    """
    apply_global_style()
    st.header("Create Ticket")
    customer_email = st.text_input("Customer Email")
    title = st.text_input("Issue Title")
    issue_type = st.text_input("Issue Type")
    desc = st.text_area("Description")
    priority = st.selectbox("Priority", ["Low", "Medium", "High"])

    if st.button("Create Ticket"):
        api_call(
            "POST",
            "/ticket_registration",
            st.session_state["token"],
            {
                "customer_email": customer_email,
                "issue_title": title,
                "issue_type": issue_type,
                "issue_description": desc,
                "priority": priority,
                "generate_datetime": datetime.utcnow().isoformat()
            }
        )

    if st.button("Create Ticket only in Hubspot"):
        api_call(
            "POST",
            "/hubspot_ticket_registration",
            st.session_state["token"],
            {
                "customer_email": customer_email,
                "issue_title": title,
                "issue_description": desc,
                "priority": priority
            }
        )


def ticket_update(role):
    """
    Streamlit form to update ticket information for employees or agents.

    Features:
        - Shows dropdown of all assigned/unassigned tickets
        - Displays ticket details in editable inputs:
            - Issue Title, Issue Type, Description, Priority, Status
        - Maintains session_state for selected ticket to preserve edits
        - Sends PUT request to backend on update

    Args:
        role (str): Role of the user ("Admin", "Agent", or "Service Person") to control which tickets are visible

    Returns:
        None
    """
    apply_global_style()
    st.header("🛠 Update Assigned Ticket")
    tickets = get_all_tickets(st.session_state["token"])
    unassign_tickets = [i for i in tickets if i['service_person_emp_id']==None]

    if role not in ['Admin','Agent']:
        tickets = api_call(
            "GET",
            "/my_tickets",
            st.session_state["token"]
        ) + unassign_tickets or []

    if not tickets:
        st.warning("No tickets assigned")
        return

    # Dropdown mapping and session state initialization
    ticket_map = {}
    ticket_labels = []

    for t in tickets:
        if t["service_person_emp_id"] is None:
            label = f"{t['ticket_id']}  🔴 (Unassigned)"
        else:
            label = t['ticket_id']
        ticket_map[label] = t
        ticket_labels.append(label)

    selected_ticket_id = st.selectbox(
        "Select Ticket ID",
        ticket_labels,
        key="ticket_selectbox"
    )
    split_id = int(str(selected_ticket_id).split(" ")[0])
    selected_ticket = ticket_map[selected_ticket_id]

    if (
        "active_ticket_id" not in st.session_state
        or st.session_state.active_ticket_id != selected_ticket_id
    ):
        st.session_state.active_ticket_id = selected_ticket_id
        st.session_state.issue_title = selected_ticket["issue_title"]
        st.session_state.issue_type = selected_ticket["issue_type"]
        st.session_state.issue_desc = selected_ticket["issue_description"]
        st.session_state.priority = selected_ticket["priority"]
        st.session_state.ticket_status = selected_ticket["ticket_status"]

    st.text_input("Issue Title", key="issue_title")
    st.text_input("Issue Type", key="issue_type")
    st.text_area("Description", key="issue_desc")
    st.selectbox("Priority", ["Low", "Medium", "High"], key="priority")
    st.selectbox("Status", ["Open", "In_Progress", "Close"], key="ticket_status")

    if st.button("✅ Update Ticket"):
        payload = {
            "ticket_id": split_id,
            "issue_title": st.session_state.issue_title,
            "issue_type": st.session_state.issue_type,
            "issue_description": st.session_state.issue_desc,
            "priority": st.session_state.priority,
            "ticket_status": st.session_state.ticket_status,
            "generate_datetime": datetime.utcnow().isoformat()
        }
        api_call("PUT", "/update_ticket", st.session_state["token"], payload)
        st.success("Ticket updated successfully 🎉")


def agent_ticket_list():
    """
    Display a list of tickets assigned to the logged-in agent.

    Features:
        - Fetches agent-specific tickets
        - Highlights tickets needing a reply with a visual indicator
        - Shows ticket ID, title, priority, status
        - Returns a DataFrame for further processing or selection

    Returns:
        pd.DataFrame: DataFrame of agent tickets with 'needs_reply' indicator
    """
    st.subheader("🎫 Assigned Tickets")
    tickets = api_call("GET", "/agent_tickets", st.session_state["token"]) or []

    if not tickets:
        st.info("No tickets")
        return

    df = pd.DataFrame(tickets)
    df["🔔 New Msg"] = df["needs_reply"].apply(lambda x: "🔴 New" if x else "")

    st.data_editor(
        df[["🔔 New Msg", "ticket_id", "issue_title", "priority", "ticket_status"]],
        hide_index=True,
        disabled=True,
        use_container_width=True
    )

    return df
