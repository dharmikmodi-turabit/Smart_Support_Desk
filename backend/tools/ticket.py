from database import access_db
from pydantic import BaseModel, ValidationError
from langchain.tools import tool
from typing import Optional
from enum import Enum
from datetime import datetime
import requests

API_BASE_URL = "http://127.0.0.1:8000"

class TicketPriority(str,Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"

class TicketStatus(str,Enum):
    Open = "Open"
    Low = "Close"
    Medium = "In_Progress"

class Create_ticket(BaseModel):
    customer_email : str
    issue_title : str 
    issue_type : str 
    issue_description : str 
    priority : TicketPriority 
    token :str | None = None


@tool("create_ticket", args_schema=Create_ticket)
def create_ticket(
    customer_email : str,
    token :str,
    issue_title : Optional[str] = None,
    issue_type : Optional[str] = None, 
    issue_description : Optional[str] = None, 
    priority : Optional[TicketPriority] = None, 
    **kwargs
) -> dict:
    """
    You are an intelligent CRM ticket creation assistant.

    When a user describes a problem in natural language, you must:
    1. Understand the user's issue intent.
    2. Automatically determine the following fields from the conversation:
       - issue_title: A short concise summary (max 8–12 words).
       - issue_description: A clear detailed explanation of the problem.
       - issue_type: Classify into one of:
            "Technical", "Billing", "Access", "Bug", "Feature Request", "General"
            or also you can think by your self if any other is relate
       - priority:
            "Low"  → general queries, minor inconvenience
            "Medium" → normal operational issues
            "High" → blocking work or affecting multiple users

    3. If the user already explicitly provides any field, use the user-provided value.
    4. If some information is missing but can reasonably be inferred, infer it intelligently.
    5. Only ask the user follow-up questions if the issue cannot be reasonably understood.
    6. Always return structured tool arguments ready for the ticket creation tool call.
    7. Never ask for system-controlled fields such as token, timestamps, ids, or backend metadata.
    explicitly
 
    """
    try:
        generate_datetime = datetime.utcnow().isoformat()

        payload = {
                "customer_email" : customer_email,
                "generate_datetime" : generate_datetime,
                "issue_title" : issue_title,
                "issue_type" : issue_type,
                "issue_description" : issue_description,
                "priority" : priority,
            }


        response = requests.post(
            f"{API_BASE_URL}/ticket_registration",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        return response.json()

    except KeyError as e:
        return {
            "error": "Missing required field",
            "required_fields": [
                "token","customer_email"
            ],
            "missing_field": str(e)
        }

    except ValidationError as e:
        return {
            "error": "Invalid input data",
            "details": e.errors()
        }

class UpdateTicketSchema(BaseModel):
    ticket_id: int
    issue_type: Optional[str] = None
    issue_description: Optional[str] = None
    priority: Optional[str] = None
    reason: Optional[str] = None
    ticket_status: Optional[str] = None
    token: Optional[str] = None

@tool("update_ticket", args_schema=UpdateTicketSchema)
def update_ticket(
    ticket_id: int,
    issue_type: Optional[str] = None,
    issue_description: Optional[str] = None,
    priority: Optional[str] = None,
    reason: Optional[str] = None,
    ticket_status: Optional[str] = None,
    token: Optional[str] = None,
):
    """
    Update an existing ticket.

    Allowed for ADMIN and AGENT roles.
    Can update issue type, description, priority, reason, or ticket status.
    """

    try:
        payload = {
            "ticket_id": ticket_id,
            "issue_type": issue_type,
            "issue_description": issue_description,
            "priority": priority,
            "reason": reason,
            "ticket_status": ticket_status,
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        response = requests.put(
            f"{API_BASE_URL}/update_ticket",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )

        return response.json()

    except Exception as e:
        return {"error": str(e)}






class EmpMyTickets(BaseModel):
    token: str   # backend injected


@tool("emp_my_tickets", args_schema=EmpMyTickets)
def emp_my_tickets(token: str=None) -> dict:
    """
    Retrieve all tickets assigned to the currently authenticated employee.

    This tool calls the `/my_tickets` API endpoint. The employee identity
    is resolved on the backend using the JWT token, so no employee ID
    needs to be provided explicitly.

    Args:
        token (str): Authorization JWT token injected by the backend.

    Returns:
        dict: JSON response containing the list of tickets assigned
        to the logged-in employee, or an error message if the request fails.
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/my_tickets",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()

    except Exception as e:
        return {"error": str(e)}


class CustomerMyTickets(BaseModel):
    token: str   # backend injected

@tool("customer_my_tickets", args_schema=CustomerMyTickets)
def customer_my_tickets(token: str) -> dict:
    """
    Retrieve all tickets created by the currently authenticated customer.

    This tool calls the `/customer_my_tickets` API endpoint. The customer
    identity is automatically determined on the backend using the provided
    JWT token, so no customer ID needs to be supplied explicitly.

    Args:
        token (str): Authorization JWT token injected by the backend.

    Returns:
        dict: JSON response containing the list of tickets associated
        with the logged-in customer, or an error message if the request fails.
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/customer_my_tickets",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()

    except Exception as e:
        return {"error": str(e)}

class Fetch_all_tickets(BaseModel):
    token : str | None = None

@tool("fetch_all_tickets",args_schema=Fetch_all_tickets)
def fetch_all_tickets(token: str=None) -> list[dict]:
    
    """
    Fetch all tickets from the system.

    This tool retrieves all ticket records.
    Authentication is handled via injected token.
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/all_tickets",
            headers={
                "Authorization": f"Bearer {token}"
            },
        )
        return response.json()
    except Exception as e:
        return {"detail": str(e)}
    
class Fetch_tickets_by_customer(BaseModel):
    customer_email : str
    token : str | None = None

@tool("fetch_tickets_by_customer",args_schema=Fetch_tickets_by_customer)
def fetch_tickets_by_customer(customer_email: str, token: str):
    """
    Fetch tickets for a specific customer.
    Allowed only for ADMIN or AGENT.
    Retrieve all tickets created by the customer whose email is customer_email.

    This tool calls the `/fetch_tickets_by_customer` API endpoint. The customer
    identity is automatically determined on the backend using the provided
    email, so no customer ID needs to be supplied explicitly.

    Args:
        token (str): Authorization JWT token injected by the backend.
        customer_email (str) : Customer email to identify customer.

    Returns:
        dict: JSON response containing the list of tickets associated
        with email of the customer, or an error message if the request fails.
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/fetch_tickets_by_customer",
            headers={"Authorization": f"Bearer {token}"},
            json = {'customer_email':customer_email}
        )
        return response.json()

    except Exception as e:
        return {"error": str(e)}


@tool
def ticket_analysis_per_emp(emp_id: int=None, token: str=None):
    """
    Fetch ticket analytics (counts) for an employee.
    """
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        f"{API_BASE_URL}/ticket_analysis_per_emp",
        params={"emp_id": emp_id},
        headers=headers,
        timeout=10
    )

    if resp.status_code != 200:
        return {"detail": resp.json().get("detail", "Failed to fetch analysis")}

    return resp.json()