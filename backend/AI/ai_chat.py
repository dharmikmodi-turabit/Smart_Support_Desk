from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from Authentication.dependencies import get_current_user
from typing import Optional, List, Dict, Union
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
import requests
from AI.tools.customer import fetch_all_customers, create_customer, fetch_customer_by_email, update_customer
from AI.tools.ticket import create_ticket, emp_my_tickets, customer_my_tickets, fetch_all_tickets, fetch_tickets_by_customer, ticket_analysis_per_emp, update_ticket
import json, os, re
from langchain_groq import ChatGroq
from database.database import chat_sessions, chat_messages
from bson import ObjectId
from datetime import datetime

ai_chat_router = APIRouter(prefix="/ai", tags=["AI Chatbot"])

class CreateSession(BaseModel):
    title: Optional[str] = "New Chat"


class SaveMessage(BaseModel):
    session_id: str
    user_id: int
    role: str
    content: str
    analysis: Optional[Dict] = None
    data: Optional[List] = None

@ai_chat_router.post("/session")
def create_session(
    payload: CreateSession,
    user=Depends(get_current_user)
):
    """
    Create a new chat session for the authenticated user.

    This endpoint:
        1. Extracts user identity and role from the JWT.
        2. Generates a session title using the current UTC timestamp.
        3. Stores session metadata in the `chat_sessions` collection.
        4. Returns the newly created session identifier.

    Request Body:
        CreateSession:
            (Currently not used directly in logic, but reserved
             for future extensibility such as custom titles.)

    Dependencies:
        user:
            Authenticated user injected via `get_current_user`.
            Must contain:
                - "emp_id" (used as user_id)
                - "role"   (stored for role-aware session context)

    Stored Fields:
        - user_id (from JWT: emp_id)
        - role (from JWT)
        - title (UTC timestamp string: YYYY-MM-DD HH:MM)
        - created_at (UTC datetime)
        - updated_at (UTC datetime)

    Returns:
        dict:
            {
                "session_id": str,   # MongoDB ObjectId as string
                "title": str         # Auto-generated session title
            }

    Behavior:
        - Title is auto-generated based on UTC time.
        - created_at and updated_at are initialized to the same value.
        - Session is strictly bound to the authenticated user.

    Security:
        - User identity is derived exclusively from JWT.
        - Client cannot override user_id or role.

    Notes:
        - Suitable for initializing a new conversational context.
        - Session title can later be updated if custom naming is required.
    """

    try:
        session = {
            "user_id": user["emp_id"],  # from JWT
            "role": user["role"],  # from JWT
            "title": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = chat_sessions.insert_one(session)

        return {
            "session_id": str(result.inserted_id),
            "title": session["title"]
        }
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )


@ai_chat_router.get("/sessions")
def get_sessions(user=Depends(get_current_user)):
    """
    Retrieve all chat sessions for the authenticated user.

    This endpoint:
        1. Extracts the authenticated user's emp_id.
        2. Queries the `chat_sessions` collection for matching user_id.
        3. Converts MongoDB ObjectId fields to string format
           for JSON serialization compatibility.

    Dependencies:
        user:
            Authenticated user injected via `get_current_user`.
            Must contain "emp_id" used as the session owner identifier.

    Returns:
        list[dict]:
            A list of chat session documents associated with the user.
            Each session includes:
                - _id (str)
                - user_id
                - session metadata (if stored)
                - any additional session attributes

    Behavior:
        - Filters sessions strictly by user["emp_id"].
        - Converts `_id` from ObjectId to string.
        - Returns an empty list if no sessions exist.

    Security:
        - Sessions are user-scoped.
        - Only sessions belonging to the authenticated user are returned.

    Notes:
        - Assumes chat_sessions collection stores user_id as emp_id.
        - No sorting is applied unless defined at the database level.
    """

    try:
        sessions = list(
            chat_sessions.find({"user_id": user["emp_id"]})
        )

        for s in sessions:
            s["_id"] = str(s["_id"])

        return sessions
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )


@ai_chat_router.post("/message")
def save_message(payload: SaveMessage):
    """
    Persist a chat message into the chat_messages collection.

    This endpoint:
        1. Accepts a structured message payload.
        2. Converts session_id into a MongoDB ObjectId.
        3. Stores the message along with metadata and timestamp.
        4. Inserts the record into the `chat_messages` collection.

    Request Body:
        SaveMessage:
            - session_id (str): MongoDB ObjectId string of the chat session.
            - user_id (str | int): Identifier of the message sender.
            - role (str): Message role (e.g., "user", "assistant", "system").
            - content (str): Main message text.
            - analysis (Optional[Any]): Optional structured analysis data.
            - data (Optional[Any]): Optional structured response data.

    Stored Fields:
        - session_id (ObjectId)
        - user_id
        - role
        - content
        - analysis
        - data
        - created_at (UTC timestamp)

    Returns:
        dict:
            {
                "status": "saved"
            }

    Notes:
        - Timestamp is generated using UTC for consistency.
        - Assumes payload.session_id is a valid ObjectId string.
        - No duplicate detection or validation logic is applied.
        - Designed for internal chat history persistence.
    """

    try:
        message = {
            "session_id": ObjectId(payload.session_id),
            "user_id": payload.user_id,
            "role": payload.role,
            "content": payload.content,
            "analysis": payload.analysis,
            "data": payload.data,
            "created_at": datetime.utcnow()
        }

        chat_messages.insert_one(message)

        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )

@ai_chat_router.get("/messages/{session_id}")
def get_messages(session_id: str):
    """
    Retrieve all chat messages for a given session.

    This endpoint:
        1. Queries the `chat_messages` collection using the provided session_id.
        2. Sorts messages in ascending order by `created_at`.
        3. Converts MongoDB ObjectId fields to string format
           for JSON serialization compatibility.

    Path Parameters:
        session_id (str):
            MongoDB ObjectId string representing the chat session.

    Returns:
        list[dict]:
            A list of message documents sorted chronologically.
            Each message includes:
                - _id (str)
                - session_id (str)
                - role (if stored)
                - content
                - created_at
                - any additional stored metadata

    Behavior:
        - Converts both `_id` and `session_id` from ObjectId to string.
        - Returns messages in oldest-to-newest order.

    Notes:
        - Assumes `session_id` is a valid MongoDB ObjectId string.
        - No explicit authentication/authorization enforcement
          is implemented in this endpoint.
        - If no messages exist, an empty list is returned.
    """

    try:
        messages = list(
            chat_messages.find(
                {"session_id": ObjectId(session_id)}
            ).sort("created_at", 1)
        )

        for m in messages:
            m["_id"] = str(m["_id"])
            m["session_id"] = str(m["session_id"])

        return messages
    except Exception as e:
        return str(e)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY1")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY2")
GROK_API_KEY = os.getenv("GROK_API_KEY")
llm = ChatGroq(
    model="qwen/qwen3-32b",
    # model="moonshotai/kimi-k2-instruct-0905",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=GROK_API_KEY
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
    update_ticket,
    emp_my_tickets,
    fetch_all_tickets,
    customer_my_tickets,
    fetch_tickets_by_customer,
    ticket_analysis_per_emp
]

llm_with_tools = llm.bind_tools(tools)

def extract_text(content):
    """
    Normalize LLM response content into a clean plain string.

    This utility ensures consistent text extraction from various
    LLM response formats, including strings, lists, and dictionaries.

    Supported Input Types:
        - str:
            Returned after trimming whitespace.
        - list:
            Iterates through items and extracts:
                • `item["text"]` if item is a dict containing "text"
                • the string itself if item is a str
            Concatenates all extracted values into a single string.
        - dict:
            Returns the value of the "message" key if present.
        - None:
            Returns an empty string.
        - Any other type:
            Converted to string using `str()`.

    Args:
        content (Any):
            Raw LLM response content.

    Returns:
        str:
            Normalized plain-text representation.

    Design Rationale:
        - Handles heterogeneous LLM output structures safely.
        - Prevents runtime errors caused by unexpected content types.
        - Ensures downstream consumers always receive a string.

    Intended Usage:
        Used as a safeguard when returning non-tool LLM responses
        to maintain predictable API behavior.
    """

    try:
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
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )

