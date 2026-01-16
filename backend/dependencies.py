from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from auth import SECRET_KEY, ALGORITHM
from redis_client import redis_client

security = HTTPBearer()

def get_current_user(credentials=Depends(security)):
    token = credentials.credentials

    # Redis check (LOGOUT protection)
    if not redis_client.exists(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or logged out"
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def admin_required(user=Depends(get_current_user)):
    if user["role"] != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user

def admin_agent_required(user=Depends(get_current_user)):
    if user["role"] not in ["Admin","Agent"]:
        raise HTTPException(
            status_code=403,
            detail="Admin or Agent access required"
        )
    return user

def service_person_required(user=Depends(get_current_user)):
    if user["role"] != "Service Person":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Service Person access required"
        )
    return user

def employee_create_permission(user=Depends(get_current_user)):
    role = user["role"]

    if role not in ["Admin", "Agent"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to create employees"
        )

    return user
