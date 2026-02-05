from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from ai_engine import run_ai_chat
from dependencies import get_current_user
import streamlit as st

ai_chat_router = APIRouter(prefix="/ai", tags=["AI Chatbot"])


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str


@ai_chat_router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    payload: ChatRequest,
    user=Depends(get_current_user)
):
    # token = request.headers.get("Authorization")
    # print("====================token==============",token)
    response = await run_ai_chat(
        prompt=payload.prompt,
        user=user,
        token=st.session_state["token"]
    )
    return ChatResponse(response=response)
