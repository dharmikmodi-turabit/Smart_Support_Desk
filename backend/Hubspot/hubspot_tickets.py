from fastapi import APIRouter, HTTPException,status, Depends
from backend.database.database import access_db
from pydantic import BaseModel
import requests, os
from requests.exceptions import RequestException
from enum import Enum
from dotenv import load_dotenv
from backend.Hubspot.hubspot_contacts import get_contact_id_by_email
# from ticket import TicketRegister,Depends,admin_agent_required
from backend.Authentication.dependencies import admin_agent_required

hubspot_ticket_router = APIRouter(prefix="/hubspot", tags=["HubSpot Ticket"])
router  = hubspot_ticket_router
SUPPORT_PIPELINE_ID = "0"
STAGE_NEW = "1"

load_dotenv()
BASE_URL = "https://api.hubapi.com"
class TicketPriority(str,Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"

class HubspotTicketRegister(BaseModel):
    customer_email : str
    issue_title : str
    issue_description : str 
    priority : TicketPriority

def hubspot_create_ticket(payload):
    """
    Create a ticket in HubSpot via the API.

    Args:
    - payload (dict): JSON payload containing ticket properties and associations.

    Returns:
    - requests.Response: Response object from the HubSpot API.

    Raises:
    - RuntimeError: If the HubSpot API request fails.
    """

    try:
        url = "https://api.hubapi.com/crm/v3/objects/tickets"
        HUBSPOT_TOKEN = os.getenv("HUBSPOT_TOKEN")

        headers = {
            "Authorization": f"Bearer {HUBSPOT_TOKEN}",
            "Content-Type": "application/json"
        }

        return requests.post(url, headers=headers, json=payload)
    except RequestException as e:
        raise RuntimeError(f"HubSpot API request failed: {e}")


@hubspot_ticket_router.post("/hubspot_ticket_registration", tags=["Hubspot Ticket"])
def hubspot_ticket_registration(data:HubspotTicketRegister,user=Depends(admin_agent_required),db = Depends(access_db)):
    """
    Register a new ticket in HubSpot for a customer.

    This endpoint:
    1. Checks if the customer exists in the local database.
    2. Fetches the HubSpot contact ID for the customer.
    3. Creates a new ticket in HubSpot and associates it with the customer.

    Args:
    - data (HubspotTicketRegister): Ticket details including customer email, title, description, and priority.
    - user (dict, Depends): Authenticated user (Admin or Agent).
    - db (Connection, Depends): Database connection.

    Returns:
    - dict: {
        "status": "success",
        "message": str  # HubSpot ticket ID
    }

    Raises:
    - HTTPException (404): If the customer is not found.
    - HTTPException (400): If HubSpot API returns an error.
    - HTTPException (500): For unexpected errors.
    """

    try:
        with db:
            with db.cursor() as cursor:
                customer = cursor.execute("select * from customer where customer_email = %s",(data.customer_email,))
                if customer:
                    customer = cursor.fetchone()
                    # 3️⃣ Prepare ticket payload for HubSpot
                    hubspot_contact_id = get_contact_id_by_email(data.customer_email)
                    ticket_payload = {
                        "properties": {
                            "subject": data.issue_title,
                            "content": data.issue_description,
                            "hs_pipeline": "0",
                            "hs_pipeline_stage": "1",
                            "hs_ticket_priority": data.priority.upper(),
                            "hubspot_owner_id": 87397359
                        },
                        "associations": [
                            {
                                "to": {"id": hubspot_contact_id},
                                "types": [
                                    {
                                        "associationCategory": "HUBSPOT_DEFINED",
                                        "associationTypeId": 16
                                    }
                                ]
                            }
                        ]
                    }

                    # 4️⃣ Create ticket in HubSpot
                    response = hubspot_create_ticket(
                        ticket_payload
                    )
                    if response.status_code != 201:
                        raise HTTPException(status_code=400, detail=response.text)

                    hubspot_ticket_id = response.json()["id"]

                    return {
                        "status": "success",
                        "message": f"Ticket generated & HubSpot Ticket id is {hubspot_ticket_id}"
                    }
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found",
                ) 
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )



