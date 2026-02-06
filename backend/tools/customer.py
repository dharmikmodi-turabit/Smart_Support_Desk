# from langchain.tools import tool
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.messages import ToolMessage, HumanMessage,AIMessage
# import requests
# from dependencies import Depends, admin_agent_required
# from fastapi import status, APIRouter
# from fastapi.exceptions import HTTPException
from database import access_db
from pydantic import BaseModel

# # ai_crm_router = APIRouter()
# API_BASE_URL = "http://192.168.1.32:8000"
# @tool
# def fetch_all_customers():
#     '''Fetch all customers from the database'''
#     try:
#         # db = access_db()
#         # with db:
#         #     with db.cursor() as cursor:
#         #         cursor.execute("select * from customer")
#         #         d = cursor.fetchall()
#         #         if d:
#         #             return d
#         #         else:
#         #             # raise HTTPException(
#         #             #         status_code=status.HTTP_404_NOT_FOUND,
#         #             #         detail="Customer not found"
#         #             #     )
#         #             return "Customer not found"
#         # user = admin_agent_required()
#         # print(user)
#         response = requests.get(
#             f"{API_BASE_URL}/all_customers",
#             # json=payload,
#             timeout=10
#         )

#         print(response)
#         if response.status_code != 200:
#             return {
#                 "error": True,
#                 "status_code": response.status_code,
#                 "detail": response.text
#             }

#         return response.json()
#     except Exception as e:
#            return str(e)


class Fetch_all_customer(BaseModel):
    token : str

from langchain.tools import tool
import requests

API_BASE_URL = "http://127.0.0.1:8000"

# @tool
# def fetch_all_customers(token:str) -> dict:
#     """
#     Fetch all customers from the database
#     Authentication is handled internally.
#     # If the LLM passed an empty string, fallback to the token injected from the FastAPI request context

#     """
#     # actual_token = token or context_stored_token

#     try:
#         # print("****************** tool activated ",token)
#         print("12345678")
#         response = requests.get(
#             f"{API_BASE_URL}/all_customers",
#             headers={
#                 "Authorization": token
#             },
#             timeout=10
#         )
#         # response.raise_for_status()
#         # return response.json()

#         # if response.status_code == 401:
#         #     return {
#         #         "success": False,
#         #         "message": "You are not authorized to view customer data"
#         #     }

#         # if response.status_code != 200:
#         #     return {
#         #         "success": False,
#         #         "message": "Failed to retrieve customers"
#         #     }


#         return {
#             "success": True,
#             "data": response.json()
#         }

#     except requests.exceptions.Timeout:
#         return {
#             "success": False,
#             "message": "The request took too long to respond"
#         }


@tool("fetch_all_customers",args_schema=Fetch_all_customer)
def fetch_all_customers(token:str) -> list[dict]:
    """Fetch all customers from the database"""
    print("Hello===============",token)
    response = requests.get(
        f"{API_BASE_URL}/all_customers",
        headers={
                "Authorization": f"Bearer {token}"
            }
    )
    response.raise_for_status() 
    print(response.json())
    return response.json()
