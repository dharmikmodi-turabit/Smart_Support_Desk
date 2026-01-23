# import os
# import requests
# HUBSPOT_CONTACT_URL = "https://api.hubapi.com/crm/v3/objects/contacts"

# HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
# HEADERS = {
#     "Authorization": f"Bearer {HUBSPOT_TOKEN}",
#     "Content-Type": "application/json"
# }



# def create_contact_from_db(customer):
#     HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
#     HEADERS = {
#         "Authorization": f"Bearer {HUBSPOT_TOKEN}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "properties": {
#             "email": customer["customer_email"],

#             "customer_id": customer["customer_id"],
#             "customer_name": customer["customer_name"],
#             "customer_email": customer["customer_email"],
#             "customer_mobile_number": customer["customer_mobile_number"],
#             "customer_company_name": customer["customer_company_name"],
#             "customer_city": customer["customer_city"],
#             "customer_state": customer["customer_state"],
#             "customer_country": customer["customer_country"],
#             "customer_address": customer["customer_address"],
#         }
#     }

#     response = requests.post(
#         HUBSPOT_CONTACT_URL,
#         headers=HEADERS,
#         json=payload
#     )

#     response.raise_for_status()
#     return response.json()

import requests, os

url = "https://api.hubapi.com/crm/v3/objects/contacts"

def create_contact_from_db(customer):
    HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "properties": {
            "email": customer["customer_email"],

            "customer_id": customer["customer_id"],
            "customer_name": customer["customer_name"],
            "customer_email": customer["customer_email"],
            "customer_mobile_number": customer["customer_mobile_number"],
            "customer_company_name": customer["customer_company_name"],
            "customer_city": customer["customer_city"],
            "customer_state": customer["customer_state"],
            "customer_country": customer["customer_country"],
            "customer_address": customer["customer_address"],
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def get_contact_id_by_email(email):
    url = "https://api.hubapi.com/crm/v3/objects/contacts/search"

    HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "email",
                "operator": "EQ",
                "value": email
            }]
        }],
        "properties": ["email"],
        "limit": 1
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    results = response.json().get("results", [])
    return results[0]["id"] if results else None

def update_contact(contact_id, customer):
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"

    HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }

    properties = {
            "email": customer["customer_email"],

            "customer_id": customer["customer_id"],
            "customer_name": customer["customer_name"],
            "customer_email": customer["customer_email"],
            "customer_mobile_number": customer["customer_mobile_number"],
            "customer_company_name": customer["customer_company_name"],
            "customer_city": customer["customer_city"],
            "customer_state": customer["customer_state"],
            "customer_country": customer["customer_country"],
            "customer_address": customer["customer_address"],
        }

    properties = {k: v for k, v in properties.items() if v}

    payload = {"properties": properties}

    response = requests.patch(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()
def sync_contact(customer):
    email = customer["customer_email"]

    contact_id = get_contact_id_by_email(email)

    if contact_id:
        # ✅ UPDATE
        return update_contact(contact_id, customer)
    else:
        # ✅ CREATE
        return create_contact_from_db(customer)

# def upsert_contact_from_db(customer):
#     url = "https://api.hubapi.com/crm/v3/objects/contacts/search"

#     HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
#     headers = {
#         "Authorization": f"Bearer {HUBSPOT_TOKEN}",
#         "Content-Type": "application/json"
#     }

#     properties = {
#             "email": customer["customer_email"],

#             "customer_id": customer["customer_id"],
#             "customer_name": customer["customer_name"],
#             "customer_email": customer["customer_email"],
#             "customer_mobile_number": customer["customer_mobile_number"],
#             "customer_company_name": customer["customer_company_name"],
#             "customer_city": customer["customer_city"],
#             "customer_state": customer["customer_state"],
#             "customer_country": customer["customer_country"],
#             "customer_address": customer["customer_address"],
#         }

#     # 🔥 Remove empty fields
#     properties = {k: v for k, v in properties.items() if v}

#     payload = {"properties": properties}

#     response = requests.post(url, json=payload, headers=headers)

#     if response.status_code >= 400:
#         print("HubSpot error:", response.text)

#     response.raise_for_status()
#     return response.json()