@router.post("/ticket/create/{ticket_id}")
def create_ticket_in_hubspot_from_db(ticket_id: int):
    """
    Sync a ticket from the local database to HubSpot.

    Steps:
    1. Fetch ticket by `ticket_id`.
    2. Fetch associated customer's email.
    3. Fetch HubSpot contact ID.
    4. Create ticket in HubSpot.
    5. Store HubSpot ticket ID in the local database.

    Args:
    - ticket_id (int): ID of the local ticket.

    Returns:
    - dict: {
        "status": "success",
        "hubspot_ticket_id": str
    }

    Raises:
    - HTTPException (404): If ticket or customer is not found.
    - HTTPException (400): If HubSpot API returns an error.
    - HTTPException (500): For unexpected errors.
    """

    try:
        conn = access_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ticket WHERE ticket_id=%s", (ticket_id,))
        ticket = cursor.fetchone()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        cursor.execute(
            "SELECT customer_email FROM customer WHERE customer_id=%s",
            (ticket["customer_id"],)
        )
        customer = cursor.fetchone()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        hubspot_contact_id = get_contact_id_by_email(customer["customer_email"])
        HUBSPOT_STATUS_MAP = {
            "Open": 1,
            "In_Progress": 3,
            "Close": 4
        }

        payload = {
            "properties": {
                "subject": ticket["issue_title"],
                "content": ticket["issue_description"],
                "hs_pipeline": "0",
                "hs_pipeline_stage": HUBSPOT_STATUS_MAP[ticket["ticket_status"]],
                "hs_ticket_priority": ticket["priority"].upper(),
                "hubspot_owner_id": 87397359
            },
            "associations": [
                {
                    "to": {"id": hubspot_contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 16
                        }
                    ]
                }
            ]
        }


        res = hubspot_create_ticket(payload)

        if res.status_code != 201:
            raise HTTPException(status_code=400, detail=res.text)

        hubspot_ticket_id = res.json()["id"]

        cursor.execute(
            "UPDATE ticket SET hubspot_ticket_id=%s WHERE ticket_id=%s",
            (hubspot_ticket_id, ticket_id)
        )
        conn.commit()

        return {
            "status": "success",
            "hubspot_ticket_id": hubspot_ticket_id
        } 
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )


def hubspot_update_ticket(hubspot_ticket_id, data):
    """
    Update an existing HubSpot ticket.

    Updates ticket properties such as priority, pipeline stage, and reason.

    Args:
    - hubspot_ticket_id (str): ID of the HubSpot ticket.
    - data (object): Ticket update data, may include priority, status, and reason.

    Raises:
    - HTTPException (500): If the HubSpot API request fails.
    """

    try:
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

        r = requests.patch(
            f"{url}/{hubspot_ticket_id}",
            headers=HEADERS,
            json=payload
        )

        r.raise_for_status() 
    except RequestException as e:
        raise RuntimeError(f"HubSpot API request failed: {e}")

def hubspot_close_ticket(hubspot_ticket_id):
    """
    Close a HubSpot ticket by updating its pipeline stage to 'Closed'.

    Args:
    - hubspot_ticket_id (str): ID of the HubSpot ticket.

    Raises:
    - HTTPException (500): If the HubSpot API request fails.
    """

    try:
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
    except RequestException as e:
        raise RuntimeError(f"HubSpot API request failed: {e}")


def fetch_ticket_by_id(ticket_id: str):
    """
    Fetch a HubSpot ticket by its HubSpot ticket ID.

    Args:
    - ticket_id (str): HubSpot ticket ID.

    Returns:
    - dict: HubSpot ticket object including properties:
        - subject
        - content
        - hs_pipeline_stage
        - hs_ticket_priority
        - createdate

    Raises:
    - HTTPException (500): If the HubSpot API request fails.
    """

    try:
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
    except RequestException as e:
        raise RuntimeError(f"HubSpot API request failed: {e}")

@router.get("/ticket/{ticket_id}")
def get_ticket_from_hubspot(ticket_id: int):
    """
    Retrieve a ticket from HubSpot for a given local ticket ID.

    This endpoint:
    1. Fetches the local ticket and its HubSpot ticket ID.
    2. Calls HubSpot API to retrieve the ticket details.

    Args:
    - ticket_id (int): Local ticket ID.

    Returns:
    - dict: HubSpot ticket object.

    Raises:
    - HTTPException (404): If ticket is not synced to HubSpot.
    - HTTPException (500): For unexpected errors.
    """

    try:
        conn = access_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT hubspot_ticket_id FROM ticket WHERE ticket_id=%s",
            (ticket_id,)
        )
        ticket = cursor.fetchone()

        if not ticket or not ticket["hubspot_ticket_id"]:
            raise HTTPException(404, "Ticket not synced to HubSpot")

        return fetch_ticket_by_id(ticket["hubspot_ticket_id"]) 
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )
