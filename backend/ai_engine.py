# import httpx
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
# import requests
# from tools.customer import fetch_all_customers
# import json, os
# from langchain_groq import ChatGroq

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY1")
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY2")
# GROK_API_KEY = os.getenv("GROK_API_KEY")
# # print("~~~~~~~~~~~~~~~~~~GEMINI_API_KEY-----------------",GEMINI_API_KEY)
# llm = ChatGroq(
#     model="qwen/qwen3-32b",
#     # model="moonshotai/kimi-k2-instruct-0905",
#     temperature=0,
#     max_tokens=None,
#     # reasoning_format="parsed",
#     timeout=None,
#     max_retries=2,
#     api_key=GROK_API_KEY
#     # other params...
# )
# ##---------------Gemini API Config---------------
# # llm = ChatGoogleGenerativeAI(
# #     model="gemini-3-flash-preview",
# #     # model="gemini-2.5-flash",
# #     # model="gemini-2.5-flash-lite",
# #     temperature=0,
# #     # api_key="AIzaSyBoDoe3kf8Una3D6wpel_L-TvVYrxTs5UU"
# #     api_key="AIzaSyB0tPpPx9o7m6QMm_63tzjxfUCHc4r8QYw"
# # )

# # 2. Register tools
# tools = [
#     fetch_all_customers,
#     # fetch_open_tickets,
#     create_customer,
# ]

# llm_with_tools = llm.bind_tools(tools)

# # 3. System message (global behavior)
# # SYSTEM_MESSAGE = SystemMessage(
# #     content="""
# # You are an AI CRM assistant.

# # Current user role: {user.get("role")}

# # Rules:
# # - Call tools only when required
# # - Tools return structured data
# # - If success=false, explain politely and guide the user
# # - If success=true, summarize the result clearly
# # - Never expose internal errors or technical terms
# # """
# # )

# # def extract_text(content) -> str:
# #     if isinstance(content, str):
# #         return content

# #     if isinstance(content, list):
# #         return " ".join(
# #             block.get("text", "")
# #             for block in content
# #             if isinstance(block, dict)
# #         )

# #     return str(content)
# def extract_text(content):
#     """
#     Normalize LLM content to plain string.
#     Handles string | list | dict safely.
#     """
#     if content is None:
#         return ""

#     if isinstance(content, str):
#         return content.strip()

#     # Sometimes content is a list of dicts
#     if isinstance(content, list):
#         texts = []
#         for item in content:
#             if isinstance(item, dict) and "text" in item:
#                 texts.append(item["text"])
#             elif isinstance(item, str):
#                 texts.append(item)
#         return " ".join(texts).strip()

#     # If dict (JSON), return as-is or stringify
#     if isinstance(content, dict):
#         return content.get("message", "") or ""

#     return str(content)

# async def fetch_all_customer_tool(tool_name: str, token: str):
#     headers = {"Authorization": token}
#     async with httpx.AsyncClient() as client:
#         if tool_name == "fetch_all_customers":
#             try:
#                 # Increase timeout to 20 or 30 seconds if your DB is slow
#                 response = await client.get(
#                     "http://127.0.0.1:8000/all_customers", 
#                     headers=headers, 
#                     timeout=20.0
#                 )
#                 # ... rest of your logic
#                 # print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",response)
#                 if response.status_code == 401:
#                     return {
#                         "success": False,
#                         "message": "You are not authorized to view customer data."
#                     }

#                 if response.status_code != 200:
#                     return {
#                         "success": False,
#                         "message": f"Customer service returned {response.status_code}"
#                     }

#                 return {
#                     "success": True,
#                     "data": response.json()
#                 }

#             except Exception as e:
#                 return {
#                     "success": False,
#                     "message": str(e)
#                 }

#         # 👇 IMPORTANT FALLBACK
#         return {
#             "success": False,
#             "message": f"Unknown tool requested: {tool_name}"
#         }

# # async def run_ai_chat(prompt: str, user: dict, token: str) -> str:
# #     system_message = SystemMessage(
# #         content=f"""
# #         You are an AI CRM assistant.

# #         Current user role: {user.get("role", "unknown")}

# #         Rules:
# #         - Call tools only when required
# #         - Tools return structured data
# #         - If success=false, explain politely and guide the user and also provide the reason that it was not succesful
# #         - If success=true, summarize the result clearly
# #         - Never expose internal errors or technical terms
# #         """
# #         # - Return Data as it is how you get data from the database like tabular form

