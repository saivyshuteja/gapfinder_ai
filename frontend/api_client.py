import requests
import streamlit as st

BACKEND_URL = "http://127.0.0.1:8000"


def api_request(
    method: str,
    endpoint: str,
    json=None,
    data=None,
    files=None,
    params=None,
):
    url = f"{BACKEND_URL}{endpoint}"

    headers = {}

    token = st.session_state.get("access_token")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            data=data,
            files=files,
            params=params,
            timeout=120,
        )

        if response.status_code == 401:
            st.session_state["authenticated"] = False
            st.session_state["access_token"] = None
            st.session_state["user"] = None

        return response

    except requests.exceptions.ConnectionError:
        st.error(
            "Cannot connect to the GapFinder AI backend. "
            "Make sure FastAPI is running on port 8000."
        )
        return None

    except requests.exceptions.Timeout:
        st.error("The backend request timed out.")
        return None

    except requests.exceptions.RequestException as exc:
        st.error(f"API request failed: {exc}")
        return None


def get_json(response):
    if response is None:
        return None

    try:
        return response.json()
    except ValueError:
        return None