def extract_json(text: str):
    """
    Extract and parse the first JSON array found in a text string.

    This function searches the input text for the first occurrence
    of a JSON array pattern (i.e., content enclosed in square brackets),
    attempts to deserialize it into a Python object, and returns it.

    Args:
        text (str):
            Raw text that may contain an embedded JSON array.

    Returns:
        list:
            - Parsed Python list if a valid JSON array is found.
            - Empty list [] if no valid JSON array is detected
              or if parsing fails.

    Behavior:
        - Uses a regex pattern to match the first "[ ... ]" block.
        - Operates in DOTALL mode to allow multi-line matching.
        - Silently suppresses JSON decoding or regex errors.

    Limitations:
        - Greedy matching may capture more than intended if multiple
          JSON arrays exist in the text.
        - Only extracts JSON arrays (not JSON objects `{}`).
        - Returns empty list instead of raising exceptions.

    Intended Use:
        Primarily used for safely extracting structured ticket
        data from LLM-generated responses.
    """
    try:
        match = re.search(r"\[.*\]", text, re.S)
        if match:
            return json.loads(match.group())
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )


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
    """
    AI-driven CRM command endpoint.

    This endpoint processes natural language CRM instructions and converts them
    into controlled backend operations using a tool-restricted LLM workflow.
    The authenticated user's role determines permitted actions.

    Authentication:
        - Requires valid JWT via Authorization header.
        - User identity and role are resolved via `get_current_user` dependency.
        - Tokens are injected internally into tool calls.
        - Clients must NOT provide token, emp_id, or customer_id manually.

    Supported Domains:
        CUSTOMER:
            - Fetch all customers
            - Fetch customer by email
            - Create customer (multi-step draft supported)
            - Update customer

        TICKET:
            - Create ticket
            - Fetch all tickets (Admin/Agent)
            - Fetch my tickets (Service Person / Customer)
            - Fetch tickets by customer (Admin/Agent only)
            - Update ticket (with strict role + status validation)
            - Ticket analytics per employee

    Core Responsibilities:
        1. Interpret user intent from natural language.
        2. Validate required fields before tool execution.
        3. Enforce strict role-based authorization.
        4. Prevent invalid or unauthorized ticket status transitions.
        5. Execute exactly one valid backend tool per request when applicable.
        6. Apply LLM-based second-pass filtering for ticket queries
           (e.g., priority or status filtering).

    Ticket Status Authorization Rules:
        - If ticket status is "Open":
            • Only the assigned Service Person may move it to "In_Progress".
            • Admin/Agent cannot modify status while it is "Open".
        - Unauthorized attempts are blocked before tool execution.

    Draft Handling:
        - Customer creation supports multi-turn draft accumulation.
        - Required fields are validated before final creation.
        - Draft is cleared after successful submission.

    Filtering Behavior:
        - Filtering requests (e.g., "high priority tickets") trigger
          the appropriate base fetch operation.
        - Filtering is applied via secondary LLM pass.
        - The system does not reject filtering requests.

    Returns:
        ChatResponse:
            {
                "message": str,        # Operation result or clarification
                "data": Optional[Any]  # Structured data when applicable
            }

    Error Handling:
        - Backend validation errors are returned in the message field.
        - Unhandled exceptions return:
              "AI system error: <error_message>"

    Notes:
        - This endpoint is deterministic and tool-restricted.
        - It is not a conversational chatbot.
        - Unsupported intents return guidance only.
    """
    chat_sessions.create_index("user_id")
    chat_messages.create_index("session_id")
    chat_messages.create_index("created_at")
    try:
        if "customer_draft" not in request.state.__dict__:
            request.state.customer_draft = {}

        # 🔐 Auth already validated by dependency
        role = user.get("role", "unknown")
        auth_header = request.headers.get("authorization")
        messages = [
            SystemMessage(
                content=f"""
You are an AI CRM assistant.
You are a STRICT AI CRM command processor, not a general chatbot.
User role: {role}
Just keep history of the chat to give better output of the next prompt or relate to previous prompt. 

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
9. Update ticket

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

If the user says:
- "update ticket <id>"
- "change ticket <id>"
- "modify ticket <id>"
- "close ticket <id>"
- "set ticket <id> to high priority"
- "change ticket <id> status to Close"

→ Call update_ticket

------------------------------------
FIELD & AUTH RULES (CRITICAL)
------------------------------------
- Authentication is already validated by the system
- Tokens are injected automatically
- NEVER ask the user for token, emp_id, or customer_id
- NEVER fabricate IDs
- Identity must always come from authentication context

------------------------------------
FIELD & AUTH RULES (CRITICAL)
------------------------------------
------------------------------------
TICKET STATUS AUTHORIZATION RULE (STRICT)
------------------------------------

Before calling update_ticket for ticket_status change:

- You MUST check:
  1. Current ticket_status
  2. Authenticated user role

RULES:

1. If ticket_status is "Open":
   - ADMIN and AGENT are NOT allowed to change the status.
   - Only the assigned SERVICE PERSON may change status from "Open" to "InProgress".

2. If ADMIN or AGENT attempts to change status while ticket is "Open":
   - DO NOT call update_ticket
   - Respond:
     "You are not authorized to update this ticket while it is Open."

3. Never bypass this rule.
4. If role permission fails → do NOT generate tool_calls.


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

Update Ticket:
Required:
- ticket_id

Optional:
- issue_type
- issue_description
- priority (Low, Medium, High)
- ticket_status (Open, InProgress, Close)
- reason

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

For update_ticket:
- ticket_id is mandatory
- If missing → ask user for ticket_id
- Never guess ticket_id

When updating a ticket:
If user says "close ticket 5"
→ Call update_ticket with:
{{
  "ticket_id": 5,
  "ticket_status": "Close"
}}

If user says "set ticket 5 priority to High"
→ Call update_ticket with:
{{
  "ticket_id": 5,
  "priority": "High"
}}

If user says "in progress ticket 5"
→ Call update_ticket with:
{{
  "ticket_id": 5,
  "priority": "In_Progress"
}}
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
        if auth_header:
            token = auth_header.split(" ")[1]

        user_id = user.get("emp_id")
        draft = CUSTOMER_DRAFTS.get(user_id, {})

        ai_response = llm_with_tools.invoke(messages)

        # ✅ TOOL CALL (controlled by API, not LLM args)
        if getattr(ai_response, "tool_calls", None):
            tool_call = ai_response.tool_calls[0]
            tool_name = tool_call.get("name")

            #---------------------------- Customer ----------------------------
            if tool_name == "fetch_all_customers":
                tool_args = {
                    "token": token,
                    "user": user

                }
                customers = fetch_all_customers.invoke(tool_args)
                if isinstance(customers,dict) and customers.get('detail'):
                    return {"message":customers['detail']}
                return {
                    "message": "Customers fetched successfully",
                    "data": customers
                }
            elif tool_name == "fetch_customer_email":
                tool_args = tool_call.get("args", {})

                tool_args["token"] = token
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

                # check missing fields
                missing = REQUIRED_FIELDS - set(draft.keys())

                if missing:
                    return {
                        "message": "I still need the following details: " + ", ".join(sorted(missing))
                    }

                # all fields available → call tool
                draft["token"] = token
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

            #     # ---------- SECOND PASS (LLM FILTERING) ----------
            #     filter_messages = [
            #         SystemMessage(content="""
            # You are a CRM ticket filtering engine.

            # Filter the provided tickets strictly based on the user's request.

            # Return ONLY a JSON array.
            # Do NOT include explanations.
            # Output MUST start with [ and end with ].
            # """),
            #         HumanMessage(
            #             content=f"""
            #     User request:
            #     {payload.prompt}

            #     Tickets:
            #     {json.dumps(tickets)}
            #     """
            #         )
            #     ]

            #     filtered = llm.invoke(filter_messages)

            #     filtered_json = extract_json(filtered.content)
                filtered_json = tickets
                print(filtered_json)

                prompt_lower = payload.prompt.lower()

                if "high" in prompt_lower:
                    filtered_json = [t for t in filtered_json if t.get("priority") == "High"]

                elif "medium" in prompt_lower:
                    filtered_json = [t for t in filtered_json if t.get("priority") == "Medium"]

                elif "low" in prompt_lower:
                    filtered_json = [t for t in filtered_json if t.get("priority") == "Low"]

                if "open" in prompt_lower:
                    filtered_json = [t for t in filtered_json if t.get("ticket_status") == "Open"]

                elif "close" in prompt_lower:
                    filtered_json = [t for t in filtered_json if t.get("ticket_status") == "Close"]

                elif "in progress" in prompt_lower:
                    filtered_json = [t for t in filtered_json if t.get("ticket_status") == "In_Progress"]
                print(filtered_json)
                return {
                    "message": "Tickets fetched successfully",
                    "data": filtered_json
                }

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

            elif tool_name == "fetch_all_tickets":
                tool_argss = {
                    "token": token,
                    "user": user

                }

                tickets = fetch_all_tickets.invoke(tool_argss)
                print("Tickets++++++++++++++++++++++++++++",tickets)
                if isinstance(tickets, dict) and tickets.get('detail'):
                    return {"message": tickets['detail']}

            #     # ---------- SECOND PASS (LLM FILTERING) ----------
            #     filter_messages = [
            #         SystemMessage(content=f"""
            # You are a CRM ticket filtering engine.

            # Filter the provided tickets strictly based on the user's request.
            # If {role} is admin and asking for "my tickets" then return all tickets, No need to find id into the data.

            # Return ONLY a JSON array.
            # Do NOT include explanations.
            # Output MUST start with [ and end with ].
            # """),
            #         HumanMessage(
            #             content=f"""
            #     User request:
            #     {payload.prompt}

            #     Tickets:
            #     {json.dumps(tickets)}
            #     """
            #         )
            #     ]


            #     filtered = llm.invoke(filter_messages)
            #     print("filtered_________________________",filtered)

            #     filtered_json = extract_json(filtered.content)
            #     print("filtered_json=============================",filtered_json)
                filtered_json = tickets
                print(filtered_json)

                prompt_lower = payload.prompt.lower()

                if "high" in prompt_lower:
                    filtered_json = [t for t in filtered_json if t.get("priority") == "High"]

                elif "medium" in prompt_lower:
                    filtered_json = [t for t in filtered_json if t.get("priority") == "Medium"]

                elif "low" in prompt_lower:
                    filtered_json = [t for t in filtered_json if t.get("priority") == "Low"]

                if "open" in prompt_lower:
                    filtered_json = [t for t in filtered_json if t.get("ticket_status") == "Open"]

                elif "close" in prompt_lower:
                    filtered_json = [t for t in filtered_json if t.get("ticket_status") == "Close"]

                elif "in progress" in prompt_lower:
                    filtered_json = [t for t in filtered_json if t.get("ticket_status") == "In_Progress"]
                print(filtered_json)
                return {
                    "message": "Tickets fetched successfully",
                    "data": filtered_json
                }
            elif tool_name == "fetch_tickets_by_customer":

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
                tool_args = tool_call.get("args", {})
                if not tool_args.get("emp_id"):
                    tool_args["emp_id"]= user_id
                tool_args["token"] = token

                analysis = ticket_analysis_per_emp.invoke(tool_args)


                return {
                    "message": "Ticket analytics fetched successfully",
                    "data": analysis
                }
            elif tool_name == "update_ticket":

                tool_args = tool_call.get("args", {})
                tool_args["token"] = token
                if tool_args.get("ticket_status"):
                    status_mapping = {
                        "InProgress": "In_Progress",
                        "In Progress": "In_Progress",
                        "in Progress": "In_Progress",
                        "In progress": "In_Progress",
                        "in progress": "In_Progress",
                        "in progress": "In_Progress",
                        "in_progress": "In_Progress"
                    }
                    tool_args["ticket_status"] = status_mapping.get(tool_args["ticket_status"], tool_args["ticket_status"])

                result = update_ticket.invoke(tool_args)

                if isinstance(result, dict) and result.get("detail"):
                    return {"message": result["detail"]}

                return {
                    "message": result.get("message", "Ticket updated successfully"),
                    "data": None
                }


        return {
            "message": extract_text(ai_response.content) or "",
            "data": None
        }
    except Exception as e:
        return {
            "message": f"AI system error: {str(e)}"
        }
