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
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select * from ticket where ticket_id = %s",(data.ticket_id,))
                ticket = cursor.fetchone()
                # print("------------------ticket--------------",ticket)
                if ticket:
                    cursor.execute("select * from employee where employee_id = %s",(user["emp_id"],))
                    e = cursor.fetchone()
                    # print("------------------e--------------",e)
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
                                      data.priority.value if data.priority.value else ticket['priority'],
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
    cursor = db.cursor()
    cursor.execute(
        "select * from ticket where service_person_emp_id=%s",
        (user["emp_id"],)
    )
    return cursor.fetchall()
@ticket_router.get("/customer_my_tickets", tags=["Ticket"])
def customer_my_tickets(user=Depends(customer_required), db=Depends(access_db)):
    cursor = db.cursor()
    cursor.execute(
        "select * from ticket where customer_id=%s",
        (user["emp_id"],)
    )
    return cursor.fetchall()


@ticket_router.get("/profile", tags=["Ticket"])
def profile(user=Depends(get_current_user), db=Depends(access_db)):
    emp_id = user["emp_id"]

    cursor = db.cursor()
    cursor.execute(
        "select count(*) as total from ticket where service_person_emp_id=%s",
        (emp_id,)
    )
    total = cursor.fetchone()["total"]

    cursor.execute(
        "select count(*) as open from ticket where ticket_status='Open' and service_person_emp_id=%s",
        (emp_id,)
    )
    open_t = cursor.fetchone()["open"]

    cursor.execute(
        "select count(*) as closed from ticket where ticket_status='Close' and service_person_emp_id=%s",
        (emp_id,)
    )
    closed = cursor.fetchone()["closed"]

    return {
        "total": total,
        "open": open_t,
        "closed": closed
    }


@ticket_router.post("/logout", tags=["Logout"])
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    redis_client.delete(credentials.credentials)
    return {"message": "Logged out successfully"}

@ticket_router.get("/customer_ticket_messages/{ticket_id}", tags=["Ticket"])
def get_ticket_messages(
    ticket_id: int,
    user=Depends(admin_agent_customer_required),
    db=Depends(access_db)
):
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
        # agent can see ticket (optionally check assignment)
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


@ticket_router.post("/customer_ticket_message/{ticket_id}", tags=["Ticket"])
def send_ticket_message(
    ticket_id: int,
    data: dict,
    user=Depends(customer_required),
    db=Depends(access_db)
):
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO ticket_message
        (ticket_id, sender_role, sender_id, message)
        VALUES (%s, 'Customer', %s, %s)
    """, (ticket_id, user["emp_id"], data["message"]))

    db.commit()
    return {"status": "sent"}


@ticket_router.post("/agent_ticket_message/{ticket_id}", tags=["Ticket"])
def agent_send_message(
    ticket_id: int,
    data: dict,
    user=Depends(admin_agent_required),   # Admin / Agent
    db=Depends(access_db)
):
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO ticket_message
        (ticket_id, sender_role, sender_id, message)
        VALUES (%s, 'Agent', %s, %s)
    """, (ticket_id, user["emp_id"], data["message"]))

    db.commit()
    return {"status": "sent"}


@ticket_router.get("/agent_tickets", tags=["Ticket"])
def agent_tickets(
    user=Depends(admin_agent_required),
    db=Depends(access_db)
):
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

