from fastapi import status,Depends, HTTPException, APIRouter
from database.database import access_db
from Authentication.dependencies import admin_required, admin_agent_required
from pydantic import BaseModel
from Authentication.auth import create_access_token
from Hubspot.hubspot_contacts import sync_contact
from Hubspot.hubspot_contacts import fetch_contact_by_id
from Hubspot.hubspot_delete import delete_hubspot_object
from typing import Optional


customer_router = APIRouter()

class CustomerLogin(BaseModel):
    email_or_mobile : str



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

@customer_router.get("/all_customers", tags=["Customer"])
def fetch_all_customers(user=Depends(admin_agent_required),db = Depends(access_db)):
    """
    Fetch all customers from the database.

    This endpoint retrieves all records from the `customer` table.
    Access is restricted to admin and agent users via dependency injection.

    Dependencies:
    - admin_agent_required: Ensures the requester is an authenticated admin or agent.
    - access_db: Provides a database connection.

    Returns:
    - List[dict]: A list of customer records if customers exist.

    Raises:
    - HTTPException (404): If no customers are found in the database.
    - HTTPException (500): If any unexpected error occurs during database access.
    """
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
 
def sync_single_customer(customer_id: int):
    """
    Synchronize a single customer record with HubSpot.

    This function retrieves a customer from the local database using the
    provided `customer_id` and synchronizes the customer data with HubSpot
    via the `sync_contact` utility.

    Args:
    - customer_id (int): Unique identifier of the customer to be synchronized.

    Returns:
    - dict:
        - {"success": True} if the customer is successfully synchronized.
        - {"error": "Customer not found"} if no customer exists with the given ID.

    Raises:
    - HTTPException (500): If an unexpected error occurs during database access
      or synchronization with HubSpot.
    """

    try:
        db = access_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM customer WHERE customer_id = %s",
            (customer_id,)
        )
        customer = cursor.fetchone()

        if not customer:
            return {"error": "Customer not found"}

        sync_contact(customer, db)

        return {"success": True}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@customer_router.post("/customer_registration", tags=["Customer"])
def customer_registration(data:CustomerRegister,user=Depends(admin_agent_required),db = Depends(access_db)):
    """
    Register a new customer and synchronize with HubSpot.

    This endpoint allows an admin or agent to create a new customer record
    in the local database after validating email uniqueness and mobile
    number format. Upon successful creation, the customer is automatically
    synchronized with HubSpot.

    Dependencies:
    - admin_agent_required: Ensures the requester is an authenticated admin or agent.
    - access_db: Provides a database connection.

    Request Body:
    - CustomerRegister: Customer registration details including name, email,
      mobile number, company, and address information.

    Returns:
    - dict:
        - status_code (int): HTTP 201 status code.
        - message (str): Confirmation message for successful registration.

    Raises:
    - HTTPException (400): If the mobile number is invalid.
    - HTTPException (409): If the email already exists.
    - HTTPException (500): If an unexpected error occurs during registration
      or synchronization.
    """

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
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )


@customer_router.post("/customer_login", tags=["Customer"])
def customer_login(data: CustomerLogin, db=Depends(access_db)):
    """
    Authenticate a customer and issue an access token.

    This endpoint validates a customer using either email address or
    mobile number and returns a JWT access token upon successful
    authentication.

    Dependencies:
    - access_db: Provides a database connection.

    Request Body:
    - CustomerLogin: Contains an email address or mobile number for login.

    Returns:
    - dict:
        - access_token (str): JWT access token identifying the authenticated customer.

    Raises:
    - HTTPException (401): If the provided email or mobile number is invalid.
    """

    try:
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
    except Exception as e:
        return str(e)

class Update_customer(BaseModel):
    name : Optional[str] = None
    email : str | None = None
    mobile_number : str | None = None
    company_name : Optional[str] = None
    city : Optional[str] = None
    state : Optional[str] = None
    country : Optional[str] = None
    address : Optional[str] = None

