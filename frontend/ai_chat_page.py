# import streamlit as st
# from api import api_call
# import pandas as pd
# # from ..backend.ai_engine import run_ai_chat

# def ai_chatbot_page():
#     st.subheader("🤖 AI CRM Assistant")
#     st.caption("Ask questions about tickets, customers, and support operations")

#     if "ai_chat_history" not in st.session_state:
#         st.session_state.ai_chat_history = []
#     for msg in st.session_state.ai_chat_history:
#         with st.chat_message(msg["role"]):
#             if "table" in msg.keys():
#                 st.markdown(msg["content"])
#                 st.dataframe(
#                     pd.DataFrame(msg["table"]),
#                     use_container_width=True,
#                     hide_index=True
#                 )
#             elif "data" in msg.keys():
#                 st.markdown(msg["content"])
#                 st.dataframe(
#                     pd.DataFrame(msg["data"]),
#                     use_container_width=True,
#                     hide_index=True
#                 )

#             else:
#                 st.markdown(msg["content"])

#     # Chat input
#     user_prompt = st.chat_input("Ask something...")

#     if user_prompt:
#         # Store user message
#         st.session_state.ai_chat_history.append({
#             "role": "user",
#             "content": user_prompt
#         })

#         with st.chat_message("user"):
#             st.markdown(user_prompt)

#         # Call AI
#         with st.chat_message("assistant"):
#             with st.spinner("Thinking..."):
#                 ai_response = api_call(
#                 "POST",
#                 "/ai/chat",
#                 st.session_state["token"],
#                 {
#                     "prompt" : user_prompt
#                 }

#                 )
#                 print("^^^^^^^^^^^^^^ ai_response ^^^^^^^^^^^^^^^^^",ai_response)
                
#                 if ai_response is None:
#                     st.error("Backend returned no response (None)")
#                     return
#                 if isinstance(ai_response, dict) and ai_response.get("data") is not None:
#                     # Tool / table response
#                     rows = ai_response["data"]
#                     message = ai_response["message"]

#                     st.markdown(message)
#                     df = pd.DataFrame(rows)
#                     st.dataframe(df, use_container_width=True, hide_index=True)

#                     st.session_state.ai_chat_history.append({
#                         "role": "assistant",
#                         "content": message,
#                         "data": rows
#                     })

#                 else:
#                     # Normal text response
#                     message = ai_response['message']

#                     st.markdown(message)

#                     st.session_state.ai_chat_history.append({
#                         "role": "assistant",
#                         "content": message
#                     })


import streamlit as st
from api import api_call
import pandas as pd
import plotly.express as px


def ai_chatbot_page():
    st.subheader("🤖 AI CRM Assistant")
    st.caption("Ask questions about tickets, customers, and support operations")

    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    # -------- Render history --------
    # for msg in st.session_state.ai_chat_history:
    #     with st.chat_message(msg["role"]):

    #         if msg.get("analysis"):
    #             st.markdown(msg["content"])

    #             analysis = msg["analysis"]

    #             chart_df = pd.DataFrame({
    #                 "Status": ["Open", "In Progress", "Closed"],
    #                 "Count": [
    #                     analysis["Opened_ticket_count"],
    #                     analysis["in_progress_ticket_count"],
    #                     analysis["Closed_ticket_count"]
    #                 ]
    #             })

    #             fig = px.pie(chart_df, names="Status", values="Count", hole=0.55)
    #             st.plotly_chart(fig, use_container_width=True)

    #         elif "data" in msg:
    #             st.markdown(msg["content"])
    #             st.dataframe(pd.DataFrame(msg["data"]), use_container_width=True, hide_index=True)

    #         else:
    #             st.markdown(msg["content"])
    for msg in st.session_state.ai_chat_history:
        with st.chat_message(msg["role"]):

            # -------- ANALYTICS HISTORY --------
            if "analysis" in msg:
                st.markdown(msg["content"])

                data = msg["analysis"]

                chart_df = pd.DataFrame({
                    "Status": ["Open", "In Progress", "Closed"],
                    "Count": [
                        data["Opened_ticket_count"],
                        data["in_progress_ticket_count"],
                        data["Closed_ticket_count"]
                    ]
                })

                fig = px.pie(chart_df, names="Status", values="Count", hole=0.55)
                st.plotly_chart(fig, use_container_width=True)

            # -------- TABLE HISTORY --------
            elif "data" in msg:
                st.markdown(msg["content"])
                st.dataframe(pd.DataFrame(msg["data"]), use_container_width=True, hide_index=True)

            else:
                st.markdown(msg["content"])

    # -------- Chat input --------
    user_prompt = st.chat_input("Ask something...")

    if user_prompt:
        st.session_state.ai_chat_history.append({
            "role": "user",
            "content": user_prompt
        })

        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ai_response = api_call(
                    "POST",
                    "/ai/chat",
                    st.session_state["token"],
                    {"prompt": user_prompt}
                )

                if ai_response is None:
                    st.error("Backend returned no response")
                    return

                message = ai_response.get("message", "")
                data = ai_response.get("data")
                print("_______________-------------------",ai_response)
                print("_______________-------------------",data)

                # -------- ANALYTICS RESPONSE --------
                if "analytics" in message:
                    print("1",data)
                    # if backend sends list -> take first item
                    if isinstance(data, list):
                        data = data[0]
                    print("2",data)

                    st.markdown(message)

                    chart_df = pd.DataFrame({
                        "Status": ["Open", "In Progress", "Closed"],
                        "Count": [
                            data["Opened_ticket_count"],
                            data["in_progress_ticket_count"],
                            data["Closed_ticket_count"]
                        ]
                    })

                    fig = px.pie(chart_df, names="Status", values="Count", hole=0.55)
                    st.plotly_chart(fig, use_container_width=True)

                    st.session_state.ai_chat_history.append({
                        "role": "assistant",
                        "content": message,
                        "analysis": data
                    })


                # -------- TABLE RESPONSE --------
                elif isinstance(data, list):
                    st.markdown(message)
                    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

                    st.session_state.ai_chat_history.append({
                        "role": "assistant",
                        "content": message,
                        "data": data
                    })

                # -------- TEXT RESPONSE --------
                else:
                    st.markdown(message)

                    st.session_state.ai_chat_history.append({
                        "role": "assistant",
                        "content": message
                    })
