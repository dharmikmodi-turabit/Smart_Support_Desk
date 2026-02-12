from fastapi import FastAPI, Depends
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os
from hubspot_tickets import hubspot_ticket_router
from employee import employee_router
from customer import customer_router
from ticket import ticket_router
from ai_chat import ai_chat_router
from dependencies import HTTPAuthorizationCredentials, security
from redis_client import redis_client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

env_path = os.path.join(BASE_DIR, ".env")
HUBSPOT_TOKEN = repr(os.getenv("HUBSPOT_TOKEN"))

app = FastAPI(title="Smart Support Desk")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_chat_router)
app.include_router(employee_router)
app.include_router(customer_router)
app.include_router(ticket_router)
app.include_router(hubspot_ticket_router)

@app.post("/logout", tags=["Logout"])
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Log out the current user by deleting their session token from Redis.

    This endpoint invalidates the user's JWT access token, effectively
    logging them out and preventing further use of the token.

    Args:
    - credentials (HTTPAuthorizationCredentials, Depends): Extracted JWT token from the Authorization header.

    Returns:
    - dict: Confirmation message indicating the user has been logged out.

    Raises:
    - No explicit exceptions; if the token does not exist in Redis, the operation is idempotent.
    """

    redis_client.delete(credentials.credentials)
    return {"message": "Logged out successfully"}
