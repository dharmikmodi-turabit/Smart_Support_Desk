from fastapi import FastAPI, Depends
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os
from hubspot_ticket_router import hubspot_ticket_router
from employee import employee_router
from customer import customer_router
from ticket import ticket_router
from dependencies import HTTPAuthorizationCredentials, security

from redis_client import redis_client



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

env_path = os.path.join(BASE_DIR, ".env")
# print("ENV PATH:", env_path)
# print("ENV EXISTS:", os.path.exists(env_path))
# print("RAW HUBSPOT_TOKEN =", repr(os.getenv("HUBSPOT_TOKEN")))
HUBSPOT_TOKEN = repr(os.getenv("HUBSPOT_TOKEN"))



app = FastAPI(title="Smart Support Desk")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employee_router)
app.include_router(customer_router)
app.include_router(ticket_router)
app.include_router(hubspot_ticket_router)

@app.post("/logout", tags=["Logout"])
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    redis_client.delete(credentials.credentials)
    return {"message": "Logged out successfully"}
