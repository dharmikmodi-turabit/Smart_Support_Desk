from fastapi import FastAPI, status,Depends, HTTPException
from fastapi.responses import JSONResponse
from database import access_db
from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime
from auth import create_access_token
from redis_client import redis_client
from dependencies import get_current_user,admin_required, admin_agent_required, HTTPAuthorizationCredentials, security, customer_required, employee_create_permission,admin_agent_customer_required
from fastapi.security import HTTPAuthorizationCredentials
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from admin import router
import os
from customer_sync import sync_single_customer
from hubspot_contacts import sync_contact

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

env_path = os.path.join(BASE_DIR, ".env")
# print("ENV PATH:", env_path)
# print("ENV EXISTS:", os.path.exists(env_path))
# print("RAW HUBSPOT_TOKEN =", repr(os.getenv("HUBSPOT_TOKEN")))

app = FastAPI(title="Smart Support Desk")


app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


    
class Login(BaseModel):
    email: str
    password: str

class CustomerLogin(BaseModel):
    email_or_mobile : str

class UserRole(str, Enum):
    Admin = "Admin"
    Agent = "Agent"
    service_person = "Service Person"

class EmployeeRegister(BaseModel):
    name : str | None
    email : str | None
    mobile_number : str | None 
    password : str | None
    type : UserRole

class CustomerRegister(BaseModel):
    name : str
    email : str
    mobile_number : str
    company_name : str
    city : str
    state : str
    country : str
    address : str

class DeleteUser(BaseModel):
    email : str

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


# -------------------------------------- Employee ----------------------------------------------
@app.post("/employee_registration", tags=["Employee"])
def employee_registration(
    data: EmployeeRegister,
    user=Depends(employee_create_permission),
    db=Depends(access_db)
):
    creator_role = user["role"]

    # AGENT RESTRICTION
    if creator_role == "Agent" and data.type != UserRole.service_person:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent can only register Service Person"
        )

    # ADMIN CAN REGISTER ANY
    if creator_role == "Admin":
        pass

    # SERVICE PERSON BLOCKED ALREADY BY DEPENDENCY

    # ---- EXISTING LOGIC ----
    with db:
        with db.cursor() as cursor:
            cursor.execute(
                "select 1 from employee where employee_email=%s",
                (data.email,)
            )
            if cursor.fetchone():
                raise HTTPException(409, "Email already exists")

            cursor.execute(
                "select employee_type_id from employee_type where type_name=%s",
                (data.type.value,)
            )
            type_id = cursor.fetchone()["employee_type_id"]

            cursor.execute(
                """insert into employee
                (employee_name, employee_email, employee_mobile_number,
                 employee_password, employee_type)
                values (%s,%s,%s,%s,%s)""",
                (data.name, data.email, data.mobile_number, data.password, type_id)
            )
            db.commit()

    return {"message": "Employee registered successfully"}

@app.get("/all_employees", tags=["Employee"])
def fetch_all_employees(user=Depends(admin_required),db = Depends(access_db)):
    with db:
        with db.cursor() as cursor:
            employees = cursor.execute("select * from employee")
            if employees:
                d = cursor.fetchall()
                return d
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee not found"
                )
    

@app.post("/employee_login", tags=["Employee"])
def employee_login(data: Login, db=Depends(access_db)):
    try:
        c = db.cursor()
        c.execute("""
                SELECT 
                    e.employee_id,
                    e.employee_email,
                    e.employee_password,
                    et.type_name as employee_type
                FROM employee e
                JOIN employee_type et
                    ON e.employee_type = et.employee_type_id
                WHERE e.employee_email = %s
            """, (data.email,))
        user = c.fetchone()

        if not user or user["employee_password"] != data.password:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token_data = {
            "emp_id": user["employee_id"],
            "role": user["employee_type"]
        }

        token = create_access_token(token_data)

        # store token in redis
        redis_client.setex(token, 1800, user["employee_id"])

        return {
            "access_token": token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )

