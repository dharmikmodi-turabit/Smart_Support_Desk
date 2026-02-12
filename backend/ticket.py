from fastapi import status,Depends, HTTPException, APIRouter
from database import access_db
from dependencies import get_current_user,admin_agent_required, HTTPAuthorizationCredentials, security, customer_required, admin_agent_customer_required
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime
from redis_client import redis_client
from hubspot_tickets import hubspot_create_ticket, hubspot_close_ticket, hubspot_update_ticket
from hubspot_contacts import get_contact_id_by_email


ticket_router = APIRouter()

class TicketPriority(str,Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"

class TicketStatus(str,Enum):
    Open = "Open"
    Low = "Close"
    Medium = "In_Progress"

class TicketRegister(BaseModel):
    customer_email : str
    issue_title : str 
    issue_type : str 
    issue_description : str 
    priority : TicketPriority 
    generate_datetime : datetime

class TicketUpdate(BaseModel):
    ticket_id : int
    # service_person_emp_id : int
    issue_type : Optional[str] = None 
    issue_description : Optional[str] = None 
    priority : Optional[TicketPriority] = None 
    reason : Optional[str] = None
    ticket_status : Optional[TicketStatus] = None

@ticket_router.get("/all_tickets", tags=["Ticket"])
def fetch_all_tickets(user=Depends(get_current_user),db = Depends(access_db)):
    """
    Fetch all tickets from the system.

    This endpoint retrieves every ticket stored in the database.
    It requires a valid authenticated user and is typically intended
    for administrative or internal use.

    Dependencies:
        - get_current_user: Ensures the request is authenticated.
        - access_db: Provides a database connection.

    Returns:
        list[dict]:
            A list of ticket records.

    Raises:
        HTTPException:
            404 - If no tickets are found.
            500 - If a database or server error occurs.
    """
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select * from ticket")
                d = cursor.fetchall()
                if d:
                    return d
                else:
                    raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Ticket not found"
                        )
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )
    
