
from database import access_db
from pydantic import BaseModel, ValidationError
from langchain.tools import tool
from typing import Optional
import requests

API_BASE_URL = "http://127.0.0.1:8000"

class Fetch_all_customer(BaseModel):
    token : str | None = None

class Fetch_customer_by_email(BaseModel):
    token : str | None = None
    email : str

class Create_customer(BaseModel):
    name : str | None = None
    email : str | None = None
    mobile_number : str | None = None
    company_name : str | None = None
    city : str | None = None
    state : str | None = None
    country : str | None = None
    address : str | None = None

class Update_customer(BaseModel):
    name : Optional[str] = None
    email : str | None = None
    company_name : Optional[str] = None
    city : Optional[str] = None
    state : Optional[str] = None
    country : Optional[str] = None
    address : Optional[str] = None
    token : str | None = None




@tool("fetch_all_customers",args_schema=Fetch_all_customer)
def fetch_all_customers(token:str) -> list[dict]:
    """
    Fetch all customers from the database
    if user mention specification to fetch then fetch by that field or specification else fetch all customers
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/all_customers",
            headers={
                    "Authorization": f"Bearer {token}"
                }
        )

        return response.json()
    except Exception as e:
        return str(e)

@tool("fetch_customer_email",args_schema=Fetch_customer_by_email)
def fetch_customer_by_email(token:str,email:str) -> list[dict]:
    """
    Fetch customer by email from the hubspot,
    email is mandotory for fetch customer .
    """
    print("Hello===============",token)
    print("email---------------",email)
    response = requests.get(
        f"{API_BASE_URL}/hubspot/customer_email/{email}",
        headers={
                "Authorization": f"Bearer {token}"
            }
    )
    print(response.json()['properties'])
    return [response.json()['properties']]




@tool("create_customer", args_schema=Create_customer)
def create_customer(
    name: str,
    email: str,
    mobile_number: str,
    company_name: str,
    city: str,
    state: str,
    country: str,
    address: str,
    token: str   # backend injected
) -> dict:
    """
    Create a new customer in the CRM system.
    Requires Admin or Agent authorization.
    All fields are mandatory.
    """
    try:
        payload = {
                "name": name,
                "email": email,
                "mobile_number": mobile_number,
                "company_name": company_name,
                "city": city,
                "state": state,
                "country": country,
                "address": address,
            }


        response = requests.post(
            f"{API_BASE_URL}/customer_registration",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        print("+++++++++++ response +++++++++++",response.json())
        return response.json()

    except KeyError as e:
        return {
            "error": "Missing required field",
            "required_fields": [
                "token", "name", "email", "mobile_number",
                "company_name", "city", "state", "country", "address"
            ],
            "missing_field": str(e)
        }

    except ValidationError as e:
        return {
            "error": "Invalid input data",
            "details": e.errors()
        }


@tool("update_customer", args_schema=Update_customer)
def update_customer(
    token: str,   # backend injected
    email: str,
    **kwargs,
) -> dict:
    """
    Update existing customer in the system and Database.
    Requires Admin or Agent authorization.
    All fields are not mandatory but email and token is compulsory.
    """
    try:
        
        payload = {"email": email}

        for k, v in kwargs.items():
            if v not in (None, "", []):
                payload[k] = v
        print("????????? payload ??????????",payload)

        response = requests.put(
            f"{API_BASE_URL}/update_customer",
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
                "token", "name", "email", "mobile_number",
                "company_name", "city", "state", "country", "address"
            ],
            "missing_field": str(e)
        }

    except ValidationError as e:
        return {
            "error": "Invalid input data",
            "details": e.errors()
        }