@app.put("/employee_update", tags=["Employee"])
def update_employee(data : EmployeeRegister,user=Depends(admin_required),db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select * from employee where employee_email = %s",(data.email,))
                d = cursor.fetchone()
                cursor.execute("select employee_type_id from employee_type where type_name=%s",(data.type,))
                type_id = cursor.fetchone()["employee_type_id"]
                if d:
                    values = (
                        data.name if data.name != "" else d['employee_name'],
                        data.mobile_number if data.mobile_number != "" else d['employee_mobile_number'],
                        data.password if data.password != "" else d['employee_password'],
                        type_id if data.type != "" else d['employee_type'],
                        data.email if data.email != "" else d['employee_email'])
                    cursor.execute("update employee set employee_name=%s,employee_mobile_number=%s,employee_password=%s,employee_type=%s where employee_email=%s",values)
                    db.commit()
                    return status.HTTP_202_ACCEPTED
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "message": "Email not exist",
                        "success": False
                    }
                )
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )
    
@app.delete("/employee_remove", tags=["Employee"])
def remove_employee(data : DeleteUser,user=Depends(admin_required),db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select employee_email from employee where employee_email = %s",(data.email,))
                d = cursor.fetchone()
                if d:
                    cursor.execute("delete from employee where employee_email = %s",(data.email,))
                    db.commit()
                    return status.HTTP_200_OK
                raise HTTPException(
                    status_code=404,
                    detail="Email not exist"
                )
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )



# -------------------------------------- Customer ----------------------------------------------

@app.get("/all_customers", tags=["Customer"])
def fetch_all_customers(user=Depends(admin_agent_required),db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select * from customer")
                d = cursor.fetchall()
                if d:
                    return d
                else:
                    raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Customer not found"
                        )
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )
    

@app.post("/customer_registration", tags=["Customer"])
def customer_registration(data:CustomerRegister,user=Depends(admin_agent_required),db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select * from customer where customer_email = %s",(data.email,))
                d = cursor.fetchone()
                if d:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Email already exist"
                    )
                if len(data.mobile_number) != 10:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Mobile Number is not valid"
                    )
                    
                query = '''insert into customer(
                customer_name, 
                customer_email, 
                customer_mobile_number, 
                customer_company_name, 
                customer_city, 
                customer_state, 
                customer_country, 
                customer_address
                ) values (%s,%s,%s,%s,%s,%s,%s,%s)'''
                values = (data.name,
                          data.email,
                          data.mobile_number,
                          data.company_name,
                          data.city,
                          data.state,
                          data.country,
                          data.address)
                cursor.execute(query,values)
                db.commit()
                customer_id = cursor.lastrowid
                sync_single_customer(customer_id)

                return {"status_code":status.HTTP_201_CREATED, "message":"Customer registered"}
    except Exception as e:
        print(e)
        print(str(e))
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )

# @app.post("/customer_login", tags=["Customer"])
# def customer_login(data : CustomerLogin,db = Depends(access_db)):
#     try:
#         c = db.cursor()
#         c.execute("""
#                 SELECT 
#                     customer_id,
#                     customer_email
#                 FROM customer
#                 WHERE customer_email = %s 
#                   OR customer_mobile_number = %s
#             """, (data.email_or_mobile,data.email_or_mobile))
#         user = c.fetchone()
#         if not user:
#             raise HTTPException(status_code=401, detail="Customer not registered")
#         return user

#     except Exception as e:
#         raise HTTPException(
#         status_code=500,
#         detail=str(e)
#     )

@app.post("/customer_login")
def customer_login(data: CustomerLogin, db=Depends(access_db)):
    cursor = db.cursor()
    cursor.execute("""
        select customer_id, customer_email
        from customer
        where customer_email=%s or customer_mobile_number=%s
    """, (data.email_or_mobile, data.email_or_mobile))

    customer = cursor.fetchone()
    if not customer:
        raise HTTPException(401, "Invalid customer")

    return {"access_token": create_access_token({
        "emp_id": customer["customer_id"],
        "role": "Customer"
    })}