# #         # STRICT RULES FOR DATA DISPLAY:
# #         # - When tool returns data (list of objects):
# #         #   - Render it as a MARKDOWN TABLE
# #         #   - Table headers must match object keys exactly
# #         #   - Do NOT summarize inside table
# #         #   - Do NOT reorder columns
# #         #   - Do NOT add extra text inside the table
# #         # - Add a short summary ABOVE the table
# #             )
# #     print("----------user-----------",user)
# #     messages = [
# #         system_message,
# #         HumanMessage(content=prompt)
# #     ]

# #     # First model call
# #     ai_response = await llm_with_tools.ainvoke(messages)
# #     messages.append(ai_response)
# #     print(":::::::::::::::: ai_response ::::::::::::::::::::::",ai_response)
# #     # If tool is requested
# #     if ai_response.tool_calls:
# #         tool_call = ai_response.tool_calls[0]
# #         print("@@@@@@@@@@@@@ tool call @@@@@@@@@@@@@@@@@@@@@@ ",tool_call)
# #         tool_map = {tool.name: tool for tool in tools}
# #         print("__________tool_map_______",tool_map)
# #         tool_fn = tool_map.get(tool_call["name"])
# #         print("__________tool_fn_______",tool_fn)

# #         if tool_fn:
# #             tool_output = await call_tool_with_auth(
# #                 tool_name=tool_call["name"],
# #                 token=token
# #             )

# #             if tool_output["success"]:
# #                 return {
# #                     "message": "Customer data retrieved successfully",
# #                     "data": tool_output["data"]
# #                 }

# #             return {
# #                 "message": tool_output.get("message", "Unable to fetch customers"),
# #                 "data": None
# #             }

#     #     if tool_fn:
#     #         try:
#     #             # print("====$$$$$ tool_output $$$$$==========",tool_fn)
#     #             tool_output = await call_tool_with_auth(
#     #                 tool_name=tool_call["name"],

#     #                 token=token
#     #             )

#     #             print("===========tool_output===============",tool_output)
#     #         except Exception:
#     #             tool_output = {
#     #                 "success": False,
#     #                 "message": "Unable to complete the requested operation"
#     #             }

#     #         # VERY IMPORTANT: append real tool output
#     #         messages.append(
#     #             ToolMessage(
#     #                 tool_call_id=tool_call["id"],
#     #                 content=json.dumps({
#     #                     "success": tool_output["success"],
#     #                     "data": tool_output.get("data"), 
#     #                     "message": tool_output.get("message")
#     #                 })
#     #             )
#     #         )

#     #         final_response = await llm_with_tools.ainvoke(messages)
#     #         return final_response.content

#     # return extract_text(ai_response.content)




# # async def run_ai_chat(prompt: str, user: dict, token: str):
# #     system_message = SystemMessage(
# #         content=f"""
# #             You are an AI CRM assistant.

# #             Current user role: {user.get("role", "unknown")}

# #             Rules:
# #             - Decide when a tool is required
# #             - Tools return structured JSON
# #             - Never fabricate data
# #         """
# #     )

# #     messages = [
# #         system_message,
# #         HumanMessage(content=prompt)
# #     ]

# #     # 1️⃣ First LLM call
# #     ai_response = await llm_with_tools.ainvoke(messages)
# #     messages.append(ai_response)
# #     print("=========messages=========",messages)
# #     # 2️⃣ If tool is requested
# #     if ai_response.tool_calls:
# #         tool_call = ai_response.tool_calls[0]
# #         print("____tool call---------------",tool_call)
# #         # tool_output = await fetch_all_customer_tool(  
# #         #     tool_name=tool_call["name"],
# #         #     token=token
# #         # )

# #         # 3️⃣ Feed tool output back to LLM (MANDATORY)
# #         # messages.append(
# #         #     ToolMessage(
# #         #         tool_call_id=tool_call["id"],
# #         #         content=json.dumps(fetch_all_customers(token))
# #         #     )
# #         # )

# #         # 4️⃣ Final LLM response
# #         final_response = await llm_with_tools.ainvoke(messages)
# #         return {
# #             "message": extract_text(final_response.content),
# #             "data": None
# #         }

# #         # 🚨 IMPORTANT: return RAW structured data if present
# #         # if tool_output.get("success") and tool_output.get("data"):
# #         #     return {
# #         #         "message": "Customer data retrieved successfully",
# #         #         "data": tool_output["data"]
# #         #     }

# #         # return {
# #         #     "message": tool_output.get("message", "Operation failed"),
# #         #     "data": None
# #         # }

# #     # 5️⃣ No tool needed
# #     return {
# #         "message": extract_text(ai_response.content),
# #         "data": None
# #     }












# # async def run_ai_chat(prompt: str, user: dict, token: str):

#     # messages = [
#     #     SystemMessage(
#     #         content=f"""
#     #         You are an AI CRM assistant.
#     #         Current user role: {user.get("role", "unknown")}

