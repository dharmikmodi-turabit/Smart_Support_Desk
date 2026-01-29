import requests, os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = "https://api.hubapi.com"
def hubspot_create_ticket(payload):
    # HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
    url = "https://api.hubapi.com/crm/v3/objects/tickets"
    HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }

    return requests.post(url, headers=headers, json=payload)
    
def hubspot_update_ticket(hubspot_ticket_id, data):
    url = "https://api.hubapi.com/crm/v3/objects/tickets"
    HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

    HEADERS = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "properties": {}
    }

    if data.priority:
        payload["properties"]["hs_ticket_priority"] = data.priority.value.upper()

    if data.ticket_status:
        payload["properties"]["hs_pipeline_stage"] = 1 if data.ticket_status=="Open" else 3

    if data.reason:
        payload["properties"]["reason"] = data.reason
       
    # print(payload)

    r = requests.patch(
        f"{url}/{hubspot_ticket_id}",
        headers=HEADERS,
        json=payload
    )

    r.raise_for_status()

def hubspot_close_ticket(hubspot_ticket_id):
    HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

    HEADERS = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "properties": {
            "hs_pipeline_stage": 4
        }
    }

    requests.patch(
        f"{BASE_URL}/crm/v3/objects/tickets/{hubspot_ticket_id}",
        headers=HEADERS,
        json=payload
    )

# import requests
# from dotenv import load_dotenv
# import os

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# load_dotenv(os.path.join(BASE_DIR, ".env"))

# HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
# HUBSPOT_TICKET_URL = "https://api.hubapi.com/crm/v3/objects/tickets"

# def hubspot_create_ticket_single(ticket_payload: dict):
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {HUBSPOT_TOKEN}"
#     }

#     response = requests.post(HUBSPOT_TICKET_URL, json=ticket_payload, headers=headers)
#     return response
import requests
import os


def hubspot_create_ticket_single(payload: dict):
    url = "https://api.hubapi.com/crm/v3/objects/tickets"
    HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }

    return requests.post(url, headers=headers, json=payload)
