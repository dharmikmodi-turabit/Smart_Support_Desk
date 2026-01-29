from fastapi import APIRouter, HTTPException
from database import access_db
from hubspot_tickets import hubspot_create_ticket_single
from hubspot_contacts import get_contact_id_by_email
from hubspot_fetch import fetch_ticket_by_id

hubspot_ticket_router = APIRouter(prefix="/hubspot", tags=["HubSpot"])
router  = hubspot_ticket_router
SUPPORT_PIPELINE_ID = "0"
STAGE_NEW = "1"

@router.post("/ticket/create/{ticket_id}")
def create_ticket_in_hubspot(ticket_id: int):

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
    # HUBSPOT_PRIORITY_MAP = {
    #     "Low": "LOW",
    #     "Medium": "MEDIUM",
    #     "High": "HIGH",
    #     "Urgent": "URGENT"
    # }
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


    res = hubspot_create_ticket_single(payload)

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

# from hubspot_tickets import fetch_ticket_by_id


@router.get("/ticket/{ticket_id}")
def get_ticket_from_hubspot(ticket_id: int):

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