@ticket_router.post("/ticket_registration", tags=["Ticket"])
def ticket_registration(data:TicketRegister,user=Depends(admin_agent_required),db = Depends(access_db)):
    """
    Create a new ticket and sync it to HubSpot.

    Args:
    - data (TicketRegister): Ticket data including customer email, issue details, priority, and generate datetime.
    - user (dict, Depends(admin_agent_required)): Current authenticated user (Admin or Agent).
    - db (Connection, Depends(access_db)): Database connection.

    Returns:
    - dict: Status message indicating success and HubSpot ticket ID.

    Raises:
    - HTTPException 404: If customer does not exist.
    - HTTPException 400: If HubSpot API call fails.
    - HTTPException 500: For unexpected errors.
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

                    query = '''insert into ticket(
                    issue_title,
                    issue_type,
                    issue_description,
                    priority,
                    generate_datetime,
                    ticket_status,
                    creater_emp_id,
                    customer_id,
                    hubspot_ticket_id
                    ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                    values = (data.issue_title,
                        data.issue_type,
                        data.issue_description,
                        data.priority.value,
                        data.generate_datetime,
                        "Open",
                        user["emp_id"],
                        customer["customer_id"],
                        hubspot_ticket_id)
                    cursor.execute(query,values)
                    ticket_id = cursor.lastrowid 
                    db.commit()

                    return {
                        "status": "success",
                        "message": "Ticket generated & synced to HubSpot"
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

@ticket_router.post("/ticket_registration_gform", tags=["Ticket"])
def ticket_registration_gform(data:TicketRegister,db = Depends(access_db)):
    """
    Register a new ticket submitted via Google Form or external source.

    This endpoint creates a ticket without requiring authentication.
    It is designed for external integrations (e.g., Google Forms),
    where tickets are created automatically for an existing customer.

    The ticket is:
    - Linked to the customer using email
    - Created with status set to 'Open'
    - Assigned a default creator employee ID

    Args:
        data (TicketRegister):
            Ticket details submitted from the external form.
        db:
            Database connection dependency.

    Returns:
        dict:
            - status_code: HTTP 201 when ticket is created
            - message: Confirmation message

    Raises:
        HTTPException:
            404 - If the customer email does not exist.
            500 - If a database or server error occurs.
    """
    try:
        with db:
            with db.cursor() as cursor:
                customer = cursor.execute("select customer_id from customer where customer_email = %s",(data.customer_email,))
                if customer:
                    customer = cursor.fetchone()
                    query = '''insert into ticket(
                    issue_title,
                    issue_type,
                    issue_description,
                    priority,
                    generate_datetime,
                    ticket_status,
                    creater_emp_id,
                    customer_id
                    ) values (%s,%s,%s,%s,%s,%s,%s,%s)'''
                    values = (data.issue_title,
                        data.issue_type,
                        data.issue_description,
                        data.priority.value,
                        data.generate_datetime,
                        "Open",
                        1,
                        customer["customer_id"])
                    cursor.execute(query,values)
                    db.commit()
                    return {"status_code":status.HTTP_201_CREATED, "message":"Ticket generated"}
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found",
                ) 
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )


@ticket_router.put("/update_ticket", tags=["Ticket"])
def update_ticket(data : TicketUpdate,user = Depends(get_current_user),db = Depends(access_db)):
    """
    Update an existing ticket and synchronize changes with HubSpot if applicable.

    This endpoint allows authorized users to update ticket details such as:
    - Issue type
    - Description
    - Priority
    - Status
    - Reason for update

    Behavior depends on the employee role:
    - Service Person (employee_type == 3):
        Can assign themselves and update all ticket fields.
    - Admin / Agent:
        Can update ticket fields except service person assignment.

    If the ticket is already synced with HubSpot:
    - Ticket status updates are propagated to HubSpot
    - Closing a ticket triggers HubSpot close action

    Args:
        data (TicketUpdate):
            Payload containing ticket update fields.
        user (dict):
            Authenticated user payload extracted from JWT.
        db:
            Database connection dependency.

    Returns:
        dict:
            - status_code: HTTP 202 when update is successful
            - message: Confirmation message

    Raises:
        HTTPException:
            404 - If ticket or employee does not exist.
            500 - If a database, HubSpot, or server error occurs.
    """
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select * from ticket where ticket_id = %s",(data.ticket_id,))
                ticket = cursor.fetchone()
                if ticket:
                    cursor.execute("select * from employee where employee_id = %s",(user["emp_id"],))
                    e = cursor.fetchone()
                    if e:
                        if e['employee_type']==3:
                            query = '''update ticket set 
                            service_person_emp_id = %s,
                            issue_type = %s,
                            issue_description = %s,
                            priority = %s,
                            reason = %s,
                            ticket_status = %s
                            where ticket_id = %s'''
                            values = (user["emp_id"],
                                      data.issue_type if data.issue_type else ticket['issue_type'],
                                      data.issue_description if data.issue_description else ticket['issue_description'],
                                      data.priority.value if data.priority.value else ticket['priority'],
                                      data.reason if data.reason else ticket['reason'],
                                      data.ticket_status.value if data.ticket_status.value else ticket['ticket_status'],
                                      data.ticket_id)
                                      
                        else:
                            query = '''update ticket set 
                            issue_type = %s,
                            issue_description = %s,
                            priority = %s,
                            reason = %s,
                            ticket_status = %s
                            where ticket_id = %s'''
                            values = (data.issue_type if data.issue_type else ticket['issue_type'],
                                      data.issue_description if data.issue_description else ticket['issue_description'],
                                      data.priority.value if data.priority else ticket['priority'],
                                      data.reason if data.reason else ticket['reason'],
                                      data.ticket_status.value if data.ticket_status.value else ticket['ticket_status'],
                                      data.ticket_id)
                        cursor.execute(query,values)
                        db.commit()
                        # 3️⃣ Update HubSpot ONLY if synced
                        if ticket["hubspot_ticket_id"]:
                            if data.ticket_status and data.ticket_status.value == "Close":
                                hubspot_close_ticket(ticket["hubspot_ticket_id"])

                            hubspot_update_ticket(
                                ticket["hubspot_ticket_id"],
                                data
                            )

                        return {
                            "status_code": status.HTTP_202_ACCEPTED,
                            "message": "Ticket updated & synced"
                        }

                        # return { 'status_code': status.HTTP_202_ACCEPTED, 'Message':"Ticket Updated!"}
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={
                            "message": "Employee not exist"
                        }
                    )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "message": "Ticket not exist"
                    }
                )
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )

@ticket_router.post("/ticket_analysis_per_emp", tags=["Ticket"])
def ticket_analysis_per_emp(emp_id:int,db = Depends(access_db)):
    """
    Get ticket statistics for a specific employee.

    This endpoint returns aggregated ticket counts based on the employee role:
    - Admin:
        Sees statistics for all tickets in the system.
    - Non-Admin (Agent / Service Person):
        Sees statistics only for tickets they created or are assigned to.

    The response includes counts for:
    - Total tickets
    - Open tickets
    - In-progress tickets
    - Closed tickets

    Args:
        emp_id (int):
            Employee ID for which ticket statistics are requested.
        db:
            Database connection dependency.

    Returns:
        dict:
            - total_ticket_count: Total number of relevant tickets
            - Opened_ticket_count: Count of tickets with status "Open"
            - in_progress_ticket_count: Count of tickets with status "In_Progress"
            - Closed_ticket_count: Count of tickets with status "Close"

    Raises:
        HTTPException:
            400 - If no tickets are found.
            500 - If a database or server error occurs.
    """
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select type_name from employee_type where employee_type_id =(select employee_type from employee where employee_id = %s)",(emp_id,))
                employee_type = cursor.fetchone()['type_name']
                if employee_type != "Admin":
                    total_ticket_count = cursor.execute("select * from ticket where creater_emp_id = %s or service_person_emp_id = %s",(emp_id,emp_id))
                    d = cursor.fetchall()
                else:
                    total_ticket_count = cursor.execute("select * from ticket")
                    d = cursor.fetchall()
                if d:
                    Opened_ticket_count = cursor.execute("select * from ticket where ticket_status = %s","Open")
                    in_progress_ticket_count = cursor.execute("select * from ticket where ticket_status = %s","In_Progress")
                    Closed_ticket_count = cursor.execute("select * from ticket where ticket_status = %s","Close")
                    return {
                        "total_ticket_count":total_ticket_count,
                        "Opened_ticket_count":Opened_ticket_count,
                        "in_progress_ticket_count":in_progress_ticket_count,
                        "Closed_ticket_count":Closed_ticket_count
                    }
                raise HTTPException(
                    status_code=400,
                    detail="Ticket not found"
                )
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )

@ticket_router.get("/my_tickets", tags=["Ticket"])
def my_tickets(user=Depends(get_current_user), db=Depends(access_db)):
    """
    Retrieve tickets assigned to the logged-in service person or agent.

    This endpoint returns all tickets where the current authenticated user
    is assigned as the service person (`service_person_emp_id`).

    Access is determined by the authenticated user's token.

    Args:
        user (dict):
            Authenticated user payload obtained from `get_current_user`.
            Must contain `emp_id`.
        db:
            Database connection dependency.

    Returns:
        list[dict]:
            A list of ticket records assigned to the logged-in user.
            Returns an empty list if no tickets are assigned.

    Raises:
        HTTPException:
            500 - If a database or server error occurs.
    """
    try:
        cursor = db.cursor()
        cursor.execute(
            "select * from ticket where service_person_emp_id=%s",
            (user["emp_id"],)
        )
        return cursor.fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@ticket_router.get("/customer_my_tickets", tags=["Ticket"])
def customer_my_tickets(user=Depends(customer_required), db=Depends(access_db)):
    """
    Retrieve all tickets created by the logged-in customer.

    This endpoint returns tickets associated with the authenticated customer
    based on their `customer_id`. Access is restricted to users authenticated
    as customers.

    Args:
        user (dict):
            Authenticated customer payload obtained from `customer_required`.
            Must contain `emp_id` representing the customer ID.
        db:
            Database connection dependency.

    Returns:
        list[dict]:
            A list of tickets created by the logged-in customer.
            Returns an empty list if no tickets are found.

    Raises:
        HTTPException:
            500 - If a database or server error occurs.
    """
    try:
        cursor = db.cursor()
        cursor.execute(
            "select * from ticket where customer_id=%s",
            (user["emp_id"],)
        )
        return cursor.fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

class FetchTicketsRequest(BaseModel):
    customer_email: str

@ticket_router.post("/fetch_tickets_by_customer", tags=["Ticket"])
def fetch_tickets_by_customer(data:FetchTicketsRequest,user=Depends(get_current_user), db=Depends(access_db)):
    """
    Fetch all tickets associated with a specific customer email.

    This endpoint:
        1. Accepts a customer email in the request body.
        2. Looks up the corresponding customer_id from the database.
        3. Retrieves all tickets linked to that customer_id.

    Request Body:
        FetchTicketsRequest:
            customer_email (str): Email address of the customer.

    Dependencies:
        user:
            Authenticated user injected via `get_current_user`.
            (Role-based restrictions should be enforced upstream if required.)
        db:
            Active database connection provided by `access_db`.

    Returns:
        list[dict]:
            A list of ticket records belonging to the customer.

        OR

        dict:
            {
                "message": "Customer not found"
            }
            If no customer exists with the given email.

    Database Flow:
        - Query 1: Fetch customer_id from `customer` table using customer_email.
        - Query 2: Fetch all records from `ticket` table using customer_id.

    Notes:
        - Email must exist in the `customer` table before ticket retrieval.
        - This endpoint does not apply filtering (status/priority).
        - Returns raw ticket records as stored in the database.
        - Authorization logic (e.g., Admin/Agent-only access) should be
          enforced before allowing cross-customer ticket access.
    """
    cursor = db.cursor()
    cursor.execute("select customer_id from customer where customer_email = %s",(data.customer_email,))

    customer = cursor.fetchone()
    
    if not customer:
        return {"message": "Customer not found"}

    customer_id = customer['customer_id']   # VERY IMPORTANT
    cursor.execute(
        "select * from ticket where customer_id=%s",
        (customer_id,)
    )
    return cursor.fetchall()



@ticket_router.get("/customer_ticket_messages/{ticket_id}", tags=["Ticket"])
def get_ticket_messages(
    ticket_id: int,
    user=Depends(admin_agent_customer_required),
    db=Depends(access_db)
):
    """
    Retrieve all messages for a specific ticket.

    This endpoint returns the message conversation (chat history) associated
    with a ticket. Access control is enforced based on the user's role:

    - Customer: Can only view messages for their own tickets.
    - Agent/Admin: Can view messages for any existing ticket.

    Args:
        ticket_id (int):
            Unique identifier of the ticket whose messages are being retrieved.
        user (dict):
            Authenticated user payload obtained from `admin_agent_customer_required`.
            Contains role information and user ID.
        db:
            Database connection dependency.

    Returns:
        list[dict]:
            A list of ticket messages ordered by creation time.
            Each message includes sender role, message content, and timestamp.

    Raises:
        HTTPException:
            403 - If a customer attempts to access a ticket they do not own.
            404 - If the ticket does not exist (Agent/Admin access).
            500 - If a server or database error occurs.
    """
    try:
        cursor = db.cursor()

        if user["role"] == "Customer":
            # customer can see only their ticket
            cursor.execute(
                "SELECT 1 FROM ticket WHERE ticket_id=%s AND customer_id=%s",
                (ticket_id, user["emp_id"])
            )
            if not cursor.fetchone():
                raise HTTPException(403, "Access denied")

        elif user["role"] == "Agent":
            # agent can see ticket
            cursor.execute(
                "SELECT 1 FROM ticket WHERE ticket_id=%s",
                (ticket_id,)
            )
            if not cursor.fetchone():
                raise HTTPException(404, "Ticket not found")

        cursor.execute("""
            SELECT sender_role, message, created_at
            FROM ticket_message
            WHERE ticket_id=%s
            ORDER BY created_at
        """, (ticket_id,))

        return cursor.fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@ticket_router.post("/customer_ticket_message/{ticket_id}", tags=["Ticket"])
def send_ticket_message(
    ticket_id: int,
    data: dict,
    user=Depends(customer_required),
    db=Depends(access_db)
):
    """
    Send a message from a customer to a ticket conversation.

    This endpoint allows an authenticated customer to post a message
    to the message thread of a specific ticket. The message is stored
    in the `ticket_message` table with the sender role marked as `Customer`.

    Args:
        ticket_id (int):
            Unique identifier of the ticket to which the message is being sent.
        data (dict):
            Request payload containing the message text.
            Expected format:
            {
                "message": "<message content>"
            }
        user (dict):
            Authenticated customer payload obtained from `customer_required`.
            Contains the customer ID.
        db:
            Database connection dependency.

    Returns:
        dict:
            Confirmation response indicating the message was sent successfully.

    Raises:
        HTTPException:
            500 - If a database or server error occurs while sending the message.
    """
    try:
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO ticket_message
            (ticket_id, sender_role, sender_id, message)
            VALUES (%s, 'Customer', %s, %s)
        """, (ticket_id, user["emp_id"], data["message"]))

        db.commit()
        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@ticket_router.post("/agent_ticket_message/{ticket_id}", tags=["Ticket"])
