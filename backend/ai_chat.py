from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from ai_engine import run_ai_chat
from dependencies import get_current_user
import streamlit as st
import requests
from typing import Optional, List
import httpx
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
import requests
from tools.customer import fetch_all_customers
import json, os
from langchain_groq import ChatGroq
from ai_engine import llm_with_tools, extract_text

ai_chat_router = APIRouter(prefix="/ai", tags=["AI Chatbot"])


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    message: str
    data: Optional[List[dict]] = None



# @ai_chat_router.post("/chat", response_model=ChatResponse)
# async def chat_with_ai(
#     payload: ChatRequest,
#     request: Request,
#     user=Depends(get_current_user)
# ):
#     token = request.headers.get("Authorization")
#     print("====================token==============",token)
#     print(payload)
#     response = await run_ai_chat(
#         prompt=payload.prompt,
#         user=user,
#         token=token
#     )
#     # messages = [
#     #     SystemMessage(
#     #         content=f"""
#     #         You are an AI CRM assistant.
#     #         Role: {user.get("role", "unknown")}

#     #         Rules:
#     #         - Decide when to call a tool
#     #         - NEVER explain tool execution
#     #         - NEVER generate filler text
#     #         - If a tool is called, return its data directly
#     #         """
#     #     ),
#     #     HumanMessage(content=payload.prompt)
#     # ]

#     # ai_response = await llm_with_tools.ainvoke(messages)
#     # print("---ai_responsse----------",ai_response)
#     # # 🔹 If tool was requested → EXECUTOR already ran it
#     # if ai_response.tool_calls:
#     #     tool_message = messages[-1]  # ToolMessage is appended automatically
#     #     print(tool_message)
#     #     final_response = await llm_with_tools.ainvoke(messages)
#     #     print(final_response)
#     #     return {
#     #         "message": "Customers fetched successfully",
#     #         "data": tool_message.content  # 👈 REAL customer data
#     #     }
#     # ai_response = await llm_with_tools.ainvoke(messages)

#     # if ai_response.tool_calls:
#     #     tool_call = ai_response.tool_calls[0]

#     #     if tool_call["name"] == "fetch_all_customers":
#     #         customers = fetch_all_customers_internal(token)

#     #         return {
#     #             "message": "Customers fetched successfully",
#     #             "data": customers
#     #         }

#     # # 🔹 Normal chat response
#     # return {
#     #     "message": extract_text(ai_response.content),
#     #     "data": None
#     # }
#     # Clean the tags here so the frontend doesn't have to
#     if "message" in response:
#         response["message"] = response["message"].replace("<response>", "").replace("</response>", "").strip()
#     # return ChatResponse(
#     #     message=response.get("message", ""),
#     #     data=response.get("data")
#     # )
#     return response


# @ai_chat_router.post("/chat", response_model=ChatResponse)
# async def chat_with_ai(
#     payload: ChatRequest,
#     request: Request,
#     user=Depends(get_current_user)
# ):
#     token = request.headers.get("Authorization")

#     messages = [
#         SystemMessage(
#             content=f"""
#             You are an AI CRM assistant.
#             Role: {user.get("role", "unknown")}

#             Rules:
#             - Decide when to call a tool
#             - NEVER explain tool execution
#             - NEVER generate filler text
#             """
#         ),
#         HumanMessage(content=payload.prompt)
#     ]

#     ai_response = await llm_with_tools.ainvoke(messages)

#     # ✅ CASE 1: TOOL CALL
#     if ai_response.tool_calls:
#         tool_call = ai_response.tool_calls[0]

#         if tool_call["name"] == "fetch_all_customers":
#             customers = fetch_all_customers_internal(token)

#             return {
#                 "message": "Customers fetched successfully",
#                 "data": customers        # ✅ MUST be list
#             }

#     # ✅ CASE 2: NORMAL CHAT
#     text = extract_text(ai_response.content)

#     return {
#         "message": text,
#         "data": None                 # ✅ NEVER ""
#     }







# @ai_chat_router.post("/chat", response_model=ChatResponse)
# async def chat_with_ai(
#     payload: ChatRequest,
#     request: Request,
#     user=Depends(get_current_user)
# ):
#     print("[[[[[[[[[[[[[[[[[[request]]]]]]]]]]]]]]]]]]",request.headers)
#     auth_header = request.headers.get("authorization")
#     token = auth_header.split(" ")[1]

#     if not auth_header or not auth_header.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Missing token")
#     messages = [
#         SystemMessage(
#             content=f"""
#             You are an AI CRM assistant.
#             Role: {user.get("role", "unknown")}

#             Rules:
#             - Decide when to call a tool
#             - NEVER explain tool execution
#             """
#         ),
#         HumanMessage(content=payload.prompt)
#     ]

#     ai_response = await llm_with_tools.ainvoke(messages)
#     print("===============================",ai_response)
#     # ✅ TOOL CALL CASE
#     if ai_response.tool_calls:
#         tool_call = ai_response.tool_calls[0]

#         if tool_call["name"] == "fetch_all_customers":
#             tool_args = {
#                 "token": token,
#                 "user": user
#             }
#             customers = await fetch_all_customers.ainvoke(tool_args)


#             return {
#                 "message": "Customers fetched successfully",
#                 "data": customers        # ✅ LIST
#             }

#     # ✅ NORMAL CHAT CASE
#     return {
#         "message": extract_text(ai_response.content),
#         "data": None                 # ✅ NOT ""
#     }




@ai_chat_router.post("/chat", response_model=ChatResponse)
def chat_with_ai(
    payload: ChatRequest,
    request: Request,
    user=Depends(get_current_user)
):
    # 🔐 Auth already validated by dependency
    role = user.get("role", "unknown")
    auth_header = request.headers.get("authorization")
    token = auth_header.split(" ")[1]

    messages = [
        SystemMessage(
            content=f"""
                You are an AI CRM assistant.

                User role: {role}

                Rules:
                - Decide whether data is required
                - If data is required, respond with a TOOL_CALL
                - NEVER explain tool execution
                """
        ),
        HumanMessage(content=payload.prompt)
    ]

    ai_response = llm_with_tools.invoke(messages)
    print("AI RESPONSE:", ai_response)

    # ✅ TOOL CALL (controlled by API, not LLM args)
    if ai_response.tool_calls:
        tool_name = ai_response.tool_calls[0]["name"]

        if tool_name == "fetch_all_customers":
            # 🔒 No token passing, no re-auth
            #         if tool_call["name"] == "fetch_all_customers":
            tool_args = {
                "token": token,
                "user": user
            }
            customers = fetch_all_customers.invoke(tool_args)

            return {
                "message": "Customers fetched successfully",
                "data": customers
            }

    # ✅ NORMAL CHAT
    return {
        "message": extract_text(ai_response.content),
        "data": None
    }