@app.put("/update_customer", tags=["Customer"])
def update_customer(data : CustomerRegister,user=Depends(admin_agent_required),db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select * from customer where customer_email = %s",(data.email,))
                d = cursor.fetchone()
                if d:
                    query = '''update customer set 
                    customer_name = %s,
                    customer_mobile_number = %s, 
                    customer_company_name = %s, 
                    customer_city = %s, 
                    customer_state = %s, 
                    customer_country = %s, 
                    customer_address = %s 
                    where customer_email = %s'''
                    values = (data.name if data.name != "" else d['customer_name'],
                              data.mobile_number if data.mobile_number != "" else d['customer_mobile_number'],
                              data.company_name if data.company_name != "" else d['customer_company_name'],
                              data.city if data.city != "" else d['customer_city'],
                              data.state if data.state != "" else d['customer_state'],
                              data.country if data.country != "" else d['customer_country'],
                              data.address if data.address != "" else d['customer_address'],
                              data.email)
                    cursor.execute(query,values)
                    db.commit()
                    # 🔥 Fetch updated row
                    cursor.execute(
                        "SELECT * FROM customer WHERE customer_id = %s",
                        (d['customer_id'],)
                    )
                    customer = cursor.fetchone()

                    # 🔥 Sync HubSpot (safe)
                    try:
                        sync_contact(customer)
                    except Exception as e:
                        print("HubSpot update failed:", e)

                    return {"message": "Customer updated & synced"}

                    # return HTTPException(
                    #     status_code=status.HTTP_202_ACCEPTED,
                    #     detail={"Message":"Customer Updated!"}
                    #     )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "message": "Email not exist",
                        "success": False
                    }
                )
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail="dharmik"+str(e)
    )

@app.delete("/remove_customer", tags=["Customer"])
def remove_customer(data = DeleteUser,user=Depends(admin_required),db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select type_name from employee_type where employee_type_id =(select employee_type from employee where employee_id = %s)",(data.emp_id,))
                employee_type = cursor.fetchone()['type_name']
                if employee_type == "Service Person":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You have not permit"
                    )
                cursor.execute("select customer_email from customer where customer_email = %s",(data.email,))
                d = cursor.fetchone()
                if d:
                    cursor.execute("delete from customer where customer_email = %s",(data.email))
                    db.commit()
                    return status.HTTP_200_OK
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Email not exist"
                )
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )



# -------------------------------------- Ticket ----------------------------------------------

@app.get("/all_tickets", tags=["Ticket"])
def fetch_all_tickets(user=Depends(admin_agent_required),db = Depends(access_db)):
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
    
@app.post("/ticket_registration", tags=["Ticket"])
def ticket_registration(data:TicketRegister,user=Depends(admin_agent_required),db = Depends(access_db)):
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
                        user["emp_id"],
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
@app.post("/ticket_registration_gform", tags=["Ticket"])
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


@app.put("/update_ticket", tags=["Ticket"])
def update_ticket(data : TicketUpdate,user = Depends(get_current_user),db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select * from ticket where ticket_id = %s",(data.ticket_id,))
                d = cursor.fetchone()
                if d:
                    cursor.execute("select employee_type from employee where employee_id = %s",(user["emp_id"],))
                    e = cursor.fetchone()
                    if e:
                        query = '''update ticket set 
                        service_person_emp_id = %s,
                        issue_type = %s,
                        issue_description = %s,
                        priority = %s,
                        reason = %s,
                        ticket_status = %s
                        where ticket_id = %s'''
                        values = (user["emp_id"],
                                  data.issue_type if data.issue_type else d['issue_type'],
                                  data.issue_description if data.issue_description else d['issue_description'],
                                  data.priority.value if data.priority.value else d['priority'],
                                  data.reason if data.reason else d['reason'],
                                  data.ticket_status.value if data.ticket_status.value else d['ticket_status'],
                                  data.ticket_id)
                        cursor.execute(query,values)
                        db.commit()
                        return { 'status_code': status.HTTP_202_ACCEPTED, 'Message':"Ticket Updated!"}
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

@app.post("/ticket_analysis_per_emp", tags=["Ticket"])
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

@app.get("/my_tickets")
def my_tickets(user=Depends(get_current_user), db=Depends(access_db)):
    cursor = db.cursor()
    cursor.execute(
        "select * from ticket where service_person_emp_id=%s",
        (user["emp_id"],)
    )
    return cursor.fetchall()
@app.get("/customer_my_tickets")
def customer_my_tickets(user=Depends(customer_required), db=Depends(access_db)):
    cursor = db.cursor()
    cursor.execute(
        "select * from ticket where customer_id=%s",
        (user["emp_id"],)
    )
    return cursor.fetchall()


@app.get("/profile")
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


@app.post("/logout", tags=["Logout"])
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    redis_client.delete(credentials.credentials)
    return {"message": "Logged out successfully"}

@app.get("/customer_ticket_messages/{ticket_id}")
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


@app.post("/customer_ticket_message/{ticket_id}")
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


@app.post("/agent_ticket_message/{ticket_id}")
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
@app.get("/agent_tickets")
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