def agent_send_message(
    ticket_id: int,
    data: dict,
    user=Depends(admin_agent_required),   # Admin / Agent
    db=Depends(access_db)
):
    """
    Send a message from an agent or admin to a ticket conversation.

    This endpoint allows an authenticated Agent or Admin to post a
    message to a specific ticket’s message thread. The message is
    stored in the `ticket_message` table with the sender role marked
    as `Agent`.

    Args:
        ticket_id (int):
            Unique identifier of the ticket to which the message is sent.
        data (dict):
            Request payload containing the message text.
            Expected format:
            {
                "message": "<message content>"
            }
        user (dict):
            Authenticated user payload obtained from `admin_agent_required`.
            Contains the employee ID and role.
        db:
            Database connection dependency.

    Returns:
        dict:
            Confirmation response indicating the message was sent successfully.

    Raises:
        HTTPException:
            500 - If a database or server error occurs while sending the message.
    """
    try:
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO ticket_message
            (ticket_id, sender_role, sender_id, message)
            VALUES (%s, 'Agent', %s, %s)
        """, (ticket_id, user["emp_id"], data["message"]))

        db.commit()
        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@ticket_router.get("/agent_tickets", tags=["Ticket"])
def agent_tickets(
    user=Depends(admin_agent_required),
    db=Depends(access_db)
):
    """
    Retrieve all tickets with agent-facing response status.

    This endpoint returns a list of tickets ordered by creation time,
    enriched with metadata indicating whether an agent reply is needed.
    A ticket is marked as requiring a reply when the most recent message
    was sent by a customer.

    Access Control:
        - Admin
        - Agent

    Response Fields:
        - ticket_id: Unique identifier of the ticket
        - issue_title: Title/subject of the ticket
        - ticket_status: Current ticket status (Open, In_Progress, Close)
        - priority: Ticket priority (Low, Medium, High)
        - last_sender: Role of the last message sender (Customer / Agent)
        - needs_reply: Boolean flag indicating if agent action is required

    Args:
        user (dict):
            Authenticated Admin or Agent payload provided by
            `admin_agent_required`.
        db:
            Database connection dependency.

    Returns:
        list[dict]:
            List of ticket objects with reply-status metadata.

    Raises:
        HTTPException:
            500 - If a database or server error occurs while fetching tickets.
    """
    try:
        cursor = db.cursor()

        cursor.execute("""
            SELECT 
                t.ticket_id,
                t.issue_title,
                t.ticket_status,
                t.priority,

                (
                    SELECT sender_role
                    FROM ticket_message m
                    WHERE m.ticket_id = t.ticket_id
                    ORDER BY m.created_at DESC
                    LIMIT 1
                ) AS last_sender

            FROM ticket t
            ORDER BY t.generate_datetime DESC
        """)

        tickets = cursor.fetchall()

        for t in tickets:
            t["needs_reply"] = (t["last_sender"] == "Customer")

        return tickets
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

