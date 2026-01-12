from fastapi import FastAPI, status,Depends, HTTPException
from fastapi.responses import JSONResponse
from database import access_db
from pydantic import BaseModel
import pymysql.cursors


    
class Login(BaseModel):
    email: str
    password: str

# class AgentRegister(BaseModel):
#     team_leader_email : str
#     name : str
#     email : str
#     mobile_number : str
#     password : str

# class ServicePersonRegister(BaseModel):
#     agent_email : str
#     name : str
#     email : str 
#     mobile_number : str 
#     password : str 
#     type : str 
#     city : str 
#     state : str 
#     country : str
class EmployeeRegister(BaseModel):
    your_email : str
    name : str
    email : str 
    mobile_number : str 
    password : str 
    type : str

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
    your_email : str
    email : str
app = FastAPI()

# -------------------------------------- Employee ----------------------------------------------
@app.post("/employee_registration")
def employee_registration(data:EmployeeRegister,db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select type_name from employee_type where employee_type_id =(select employee_type from employee where employee_email = %s)",(data.your_email,))
                senior_type = cursor.fetchone()['type_name']
                junior_type = data.type
                if senior_type == "Service Person":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You have not permit"
                    )
                elif senior_type == "Agent" and junior_type == "Admin":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You have not permit"
                    )
                elif senior_type == "Agent" and junior_type == "Agent":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You have not permit"
                    )
                
                cursor.execute("select * from employee where employee_email = %s",(data.email,))
                d = cursor.fetchone()
                if d:
                    raise HTTPException(
                        status_code = status.HTTP_409_CONFLICT,
                        detail="Email already exist"
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

@app.get("/all_employees")
def fetch_all_employees(db = Depends(access_db)):
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
    
@app.post("/employee_login")
def employee_login(data: Login,db = Depends(access_db)):
    try:
        c = db.cursor()
        c.execute("select employee_email,employee_password from employee where employee_email = %s",(data.email,))
        d = c.fetchone()
        if d is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email"
            )

        if data.password != d["employee_password"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )

        print("success")
        return {"message": "Login successful"}
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )

@app.put("/employee_update")
def update_employee(data : EmployeeRegister,db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select type_name from employee_type where employee_type_id =(select employee_type from employee where employee_email = %s)",(data.your_email,))
                senior_type = cursor.fetchone()['type_name']
                junior_type = data.type
                if senior_type == "Service Person":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You have not permit"
                    )
                elif senior_type == "Agent" and junior_type == "Admin":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You have not permit"
                    )
                elif senior_type == "Agent" and junior_type == "Agent":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You have not permit"
                    )
                
                cursor.execute("select employee_email from employee where employee_email = %s",(data.email,))
                d = cursor.fetchone()
                cursor.execute("select employee_type_id from employee_type where type_name=%s",(data.type,))
                type_id = cursor.fetchone()["employee_type_id"]
                if d:
                    cursor.execute("update employee set employee_name=%s,employee_mobile_number=%s,employee_password=%s,employee_type=%s where employee_email=%s",(data.name,data.mobile_number,data.password,type_id,data.email))
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
    
@app.delete("/employee_remove")
def remove_employee(data : DeleteUser,db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select type_name from employee_type where employee_type_id =(select employee_type from employee where employee_email = %s)",(data.your_email,))
                senior_type = cursor.fetchone()['type_name']
                cursor.execute("select type_name from employee_type where employee_type_id =(select employee_type from employee where employee_email = %s)",(data.email,))
                junior_type = cursor.fetchone()['type_name']
                if senior_type == "Service Person":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You have not permit"
                    )
                elif senior_type == "Agent" and junior_type == "Admin":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You have not permit"
                    )
                elif senior_type!="Admin" and senior_type == junior_type:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You have not permit"
                    )
                
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

@app.get("/all_customers")
def fetch_all_customers(db = Depends(access_db)):
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
    

@app.post("/customer_registration")
def customer_registration(data:CustomerRegister,db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select type_name from employee_type where employee_type_id =(select employee_type from employee where employee_email = %s)",(data.your_email,))
                employee_type = cursor.fetchone()['type_name']
                if employee_type == "Service Person":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You have not permit"
                    )
                agent = cursor.execute("select * from agent where agent_email = %s",(data.agent_email,))
                if agent:
                    cursor.execute("select * from customer where customer_email = %s",(data.email,))
                    d = cursor.fetchone()
                    if d:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Email already exist"
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
                else:
                    raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Agent not found",
                        )
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )


# @app.post("/customer_login")
# # def customer_login(data: Login,db = Depends(access_db)):
# #     try:
# #         c = db.cursor()
# #         c.execute("select customer_email,customer_password from customer where customer_email = %s",(data.email,))
# #         d = c.fetchone()
        
# #         if d is None:
# #             raise HTTPException(
# #                 status_code=status.HTTP_401_UNAUTHORIZED,
# #                 detail="Invalid email"
# #             )

# #         if data.password != d["customer_password"]:
# #             raise HTTPException(
# #                 status_code=status.HTTP_401_UNAUTHORIZED,
# #                 detail="Invalid password"
# #             )

# #         print("success")
# #         return {"message": "Login successful"}
# #     except Exception as e:
# #         return e

@app.put("/update_customer")
def update_customer(data : CustomerRegister,db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select type_name from employee_type where employee_type_id =(select employee_type from employee where employee_email = %s)",(data.your_email,))
                employee_type = cursor.fetchone()['type_name']
                if employee_type == "Service Person":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You have not permit"
                    )
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
                    raise HTTPException(
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

@app.delete("/remove_customer")
def remove_customer(data = DeleteUser,db = Depends(access_db)):
    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("select type_name from employee_type where employee_type_id =(select employee_type from employee where employee_email = %s)",(data.your_email,))
                senior_type = cursor.fetchone()['type_name']
                if senior_type == "Service Person":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="You have not permit"
                    )
                cursor.execute("select type_name from employee_type where employee_type_id =(select employee_type from employee where employee_email = %s)",(data.your_email,))
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

