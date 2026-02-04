from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage, HumanMessage,AIMessage
import requests
from dependencies import Depends
from fastapi import status, APIRouter
from fastapi.exceptions import HTTPException
from database import access_db
from tools.customer import fetch_all_customers

ai_crm_router = APIRouter()

llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0,
    api_key="AIzaSyBoDoe3kf8Una3D6wpel_L-TvVYrxTs5UU"
)

tools = [fetch_all_customers,]

llm_with_tools = llm.bind_tools(tools)
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