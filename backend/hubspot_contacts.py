from fastapi import status,HTTPException
import os,requests
from requests.exceptions import RequestException

url = "https://api.hubapi.com"

def create_contact_from_db(customer):
    """
    Create a new HubSpot contact from a customer record in the database.

    This function sends a request to the HubSpot CRM API to create a contact
    with the customer's details. Returns the HubSpot contact ID for internal use.

    Args:
    - customer (dict): Customer record containing all relevant fields.

    Returns:
    - str: HubSpot contact ID of the newly created contact.

    Raises:
    - RuntimeError: If the HubSpot API request fails.
    """

    try:
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
    except RequestException as e:
        raise RuntimeError(f"HubSpot API request failed: {e}")

def get_contact_id_by_email(email):
    """
    Retrieve a HubSpot contact ID using an email address.

    This function queries the HubSpot CRM Contacts Search API to find
    a contact matching the provided email address and returns the
    corresponding contact ID if found.

    Args:
    - email (str): Email address used to search for the contact in HubSpot.

    Returns:
    - str | None: The HubSpot contact ID if a matching contact is found,
      otherwise None.

    Raises:
    - HTTPException (500): If an error occurs while calling the HubSpot API
      or processing the response.
    """

    try:
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

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

def update_contact(contact_id, customer):
    """
    Update an existing HubSpot contact with new customer data.

    Sends a PATCH request to the HubSpot CRM API to update the contact's
    properties. Only non-empty values are sent in the request.

    Args:
    - contact_id (str): HubSpot contact ID to update.
    - customer (dict): Customer record with updated data.

    Returns:
    - dict: JSON response from HubSpot API.

    Raises:
    - RuntimeError: If the HubSpot API request fails.
    """

    try:
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
    except RequestException as e:
        raise RuntimeError(f"HubSpot API request failed: {e}")


def sync_contact(customer, db):
    """
    Synchronize a customer record with HubSpot.

    This function ensures that a customer is represented in HubSpot:
    1. If the HubSpot contact ID exists, it updates the contact.
    2. Else, it searches for an existing contact by email.
    3. If not found, it creates a new contact.

    After syncing, the HubSpot contact ID is saved in the local database.

    Args:
    - customer (dict): Customer record to sync.
    - db: Database connection object.

    Returns:
    - str: HubSpot contact ID.

    Raises:
    - RuntimeError: If any HubSpot API request fails.
    """

    try:
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
    except RequestException as e:
        raise RuntimeError(f"HubSpot API request failed: {e}")

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
    """
    Fetch a HubSpot contact by contact ID.

    This function retrieves a contact record from the HubSpot CRM using the
    contact's unique HubSpot ID and returns the contact data including
    custom customer-related properties.

    Args:
    - contact_id (str): Unique HubSpot contact ID.

    Returns:
    - dict: HubSpot contact object containing standard and custom properties
      such as email, customer ID, name, mobile number, company, and address.

    Raises:
    - RuntimeError: If the HubSpot access token is missing or if the
      HubSpot API request fails.
    """

    try:
        HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")
        if not HUBSPOT_TOKEN:
            raise RuntimeError("HUBSPOT_TOKEN is not configured")

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
    except RequestException as e:
        raise RuntimeError(f"HubSpot API request failed: {e}")