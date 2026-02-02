from fastapi import status,Depends, HTTPException, APIRouter
from database import access_db
from dependencies import admin_required, admin_agent_required
from pydantic import BaseModel
from auth import create_access_token
from hubspot_contacts import sync_contact
from hubspot_contacts import fetch_contact_by_id
from hubspot_delete import delete_hubspot_object

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
        return e


@customer_router.post("/customer_registration", tags=["Customer"])
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


@customer_router.post("/customer_login", tags=["Customer"])
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


@customer_router.put("/update_customer", tags=["Customer"])
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
                        sync_contact(customer,db)
                    except Exception as e:
                        print("HubSpot update failed:", e)

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
        detail="dharmik"+str(e)
    )

@customer_router.delete("/remove_customer", tags=["Customer"])
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


@customer_router.post("/sync-customer/{customer_id}", tags=["Customer"])
def sync_customer(customer_id: int):
    return sync_single_customer(customer_id)


@customer_router.get("/hubspot/customer/{customer_id}", tags=["Customer"])
def get_customer_from_hubspot(
    customer_id: int,
    user=Depends(admin_agent_required),
    db=Depends(access_db)
):
    cursor = db.cursor()
    cursor.execute(
        "SELECT hubspot_contact_id FROM customer WHERE customer_id=%s",
        (customer_id,)
    )
    customer = cursor.fetchone()

    if not customer or not customer["hubspot_contact_id"]:
        raise HTTPException(404, "Customer not synced to HubSpot")

    return fetch_contact_by_id(customer["hubspot_contact_id"])

@customer_router.get("/hubspot/customer-delete/{customer_id}", tags=["Customer"])
def delete_customer_from_hubspot(customer_id:int,db=Depends(access_db)):
    try:
        cursor = db.cursor()
        cursor.execute(
            "SELECT hubspot_contact_id FROM customer WHERE customer_id=%s",
            (customer_id,)
        )
        hubspot_id = cursor.fetchone()
        return delete_hubspot_object(object_type="contacts",object_id=hubspot_id['hubspot_contact_id'])
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=e
        )
