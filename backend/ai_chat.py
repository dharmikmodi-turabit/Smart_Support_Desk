from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from dependencies import get_current_user
from typing import Optional, List, Dict, Union
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
import requests
from tools.customer import fetch_all_customers, create_customer, fetch_customer_by_email, update_customer
from tools.ticket import create_ticket, emp_my_tickets, customer_my_tickets, fetch_all_tickets, fetch_tickets_by_customer, ticket_analysis_per_emp
import json, os, re
from langchain_groq import ChatGroq
# from ai_engine import llm_with_tools, extract_text/

ai_chat_router = APIRouter(prefix="/ai", tags=["AI Chatbot"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY1")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY2")
GROK_API_KEY = os.getenv("GROK_API_KEY")
# print("~~~~~~~~~~~~~~~~~~GEMINI_API_KEY-----------------",GEMINI_API_KEY)
llm = ChatGroq(
    model="qwen/qwen3-32b",
    # model="moonshotai/kimi-k2-instruct-0905",
    temperature=0,
    max_tokens=None,
    # reasoning_format="parsed",
    timeout=None,
    max_retries=2,
    api_key=GROK_API_KEY
    # other params...
)
##---------------Gemini API Config---------------
# llm = ChatGoogleGenerativeAI(
#     model="gemini-3-flash-preview",
#     # model="gemini-2.5-flash",
#     # model="gemini-2.5-flash-lite",
#     temperature=0,
#     # api_key="AIzaSyBoDoe3kf8Una3D6wpel_L-TvVYrxTs5UU"
#     api_key="AIzaSyB0tPpPx9o7m6QMm_63tzjxfUCHc4r8QYw"
# )

# 2. Register tools
tools = [
    fetch_all_customers,
    fetch_customer_by_email,
    create_customer,
    update_customer,
    create_ticket,
    emp_my_tickets,
    fetch_all_tickets,
    customer_my_tickets,
    fetch_tickets_by_customer,
    ticket_analysis_per_emp
]

llm_with_tools = llm.bind_tools(tools)

def extract_text(content):
    """
    Normalize LLM content to plain string.
    Handles string | list | dict safely.
    """
    if content is None:
        return ""

    if isinstance(content, str):
        return content.strip()

    # Sometimes content is a list of dicts
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                texts.append(item["text"])
            elif isinstance(item, str):
                texts.append(item)
        return " ".join(texts).strip()

    # If dict (JSON), return as-is or stringify
    if isinstance(content, dict):
        return content.get("message", "") or ""

    return str(content)


def extract_json(text: str):
    try:
        match = re.search(r"\[.*\]", text, re.S)
        if match:
            return json.loads(match.group())
    except:
        pass
    return []


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    message: str
    data: Optional[Union[List[dict], Dict]] = None



# store partial customer inputs per user
CUSTOMER_DRAFTS = {}

REQUIRED_FIELDS = {
    "name",
    "email",
    "mobile_number",
    "company_name",
    "city",
    "state",
    "country",
    "address"
}


@ai_chat_router.post("/chat", response_model=ChatResponse)
def chat_with_ai(
    payload: ChatRequest,
    request: Request,
    user=Depends(get_current_user)
):
    if "customer_draft" not in request.state.__dict__:
        request.state.customer_draft = {}

    # 🔐 Auth already validated by dependency
    role = user.get("role", "unknown")
    auth_header = request.headers.get("authorization")
    # token = None
    if auth_header: 
        token = auth_header.split(" ")[1]
    print("********** Token ***************",token)

    user_id = user.get("id")
    draft = CUSTOMER_DRAFTS.get(user_id, {})


    messages = [
        SystemMessage(
            content=f"""
You are an AI CRM assistant.
You are a STRICT AI CRM command processor, not a general chatbot.

Your job is to:
- Interpret user intent from natural language
- Decide the correct CRM operation
- Call a backend tool ONLY when rules are satisfied
- Otherwise ask only for missing or unclear information

You are NOT allowed to:
- Act like a human support agent
- Apologize for system limitations
- Mention internal tools, APIs, or backend logic
- Invent data or assumptions
- Explain your reasoning or tool execution

User role: {role}
------------------------------------
SUPPORTED ACTIONS ONLY
------------------------------------
You support ONLY the following operations:

CUSTOMER:
1. Fetch all customers
2. Fetch customer by email
3. Create customer
4. Update customer

TICKET:
5. Create ticket
6. Fetch all tickets (Admin or Agent)
6. Fetch my tickets (Service Person)
7. Fetch my tickets (customer)
8. Fetch tickets by customer (Admin or Agent only)

------------------------------------
INTENT → ACTION MAPPING
------------------------------------

If the user says:
- "my tickets", "show my tickets", "tickets assigned to me"
  → Fetch MY tickets
- "tickets of customer"
- "customer wise tickets"
- "tickets for customer <email>"

→ Fetch tickets by customer

Only ADMIN or AGENT can fetch tickets for another customer.
CUSTOMER is not allowed.

Decision rules:
- If user role is ADMIN or AGENT → call fetch_all_tickets
- If user role is SERVICE PERSON → call emp_my_tickets
- If user role is CUSTOMER → call customer_my_tickets

------------------------------------
FIELD & AUTH RULES (CRITICAL)
------------------------------------
- Authentication is already validated by the system
- Tokens are injected automatically
- NEVER ask the user for token, emp_id, or customer_id
- NEVER fabricate IDs
- Identity must always come from authentication context

------------------------------------
REQUIRED VS OPTIONAL FIELDS
------------------------------------

Create Customer:
Required:
- name
- email
- mobile_number
- company_name
- city
- state
- country
- address

Update Customer:
Required:
- email
Optional:
- name
- mobile_number
- company_name
- city
- state
- country
- address

Fetch Customer:
Required:
- email

Ticket Creation:
Required:
- issue_title
- issue_description
- issue_type
- issue_priority

Fetch Tickets by Customer:
Required:
- customer_email

------------------------------------
TOOL CALL RULES (MANDATORY)
------------------------------------
Before calling a tool:
- Intent MUST clearly match
- All required fields MUST be present
- Arguments MUST match the tool schema exactly
- Do NOT add extra fields

If required data is missing:
- DO NOT call the tool
- Ask ONLY for missing fields

------------------------------------
TICKET FETCHING RULES
------------------------------------
If the user asks:
- "all tickets"
- "show all tickets"
- "list all tickets"
- "fetch tickets"

→ Call fetch_all_tickets

------------------------------------
FILTERING RULE (VERY IMPORTANT)
------------------------------------
If the user requests filtering such as:
- "high priority tickets"
- "medium priority tickets"
- "open tickets"
- "closed tickets"
- "my high priority tickets"

The tool itself may not support filtering.

In such cases:
- ALWAYS call the correct ticket-fetching tool FIRST:
    - SERVICE PERSON → emp_my_tickets
    - CUSTOMER → customer_my_tickets
    - ADMIN / AGENT → fetch_all_tickets

- DO NOT refuse the request
- DO NOT say filtering is unsupported
- Filtering will be applied later by the system automatically
- Your job is ONLY to select the correct base fetch operation

------------------------------------
ROLE-BOUND TICKET FETCHING (CRITICAL)
------------------------------------

When the user intent is to fetch THEIR OWN tickets:

IF User role = CUSTOMER:
- ALWAYS call customer_my_tickets
- NEVER call emp_my_tickets

IF User role = Service Person:
- ALWAYS call emp_my_tickets
- NEVER call customer_my_tickets

The phrase "my tickets" ALWAYS refers to the authenticated user.
Do NOT infer or switch roles.
Do NOT guess.

If the user is a CUSTOMER:
- They are NOT allowed to fetch all tickets
- "all tickets" must be rejected or clarified

If the user is Agent or ADMIN:
- "all tickets" → fetch_all_tickets


------------------------------------
EMAIL VALIDATION RULE
------------------------------------
If an email is provided:
- Must be valid format
- If invalid → respond:
  "Please provide a valid email address (example: user@example.com)"

------------------------------------
FINAL RULE
------------------------------------
- If intent matches → CALL TOOL
- If required data missing → ASK
- If intent unsupported → provide valid input guidance ONLY
- Never mention tools
- Never explain execution
- Be short, precise, and deterministic

Your goal is SAFE, PREDICTABLE, and CORRECT CRM automation.


                """
        ),
        HumanMessage(content=payload.prompt)
    ]
    print("==================user-----------------",user)
    print("TOken is here ", token)

    ai_response = llm_with_tools.invoke(messages)
    print("AI RESPONSE:", ai_response)

    # ✅ TOOL CALL (controlled by API, not LLM args)
    if getattr(ai_response, "tool_calls", None):
        tool_call = ai_response.tool_calls[0]
        tool_name = tool_call.get("name")
        # print(tool_name)
        #---------------------------- Customer ----------------------------
        if tool_name == "fetch_all_customers":
            tool_args = {
                "token": token,
                "user": user

            }
            customers = fetch_all_customers.invoke(tool_args)
            if isinstance(customers,dict) and customers.get('detail'):
                return {"message":customers['detail']}
            print("***** customers **********",customers)
            return {
                "message": "Customers fetched successfully",
                "data": customers
            }
        elif tool_name == "fetch_customer_email":
            tool_args = tool_call.get("args", {})

            tool_args["token"] = token
            print("$$$$$ Tool args $$$$$$$$$$$$$",tool_args)
            customer = fetch_customer_by_email.invoke(tool_args)
            if isinstance(customer,dict) and customer.get('detail'):
                return {"message":customer['detail']}

            return {
                "message": "Customer fetched successfully",
                "data": customer
            }
        elif tool_name == "create_customer":

            tool_args = tool_call.get("args", {})

            # merge new values into stored draft
            for k, v in tool_args.items():
                if v is not None and v != "":
                    draft[k] = v

            CUSTOMER_DRAFTS[user_id] = draft
            print("CUSTOMER_DRAFTS[user_id]",CUSTOMER_DRAFTS[user_id])

            # check missing fields
            missing = REQUIRED_FIELDS - set(draft.keys())

            if missing:
                return {
                    "message": "I still need the following details: " + ", ".join(sorted(missing))
                }

            # all fields available → call tool
            draft["token"] = token
            print(draft)
            result = create_customer.invoke(draft)

            # clear draft after success
            CUSTOMER_DRAFTS.pop(user_id, None)

            if isinstance(result, dict) and result.get("detail"):
                return {"message": result["detail"]}

            return {
                "message": result.get("message", "Customer created successfully"),
                "data": None
            }
        elif tool_name == "update_customer":
            tool_args = tool_call.get("args", {})

            tool_args["token"] = token
            print("$$$$$ Tool args $$$$$$$$$$$$$",tool_args)
            result = update_customer.invoke(tool_args)
            if isinstance(result, list):
                return {
                    "message": "Validation error",
                    "data": result
                }
            if isinstance(result, dict) and result.get("detail"):
                return {"message": result["detail"]}

            return {
                "message": result.get("message", "Customer updated successfully"),
                "data": None
            }
        #---------------------------- Ticket ----------------------------
        elif tool_name == "create_ticket":
        
            tool_args = tool_call.get("args", {})

            # merge new values into stored draft
            for k, v in tool_args.items():
                if v is not None and v != "":
                    draft[k] = v

            # all fields available → call tool
            draft["token"] = token
            print(draft)
            result = create_ticket.invoke(draft)


            if isinstance(result, dict) and result.get("detail"):
                return {"message": result["detail"]}

            return {
                "message": result.get("message", "Ticket created successfully"),
                "data": None
            }
        elif tool_name == "emp_my_tickets":
            tool_args = {
                "emp_id": user["emp_id"],  # derived from token
                "token" : token
            }

            tickets = emp_my_tickets.invoke(tool_args)

            if isinstance(tickets, dict) and tickets.get("detail"):
                return {"message": tickets["detail"]}

        # ---------- SECOND PASS (LLM FILTERING) ----------
            filter_messages = [
            SystemMessage(content="""
        You are a CRM ticket filtering engine.

        Filter the provided tickets strictly based on the user's request.

        Return ONLY a JSON array.
        Do NOT include explanations.
        Output MUST start with [ and end with ].
        """),
            HumanMessage(
                content=f"""
            User request:
            {payload.prompt}

            Tickets:
            {json.dumps(tickets)}
            """
                )
            ]

            filtered = llm.invoke(filter_messages)

            filtered_json = extract_json(filtered.content)

            return {
                "message": "Tickets fetched successfully",
                "data": filtered_json
            }

            # return {
            #     "message": "Tickets fetched successfully",
            #     "data": tickets
            # }
        elif tool_name == "customer_my_tickets":
            tool_args = {
                "token": token  # identity resolved by backend
            }

            tickets = customer_my_tickets.invoke(tool_args)

            if isinstance(tickets, dict) and tickets.get("detail"):
                return {"message": tickets["detail"]}

            # ---------- SECOND PASS (LLM FILTERING) ----------
            filter_messages = [
            SystemMessage(content="""
        You are a CRM ticket filtering engine.

        Filter the provided tickets strictly based on the user's request.

        Return ONLY a JSON array.
        Do NOT include explanations.
        Output MUST start with [ and end with ].
        """),
            HumanMessage(
                content=f"""
            User request:
            {payload.prompt}

            Tickets:
            {json.dumps(tickets)}
            """
                )
            ]

            filtered = llm.invoke(filter_messages)

            filtered_json = extract_json(filtered.content)

            return {
                "message": "Tickets fetched successfully",
                "data": filtered_json
            }
            # return {
            #     "message": "Tickets fetched successfully",
            #     "data": tickets
            # }
        elif tool_name == "fetch_all_tickets":
            print("++++++++++++Token________________",token)
            tool_argss = {
                "token": token,
                "user": user

            }

            tickets = fetch_all_tickets.invoke(tool_argss)
            print("Tickets --------------------------",tickets)
            if isinstance(tickets, dict) and tickets.get('detail'):
                return {"message": tickets['detail']}

            # ---------- SECOND PASS (LLM FILTERING) ----------
            filter_messages = [
            SystemMessage(content="""
        You are a CRM ticket filtering engine.

        Filter the provided tickets strictly based on the user's request.

        Return ONLY a JSON array.
        Do NOT include explanations.
        Output MUST start with [ and end with ].
        """),
            HumanMessage(
                content=f"""
            User request:
            {payload.prompt}

            Tickets:
            {json.dumps(tickets)}
            """
                )
            ]

            print("**********filter_message ***************",filter_messages)


            filtered = llm.invoke(filter_messages)
            print("**** filtered *********",filtered)

            filtered_json = extract_json(filtered.content)
            print("*********** filtered_json **************",filtered_json)
            print("returning")
            return {
                "message": "Tickets fetched successfully",
                "data": filtered_json
            }
        elif tool_name == "fetch_tickets_by_customer":
            if user["role"] not in ["ADMIN", "AGENT"]:
                return {"message": "You are not authorized to view other customers' tickets"}

            tool_args = tool_call.get("args", {})
            tool_args["token"] = token
            tool_args["user"] = user

            tickets = fetch_tickets_by_customer.invoke(tool_args)

            if isinstance(tickets, dict) and tickets.get("detail"):
                return {"message": tickets["detail"]}

            # optional second-pass filtering (priority/status)
            filter_messages = [
                SystemMessage(content="""
        You are a CRM ticket filtering engine.
        Return ONLY a JSON array.
        """),
                HumanMessage(content=f"""
        User request:
        {payload.prompt}

        Tickets:
        {json.dumps(tickets)}
        """)
            ]

            filtered = llm.invoke(filter_messages)
            filtered_json = extract_json(filtered.content)

            return {
                "message": "Tickets fetched successfully",
                "data": filtered_json
            }
        elif tool_name == "ticket_analysis_per_emp":
            print("&&&&&&&&& Tool args",tool_call.get("args", {}))
            tool_args = tool_call.get("args", {})
            # tool_args = {
            #     "emp_id": user["emp_id"],
            #     "token": token
            # }
            tool_args["token"] = token

            analysis = ticket_analysis_per_emp.invoke(tool_args)
            print("^^^^^^^^^^^ analysis ",analysis)

            # if isinstance(analysis, dict) and analysis.get("detail"):
            #     return {"message": analysis["detail"]}
            return {
                "message": "Ticket analytics fetched successfully",
                # "type": "analytics",
                "data": analysis
            }


        



    return {
        "message": extract_text(ai_response.content) or "",
        "data": None
    }