@customer_router.put("/update_customer", tags=["Customer"])
def update_customer(data : Update_customer,user=Depends(admin_agent_required),db = Depends(access_db)):
    """
    Update an existing customer's details and synchronize with HubSpot.

    This endpoint allows an admin or agent to update customer information
    based on the customer's email address. Only provided (non-empty) fields
    are updated; missing or empty fields retain their existing values.
    After a successful update, the customer record is synchronized with
    HubSpot.

    Dependencies:
    - admin_agent_required: Ensures the requester is an authenticated admin or agent.
    - access_db: Provides a database connection.

    Request Body:
    - CustomerRegister: Customer details to update. The email field is used
      to identify the customer record.

    Returns:
    - dict:
        - message (str): Confirmation message indicating successful update
          and synchronization.

    Raises:
    - HTTPException (404): If no customer exists with the provided email.
    - HTTPException (500): If an unexpected error occurs during update or
      synchronization.
    """

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
                    values = (data.name if data.name != "" and data.name is not None else d['customer_name'],
                              data.mobile_number if data.mobile_number != "" and data.mobile_number is not None else d['customer_mobile_number'],
                              data.company_name if data.company_name != "" and data.company_name is not None else d['customer_company_name'],
                              data.city if data.city != "" and data.city is not None else d['customer_city'],
                              data.state if data.state != ""and data.state is not None else d['customer_state'],
                              data.country if data.country != "" and data.country is not None else d['customer_country'],
                              data.address if data.address != "" and data.address is not None else d['customer_address'],
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
                        sync_contact(customer,db)
                    except Exception as e:
                        pass
                    return {"message": "Customer updated & synced"}

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

@customer_router.delete("/remove_customer", tags=["Customer"])
def remove_customer(data : DeleteUser,user=Depends(admin_required),db = Depends(access_db)):
    """
    Delete a customer record from the system.

    This endpoint allows an authorized admin user to remove a customer
    from the database using the customer's email address. The operation
    is restricted based on the requesting employee's role; service
    persons are not permitted to delete customers.

    Dependencies:
    - admin_required: Ensures the requester is an authenticated admin.
    - access_db: Provides a database connection.

    Request Body:
    - DeleteUser: Contains the employee ID of the requester and the
      customer email to be deleted.

    Returns:
    - int: HTTP 200 status code if the customer is successfully deleted.

    Raises:
    - HTTPException (401): If the requester does not have permission
      to delete customers.
    - HTTPException (404): If the specified customer email does not exist.
    - HTTPException (500): If an unexpected error occurs during deletion.
    """

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


@customer_router.post("/sync-customer/{customer_id}", tags=["Customer"])
def sync_customer(customer_id: int,
    user=Depends(admin_agent_required)):
    """
    Synchronize a customer with HubSpot by customer ID.

    This endpoint triggers synchronization of a single customer record
    from the local database to HubSpot using the provided customer ID.

    Path Parameters:
    - customer_id (int): Unique identifier of the customer to be synchronized.

    Returns:
    - dict:
        - {"success": True} if the customer is successfully synchronized.
        - {"error": "Customer not found"} if the customer does not exist.

    Raises:
    - HTTPException (500): If an unexpected error occurs during synchronization.
    """

    return sync_single_customer(customer_id)


@customer_router.get("/hubspot/customer/{customer_id}", tags=["Customer"])
def get_customer_from_hubspot(
    customer_id: int,
    user=Depends(admin_agent_required),
    db=Depends(access_db)
):
    """
    Retrieve a customer record from HubSpot using the local customer ID.

    This endpoint fetches the HubSpot contact associated with a given
    local customer ID. It first looks up the HubSpot contact ID from
    the local database and then retrieves the corresponding contact
    details from HubSpot.

    Dependencies:
    - admin_agent_required: Ensures the requester is an authenticated admin or agent.
    - access_db: Provides a database connection.

    Path Parameters:
    - customer_id (int): Local customer ID used to locate the corresponding
      HubSpot contact.

    Returns:
    - dict: HubSpot contact data including standard and custom customer
      properties.

    Raises:
    - HTTPException (404): If the customer does not exist or is not synced
      with HubSpot.
    - HTTPException (500): If an unexpected error occurs during database
      access or HubSpot communication.
    """

    try:
        cursor = db.cursor()
        cursor.execute(
            "SELECT hubspot_contact_id FROM customer WHERE customer_id=%s",
            (customer_id,)
        )
        customer = cursor.fetchone()

        if not customer or not customer["hubspot_contact_id"]:
            raise HTTPException(404, "Customer not synced to HubSpot")

        return fetch_contact_by_id(customer["hubspot_contact_id"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e))


@customer_router.get("/hubspot/customer_email/{customer_email}", tags=["Customer"])
def get_customer_from_hubspot_by_email(
    customer_email: str,
    user=Depends(admin_agent_required),
    db=Depends(access_db)
):
    try:
        cursor = db.cursor()
        print(customer_email)
        cursor.execute(
            "SELECT hubspot_contact_id FROM customer WHERE customer_email=%s",
            (customer_email,)
        )
        customer = cursor.fetchone()

        if not customer or not customer["hubspot_contact_id"]:
            raise HTTPException(404, "Customer not synced to HubSpot")

        return fetch_contact_by_id(customer["hubspot_contact_id"])
    except Exception as e:
        return str(e)


@customer_router.get("/hubspot/customer-delete/{customer_id}", tags=["Customer"])
def delete_customer_from_hubspot(customer_id:int,db=Depends(access_db)):
    """
    Delete a customer from HubSpot using the local customer ID.

    This endpoint deletes a HubSpot contact associated with a given local
    customer ID. It first retrieves the HubSpot contact ID from the local
    database and then calls the HubSpot API to delete the contact.

    Dependencies:
    - access_db: Provides a database connection.

    Path Parameters:
    - customer_id (int): Local customer ID whose corresponding HubSpot
      contact will be deleted.

    Returns:
    - dict: Result of the HubSpot deletion operation, typically:
        - {"status": "success", "message": "Deleted successfully"} on success
        - {"status": "error", "status_code": int, "detail": str} on failure

    Raises:
    - HTTPException (400): If an error occurs during database access or
      deletion in HubSpot.
    """

    try:
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT hubspot_contact_id FROM customer WHERE customer_id=%s",
                (customer_id,)
            )
            hubspot_id = cursor.fetchone()
            if not hubspot_id or not hubspot_id.get("hubspot_contact_id"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not synced to HubSpot"
                )

            return delete_hubspot_object(object_type="contacts",object_id=hubspot_id['hubspot_contact_id'])
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete customer from HubSpot"
        )
