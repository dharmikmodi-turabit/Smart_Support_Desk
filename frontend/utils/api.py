import requests
import streamlit as st

BASE_URL = "http://127.0.0.1:8000"

def logout_user(message="Session expired. Please login again."):
    """
    Log out the currently authenticated user and reset the application state.

    This function clears all Streamlit session data, displays an error
    message explaining the logout reason, and forces a full app rerun.
    It is primarily used when authentication fails (e.g., token expiry
    or invalid credentials).

    Args:
        message (str, optional):
            Message displayed to the user after logout.
            Defaults to "Session expired. Please login again."

    Side Effects:
        - Clears `st.session_state`
        - Displays an error message in the UI
        - Triggers `st.rerun()` to redirect the user to the login flow

    Returns:
        None
    """

    st.session_state.clear()
    st.error(message)
    st.rerun()


def api_call(method, endpoint, token=None, json=None, params=None):
    """
    Perform an authenticated HTTP request to the backend API.

    This helper function centralizes API communication for the Streamlit
     It automatically attaches the JWT token (if provided),
    handles common error scenarios, and manages token-expiry logout
    behavior.

    Features:
    - Supports all HTTP methods (GET, POST, PUT, PATCH, DELETE)
    - Injects Bearer token authentication
    - Detects token expiration (401) and forces logout
    - Displays backend error messages in the UI
    - Handles backend unavailability gracefully

    Args:
        method (str):
            HTTP method (e.g., "GET", "POST", "PUT", "DELETE").
        endpoint (str):
            API endpoint path (e.g., "/all_tickets").
        token (str, optional):
            JWT access token for Authorization header.
        json (dict, optional):
            JSON payload to send in the request body.
        params (dict, optional):
            Query parameters for the request.

    Returns:
        dict | list | None:
            Parsed JSON response from the backend on success,
            or None if an error occurs.
    """

    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        res = requests.request(
            method,
            BASE_URL + endpoint,
            headers=headers,
            json=json,
            params=params,
            timeout=100
        )
        # 🔥 HANDLE TOKEN EXPIRY
        if res.status_code == 401:
            logout_user(res.json().get("detail", "Invalid token"))

        if res.status_code >= 400:
            st.error(res.json().get("detail", "Something went wrong"))
            return None

        return res.json()

    except requests.exceptions.RequestException as e:
        st.error(f"Backend server not reachable {e}")
        return None
    