from fastapi import status,Depends, HTTPException, APIRouter
from database.database import access_db
from Authentication.dependencies import admin_required, employee_create_permission
from pydantic import BaseModel
from enum import Enum
from Authentication.auth import create_access_token
from Authentication.redis_client import redis_client

employee_router = APIRouter()


class Login(BaseModel):
    email: str
    password: str

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

class DeleteUser(BaseModel):
    email : str





@employee_router.post("/employee_registration", tags=["Employee"])
def employee_registration(
    data: EmployeeRegister,
    user=Depends(employee_create_permission),
    db=Depends(access_db)
):
    """
    Register a new employee in the system.

    This endpoint allows Admins or Agents (with restrictions) to create
    a new employee record. Agents can only register Service Persons.
    The employee's type, email, password, and other details are stored
    in the database.

    Args:
    - data (EmployeeRegister): Employee registration details.
    - user (dict, Depends): Current authenticated user (Admin or Agent).
    - db (Connection, Depends): Database connection.

    Returns:
    - dict: Success message.

    Raises:
    - HTTPException (403): If an Agent tries to register a role other than Service Person.
    - HTTPException (409): If the employee email already exists.
    - HTTPException (500): If an unexpected error occurs.
    """

    try:
        creator_role = user["role"]

        # AGENT RESTRICTION
        if user["role"] == "Agent" and data.type != UserRole.service_person:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agent can only register Service Person"
            )


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
    except Exception as e:
        return str(e)

@employee_router.get("/all_employees", tags=["Employee"])
def fetch_all_employees(user=Depends(admin_required),db = Depends(access_db)):
    """
    Fetch all employees from the database.

    Only Admin users can access this endpoint.

    Args:
    - user (dict, Depends): Current authenticated Admin user.
    - db (Connection, Depends): Database connection.

    Returns:
    - list[dict]: List of employee records.

    Raises:
    - HTTPException (404): If no employees are found.
    """

    try:
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
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )
    

@employee_router.post("/employee_login", tags=["Employee"])
def employee_login(data: Login, db=Depends(access_db)):
    """
    Authenticate an employee and return a JWT access token.

    This endpoint validates employee credentials (email and password),
    generates a JWT token, and stores it in Redis for session management.

    Args:
    - data (Login): Employee login credentials.
    - db (Connection, Depends): Database connection.

    Returns:
    - dict: {
        "access_token": str,
        "token_type": "bearer"
    }

    Raises:
    - HTTPException (401): If credentials are invalid.
    - HTTPException (500): If an unexpected error occurs.
    """

    try:
        with db:
            with db.cursor() as cursor:
                cursor.execute("""
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
                user = cursor.fetchone()

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
                    "token_type": "bearer",
                    "emp_id": user["employee_id"],
                    "role": user["employee_type"]
                }
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )

@employee_router.put("/employee_update", tags=["Employee"])
def update_employee(data : EmployeeRegister,user=Depends(admin_required),db = Depends(access_db)):
    """
    Update an existing employee's information.

    Only Admin users can update employee records. Fields that are left
    empty in the request will retain their current values.

    Args:
    - data (EmployeeRegister): Employee details to update.
    - user (dict, Depends): Current authenticated Admin user.
    - db (Connection, Depends): Database connection.

    Returns:
    - HTTP 202 Accepted on successful update.

    Raises:
    - HTTPException (404): If the employee email does not exist.
    - HTTPException (500): If an unexpected error occurs.
    """

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
    
@employee_router.delete("/employee_remove", tags=["Employee"])
def remove_employee(data : DeleteUser,user=Depends(admin_required),db = Depends(access_db)):
    """
    Delete an employee from the system.

    Only Admin users can remove employees. The endpoint checks if the
    employee exists before deletion.

    Args:
    - data (DeleteUser): Email of the employee to delete.
    - user (dict, Depends): Current authenticated Admin user.
    - db (Connection, Depends): Database connection.

    Returns:
    - HTTP 200 OK on successful deletion.

    Raises:
    - HTTPException (404): If the employee email does not exist.
    - HTTPException (500): If an unexpected error occurs.
    """

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

