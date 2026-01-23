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

def customer_required(credentials=Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("role") != "Customer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customer access only"
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
def admin_agent_customer_required(credentials=Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("role") not in ["Customer", "Agent","Admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customer access only"
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def admin_required(user=Depends(get_current_user)):
    try:
        if user["role"] != "Admin":
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )
        return user
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )

def admin_agent_required(user=Depends(get_current_user)):
    try:
        if user["role"] not in ["Admin","Agent"]:
            raise HTTPException(
                status_code=403,
                detail="Admin or Agent access required"
            )
        return user
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )

def service_person_required(user=Depends(get_current_user)):
    try:
        if user["role"] != "Service Person":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Service Person access required"
            )
        return user
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )

def employee_create_permission(user=Depends(get_current_user)):
    try:
        role = user["role"]

        if role not in ["Admin", "Agent"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to create employees"
            )

        return user
    except Exception as e:
        raise HTTPException(
        status_code=500,
        detail=str(e)
    )
