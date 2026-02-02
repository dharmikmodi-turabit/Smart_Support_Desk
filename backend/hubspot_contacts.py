
import requests, os

url = "https://api.hubapi.com"

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

    response = requests.post(f"{url}/crm/v3/objects/contacts", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data["id"]  # ✅ internal use only

def get_contact_id_by_email(email):

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

    response = requests.post(f"{url}/crm/v3/objects/contacts/search", json=payload, headers=headers)
    response.raise_for_status()

    results = response.json().get("results", [])
    return results[0]["id"] if results else None

def update_contact(contact_id, customer):

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
    print(payload)
    response = requests.patch(f"{url}/crm/v3/objects/contacts/{contact_id}", json=payload, headers=headers)
    print("________________--------------------------------------2",response)
    response.raise_for_status()
    return response.json()


def sync_contact(customer, db):
    email = customer["customer_email"]

    contact_id = customer.get("hubspot_contact_id")
    print(contact_id)
    # 1️⃣ If ID already stored → update directly
    # if contact_id:
    #     update_contact(contact_id, customer)
    #     return contact_id

    # 2️⃣ Else try search
    contact_id = get_contact_id_by_email(email)

    if contact_id:
        # save ID
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE customer SET hubspot_contact_id = %s WHERE customer_id = %s",
                (contact_id, customer["customer_id"])
            )
            db.commit()

        update_contact(contact_id, customer)
        return contact_id

    # 3️⃣ Else create
    contact_id = create_contact_from_db(customer)

    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE customer SET hubspot_contact_id = %s WHERE customer_id = %s",
            (contact_id, customer["customer_id"])
        )
        db.commit()

    return contact_id

# def fetch_contact_by_email(email: str):
#     HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
#     headers = {
#         "Authorization": f"Bearer {HUBSPOT_TOKEN}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "filterGroups": [{
#             "filters": [{
#                 "propertyName": "email",
#                 "operator": "EQ",
#                 "value": email
#             }]
#         }],
#         "properties": [
#             "email",

#             "customer_id",
#             "customer_name",
#             "customer_email",
#             "customer_mobile_number",
#             "customer_company_name",
#             "customer_city",
#             "customer_state",
#             "customer_country",
#             "customer_address",
#         ],
#         "limit": 1
#     }


#     res = requests.post(
#         f"{url}/crm/v3/objects/contacts/search",
#         headers=headers,
#         json=payload
#     )
#     res.raise_for_status()

#     results = res.json().get("results", [])
#     return results[0] if results else None

def fetch_contact_by_id(contact_id: str):
    HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }
    res = requests.get(
        f"{url}/crm/v3/objects/contacts/{contact_id}",
        headers=headers,
        params={
            "properties": [
                "email",

                "customer_id",
                "customer_name",
                "customer_email",
                "customer_mobile_number",
                "customer_company_name",
                "customer_city",
                "customer_state",
                "customer_country",
                "customer_address",
            ]
        }
    )
    res.raise_for_status()
    return res.json()