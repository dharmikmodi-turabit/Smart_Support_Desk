from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage, HumanMessage,AIMessage
import requests
from dependencies import Depends
from fastapi import status, APIRouter
from fastapi.exceptions import HTTPException
from database import access_db

# ai_crm_router = APIRouter()

@tool
# @ai_crm_router.get("/ai_all_customers", tags=["AI"])
def fetch_all_customers():
    '''Fetch all customers from the database'''
    try:
        db = access_db()
        with db:
            with db.cursor() as cursor:
                cursor.execute("select * from customer")
                d = cursor.fetchall()
                if d:
                    return d
                else:
                    # raise HTTPException(
                    #         status_code=status.HTTP_404_NOT_FOUND,
                    #         detail="Customer not found"
                    #     )
                    return "Customer not found"
    except Exception as e:
    #     raise HTTPException(
    #     status_code=500,
    #     detail=str(e)
    # )
           return str(e)


llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0,
    api_key="AIzaSyBoDoe3kf8Una3D6wpel_L-TvVYrxTs5UU"
)

llm_with_tools = llm.bind_tools([fetch_all_customers])
query = HumanMessage('Give me all customers list')

messages = [query]
print(messages)
ai_response = llm_with_tools.invoke(messages)
print(ai_response)
messages.append(ai_response)

tool_call = ai_response.tool_calls[0]

tool_output = fetch_all_customers.invoke(tool_call)

messages.append(
    ToolMessage(
        tool_call_id=tool_call["id"],
        content=str(tool_output)
    )
)

final_response = llm_with_tools.invoke(messages)
print(final_response.content)

# print("----------________________-------------------",result)
# print(result.content)