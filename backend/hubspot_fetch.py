import os
import requests

BASE_URL = "https://api.hubapi.com"
HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json"
}

def fetch_ticket_by_id(hubspot_ticket_id: str):
    response = requests.get(
        f"{BASE_URL}/crm/v3/objects/tickets/{hubspot_ticket_id}",
        headers=HEADERS,
        params={
            "properties": [
                "subject",
                "content",
                "hs_pipeline",
                "hs_pipeline_stage",
                "hs_ticket_priority",
                "createdate"
            ]
        }
    )

    response.raise_for_status()
    return response.json()

def fetch_ticket_by_id(ticket_id: str):
    HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

    HEADERS = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }
    res = requests.get(
        f"{BASE_URL}/crm/v3/objects/tickets/{ticket_id}",
        headers=HEADERS,
        params={
            "properties": [
                "subject",
                "content",
                "hs_pipeline_stage",
                "hs_ticket_priority",
                "createdate"
            ]
        }
    )
    res.raise_for_status()
    return res.json()