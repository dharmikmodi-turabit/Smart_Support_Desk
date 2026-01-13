from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from auth import SECRET_KEY, ALGORITHM
from redis_client import redis_client

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        emp_id = payload.get("emp_id")

        if not redis_client.exists(token):
            raise HTTPException(status_code=401, detail="Session expired")

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
    if user["role"] != "Admin" or user["role"] != "Agent":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user
