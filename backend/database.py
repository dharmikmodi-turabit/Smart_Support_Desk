import pymysql
from fastapi.exceptions import HTTPException
from pymongo import MongoClient
import os
from dotenv import load_dotenv


def access_db():
    try:
        connection = pymysql.connect(host='localhost',
                             user='root',
                             password='root',
                             database='smart_support_desk',
                             cursorclass=pymysql.cursors.DictCursor)
        return connection
    except pymysql.MySQLError as e:
        print("DB Connection Error:", e)
        raise HTTPException(status_code=500, detail="Database connection failed")


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)

db = client["ai_crm_chat_db"]

chat_sessions = db["chat_sessions"]
chat_messages = db["chat_messages"]
