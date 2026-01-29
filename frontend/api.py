import requests
import streamlit as st

BASE_URL = "http://192.168.1.32:8000"

def logout_user(message="Session expired. Please login again."):
    st.session_state.clear()
    st.error(message)
    st.rerun()


def api_call(method, endpoint, token=None, json=None, params=None):
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
            timeout=5
        )

        # 🔥 HANDLE TOKEN EXPIRY
        if res.status_code == 401:
            logout_user(res.json().get("detail", "Invalid token"))

        if res.status_code >= 400:
            st.error(res.json().get("detail", "Something went wrong"))
            return None

        return res.json()

    except requests.exceptions.RequestException:
        st.error("Backend server not reachable")
        return None
    