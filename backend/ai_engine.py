from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    ToolMessage,
)
import requests
from tools.customer import fetch_all_customers
import json
# later you can add more tools:
# from tools.ticket import fetch_open_tickets, create_ticket

# 1. Initialize LLM once (IMPORTANT)
llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    # model="gemini-2.5-flash",
    # model="gemini-2.5-flash-lite",
    temperature=0,
    # api_key="AIzaSyBoDoe3kf8Una3D6wpel_L-TvVYrxTs5UU"
    api_key="AIzaSyB0tPpPx9o7m6QMm_63tzjxfUCHc4r8QYw"
)

# 2. Register tools
tools = [
    fetch_all_customers,
    # fetch_open_tickets,
    # create_ticket,
]

llm_with_tools = llm.bind_tools(tools)

# 3. System message (global behavior)
# SYSTEM_MESSAGE = SystemMessage(
#     content="""
# You are an AI CRM assistant.

# Current user role: {user.get("role")}

# Rules:
# - Call tools only when required
# - Tools return structured data
# - If success=false, explain politely and guide the user
# - If success=true, summarize the result clearly
# - Never expose internal errors or technical terms
# """
# )

def extract_text(content) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return " ".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict)
        )

    return str(content)
import httpx

async def call_tool_with_auth(tool_name: str, token: str):
    headers = {"Authorization": token}
    async with httpx.AsyncClient() as client:
        if tool_name == "fetch_all_customers":
            try:
                # Increase timeout to 20 or 30 seconds if your DB is slow
                response = await client.get(
                    "http://127.0.0.1:8000/all_customers", 
                    headers=headers, 
                    timeout=20.0
                )
                # ... rest of your logic
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",response)
                if response.status_code == 401:
                    return {
                        "success": False,
                        "message": "You are not authorized to view customer data."
                    }

                if response.status_code != 200:
                    return {
                        "success": False,
                        "message": f"Customer service returned {response.status_code}"
                    }

                return {
                    "success": True,
                    "data": response.json()
                }

            except Exception as e:
                return {
                    "success": False,
                    "message": str(e)
                }

        # 👇 IMPORTANT FALLBACK
        return {
            "success": False,
            "message": f"Unknown tool requested: {tool_name}"
        }

async def run_ai_chat(prompt: str, user: dict, token: str) -> str:
    system_message = SystemMessage(
        content=f"""
        You are an AI CRM assistant.

        Current user role: {user.get("role", "unknown")}

        Rules:
        - Call tools only when required
        - Tools return structured data
        - If success=false, explain politely and guide the user and also provide the reason that it was not succesful
        - If success=true, summarize the result clearly
        - Never expose internal errors or technical terms
        """
            )
    print("----------user-----------",user)
    messages = [
        system_message,
        HumanMessage(content=prompt)
    ]

    # First model call
    ai_response = await llm_with_tools.ainvoke(messages)
    messages.append(ai_response)
    print(":::::::::::::::: ai_response ::::::::::::::::::::::",ai_response)
    # If tool is requested
    if ai_response.tool_calls:
        tool_call = ai_response.tool_calls[0]
        print("@@@@@@@@@@@@@ tool call @@@@@@@@@@@@@@@@@@@@@@ ",tool_call)
        tool_map = {tool.name: tool for tool in tools}
        print("__________tool_map_______",tool_map)
        tool_fn = tool_map.get(tool_call["name"])
        print("__________tool_fn_______",tool_fn)

        if tool_fn:
            try:
                # print("====$$$$$ tool_output $$$$$==========",tool_fn)
                tool_output = await call_tool_with_auth(
                    tool_name=tool_call["name"],

                    token=token
                )

                print("===========tool_output===============",tool_output)
            except Exception:
                tool_output = {
                    "success": False,
                    "message": "Unable to complete the requested operation"
                }

            # VERY IMPORTANT: append real tool output
            messages.append(
                ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=json.dumps({
                        "success": tool_output["success"],
                        "data": tool_output.get("data"), 
                        "message": tool_output.get("message")
                    })
                )
            )

            final_response = await llm_with_tools.ainvoke(messages)
            return extract_text(final_response.content)

    return extract_text(ai_response.content)
