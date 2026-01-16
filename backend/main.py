from fastapi import FastAPI, status,Depends, HTTPException
from fastapi.responses import JSONResponse
from database import access_db
from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime
from auth import create_access_token
from redis_client import redis_client
from dependencies import get_current_user,admin_required, admin_agent_required, HTTPAuthorizationCredentials, security
from fastapi.security import HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os

load_dotenv()

    
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
    service_person_emp_id : int
    issue_type : Optional[str] = None 
    issue_description : Optional[str] = None 
    priority : Optional[TicketPriority] = None 
    reason : Optional[str] = None
    ticket_status : Optional[TicketStatus] = None

app = FastAPI()

# -------------------------------------- Employee ----------------------------------------------
@app.post("/employee_registration", tags=["Employee"])
def employee_registration(data:EmployeeRegister,user=Depends(admin_required),db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select * from employee where employee_email = %s",(data.email,))
                d = cursor.fetchone()
                if d:
                    raise HTTPException(
                        status_code = status.HTTP_409_CONFLICT,
                        detail="Email already exist"
                    )
                if len(data.mobile_number) != 10:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Mobile Number is not valid"
                    )
                cursor.execute("select employee_type_id from employee_type where type_name=%s",(data.type,))
                type_id = cursor.fetchone()["employee_type_id"]
                query = '''
                        insert into employee(
                        employee_name, 
                        employee_email, 
                        employee_mobile_number, 
                        employee_password, 
                        employee_type
                        ) values (%s,%s,%s,%s,%s)
                    '''
                values = (data.name,data.email,data.mobile_number,data.password,type_id)
                cursor.execute(query,values)
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_201_CREATED,
                    detail="Employee registered"
                )
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )

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
        print(user)

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
                        data.name if data.name is not None else d['employee_name'],
                        data.mobile_number if data.mobile_number is not None else d['employee_mobile_number'],
                        data.password if data.password is not None else d['employee_password'],
                        type_id if data.type is not None else d['employee_type'],
                        data.email if data.email is not None else d['employee_email'])
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



# -------------------------------------- customer ----------------------------------------------

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
                return {"status_code":status.HTTP_201_CREATED, "message":"Customer registered"}
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )

@app.post("/customer_login", tags=["Customer"])
def customer_login(data : CustomerLogin,db = Depends(access_db)):
    try:
        c = db.cursor()
        c.execute("""
                SELECT 
                    customer_id,
                    customer_email
                FROM customer
                WHERE customer_email = %s 
                  OR customer_mobile_number = %s
            """, (data.email_or_mobile,data.email_or_mobile))
        user = c.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Customer not registered")
        return user

    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )


@app.put("/update_customer", tags=["Customer"])
def update_customer(data : CustomerRegister,user=Depends(admin_agent_required),db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select customer_email from customer where customer_email = %s",(data.email,))
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
                    values = (data.name,
                              data.mobile_number,
                              data.company_name,
                              data.city,
                              data.state,
                              data.country,
                              data.address,
                              data.email)
                    cursor.execute(query,values)
                    print(1)
                    db.commit()
                    return HTTPException(
                        status_code=status.HTTP_202_ACCEPTED,
                        detail={"Message":"Customer Updated!"}
                        )
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
def fetch_all_tickets(user=Depends(admin_required),db = Depends(access_db)):
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
                        data.priority,
                        data.generate_datetime,
                        "Open",
                        data.creater_emp_id,
                        customer)
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
def update_ticket(data : TicketUpdate,db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select * from ticket where ticket_id = %s",(data.ticket_id,))
                d = cursor.fetchone()
                if d:
                    cursor.execute("select employee_type from employee where employee_id = %s",(data.service_person_emp_id,))
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
                        values = (data.service_person_emp_id,
                                  data.issue_type if data.issue_type else d['issue_type'],
                                  data.issue_description if data.issue_description else d['issue_description'],
                                  data.priority if data.priority else d['priority'],
                                  data.reason if data.reason else d['reason'],
                                  data.ticket_status if data.ticket_status else d['ticket_status'],
                                  data.ticket_id)
                        cursor.execute(query,(values))
                        db.commit()
                        raise HTTPException(
                            status_code=status.HTTP_202_ACCEPTED,
                            detail={"Message":"Ticket Updated!"}
                            )
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={
                            "message": "Employee not exist",
                            "success": False
                        }
                    )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "message": "Ticket not exist",
                        "success": False
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
                    print(Opened_ticket_count)
                    print(in_progress_ticket_count)
                    print(Closed_ticket_count)
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


@app.post("/logout", tags=["Logout"])
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    redis_client.delete(credentials.credentials)
    return {"message": "Logged out successfully"}