#     #         Rules:
#     #         - Decide when a tool is required
#     #         - Tools return structured JSON
#     #         - NEVER expose tool calls or reasoning
#     #         - Final response must be simple user-facing text
#     #         """
#     #     ),
#     #     HumanMessage(content=prompt)
#     # ]

#     # # First invoke (may request tool)
#     # ai_response = await llm_with_tools.ainvoke(messages)
#     # messages.append(ai_response)

#     # # If tool is called → second invoke gives final answer
#     # if ai_response.tool_calls:
#     #     final_response = await llm_with_tools.ainvoke(messages)
#     #     return {
#     #         "message": extract_text(final_response.content)
#     #     }

#     # # Normal text response
#     # return {
#     #     "message": extract_text(ai_response.content)
#     # }





# # async def run_ai_chat(prompt: str, user: dict, token:str):

# #     messages = [
# #         SystemMessage(
# #             content=f"""
# #             You are an AI CRM assistant.
# #             Current user role: {user.get("role", "unknown")}
# #             Rules:
# #             - Decide when a tool is required
# #             - Tools return structured JSON
# #             - Never fabricate data
# #             """
# #         ),
# #         HumanMessage(content=prompt)
# #     ]

# #     ai_response = await llm_with_tools.ainvoke(messages)
# #     messages.append(ai_response)
# #     print("-----------------+++++++++++++++++++",ai_response)
# #     # 👇 second invoke executes tools automatically
# #     if ai_response.tool_calls:
# #         final_response = await llm_with_tools.ainvoke(messages)
# #         print(final_response)
# #         return {
# #             "message": extract_text(final_response.content)
# #         }

# #     # return {
# #     #     "message": extract_text(ai_response.content)
# #     # }
# #     print(ai_response.content)
# #     return { "message":ai_response.content}











# # async def run_ai_chat(prompt: str, user: dict, token: str):

# #     messages = [
# #         SystemMessage(
# #             content=f"""
# #             You are an AI CRM assistant.
# #             Role: {user.get("role", "unknown")}

# #             Rules:
# #             - Decide when to call a tool
# #             - NEVER explain tool execution
# #             - NEVER generate filler text
# #             - If a tool is called, return its data directly
# #             """
# #         ),
# #         HumanMessage(content=prompt)
# #     ]

# #     ai_response = await llm_with_tools.ainvoke(messages)
# #     print("---ai_responsse----------",ai_response)
# #     # 🔹 If tool was requested → EXECUTOR already ran it
    
# #     if ai_response.tool_calls[0]['name']=='fetch_all_customers':
# #         # tool_message = messages[-1]  # ToolMessage is appended automatically
# #         # print(tool_message)
# #         tool_call = ai_response.tool_calls
# #         tool_call['args'] = token
# #         final_response = await fetch_all_customers.ainvoke()
# #         print(final_response.content)
# #         return {
# #             "message": "Customers fetched successfully",
# #             "data": final_response.content  # 👈 REAL customer data
# #         }

# #     # 🔹 Normal chat response
# #     return {
# #         "message": extract_text(ai_response.content),
# #         "data": None
# #     }



# from langchain_core.messages import ToolMessage

# async def run_ai_chat(prompt: str, user: dict, token: str):
#     print("(((((((((((((Token)))))))))))))",token)
#     messages = [
#         SystemMessage(
#             content=f"""
#             You are an AI CRM assistant.
#             Role: {user.get("role", "unknown")}

#             Rules:
#             - Decide when to call a tool
#             - NEVER explain tool execution
#             - NEVER generate filler text
#             - If a tool is called, return its data directly
#             """
#         ),
#         HumanMessage(content=prompt)
#     ]

#     ai_response = await llm_with_tools.ainvoke(messages)
#     print("--- ai_response ---", ai_response)

#     # ✅ tool_calls is a LIST
#     if ai_response.tool_calls:

#         tool_call = ai_response.tool_calls[0]

#         # ✅ check tool name
#         if tool_call["name"] == "fetch_all_customers":
#             args = tool_call["args"]
#             # # ✅ correct way to pass args
#             # tool_args = {
#             #     **tool_call["args"],  # args from LLM (often empty here)
#             #     "user": user          # dependency injection
#             # }
#             args['token'] = token

#             # ✅ manually execute tool
#             tool_result = fetch_all_customers.invoke(args)

#             return {
#                 "message": "Customers fetched successfully",
#                 "data": tool_result   # REAL customer data
#             }

#     # 🔹 Normal chat response
#     return {
#         "message": extract_text(ai_response.content),
#         "data": None
#     }

