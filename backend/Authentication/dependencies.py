from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from auth import SECRET_KEY, ALGORITHM
from redis_client import redis_client

security = HTTPBearer()

def get_current_user(credentials=Depends(security)):
    """
    Retrieve and validate the current user from a JWT access token.

    This function extracts the JWT from the provided credentials, verifies
    its validity, and checks that the token is still active in Redis (to
    protect against logout). If valid, it decodes the token payload and
    returns it.

    Dependencies:
    - security: FastAPI dependency providing the Authorization header.
    - redis_client: Redis instance used to track active tokens.
    - SECRET_KEY and ALGORITHM: Used for JWT decoding.

    Args:
    - credentials (Depends): FastAPI security dependency providing token.

    Returns:
    - dict: Decoded JWT payload containing user information and claims.

    Raises:
    - HTTPException (401): If the token is expired, logged out, or invalid.
    """

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
    """
    Authorize that the current user is a customer.

    This function decodes a JWT access token from the provided credentials
    and ensures that the user's role is "Customer". It raises an
    HTTPException if the token is invalid or if the user does not have
    customer privileges.

    Dependencies:
    - security: FastAPI security dependency providing the Authorization header.
    - SECRET_KEY and ALGORITHM: Used for JWT decoding.

    Args:
    - credentials (Depends): FastAPI security dependency providing token.

    Returns:
    - dict: Decoded JWT payload containing user information and claims.

    Raises:
    - HTTPException (401): If the JWT token is invalid.
    - HTTPException (403): If the user is authenticated but not a customer.
    """

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
    """
    Authorize that the current user is a Customer, Agent, or Admin.

    This function decodes a JWT access token from the provided credentials
    and ensures that the user's role is one of "Customer", "Agent", or "Admin".
    It raises an HTTPException if the token is invalid or if the user does not
    have the required role.

    Dependencies:
    - security: FastAPI security dependency providing the Authorization header.
    - SECRET_KEY and ALGORITHM: Used for JWT decoding.

    Args:
    - credentials (Depends): FastAPI security dependency providing token.

    Returns:
    - dict: Decoded JWT payload containing user information and claims.

    Raises:
    - HTTPException (401): If the JWT token is invalid.
    - HTTPException (403): If the user is authenticated but does not have
      one of the allowed roles.
    """

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
    """
    Authorize that the current user is an Admin.

    This function checks the role in the decoded JWT payload (retrieved
    from the `get_current_user` dependency) and ensures that the user
    has an Admin role. If not, it raises an HTTPException.

    Dependencies:
    - get_current_user: Dependency that retrieves and validates the current
      user from JWT.

    Args:
    - user (dict, Depends): Decoded JWT payload from the current user.

    Returns:
    - dict: The decoded JWT payload of the Admin user.

    Raises:
    - HTTPException (403): If the user is authenticated but does not have
      the Admin role.
    - HTTPException (500): If an unexpected error occurs.
    """

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
    """
    Authorize that the current user is an Admin or Agent.

    This function checks the role in the decoded JWT payload (retrieved
    from the `get_current_user` dependency) and ensures that the user
    has either the Admin or Agent role. If not, it raises an HTTPException.

    Dependencies:
    - get_current_user: Dependency that retrieves and validates the current
      user from JWT.

    Args:
    - user (dict, Depends): Decoded JWT payload of the current user.

    Returns:
    - dict: The decoded JWT payload of the Admin or Agent user.

    Raises:
    - HTTPException (403): If the user is authenticated but does not have
      Admin or Agent role.
    - HTTPException (500): If an unexpected error occurs.
    """

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
    """
    Authorize that the current user is a Service Person.

    This function checks the role in the decoded JWT payload (retrieved
    from the `get_current_user` dependency) and ensures that the user
    has the "Service Person" role. It raises an HTTPException if the user
    does not have the required role.

    Dependencies:
    - get_current_user: Dependency that retrieves and validates the current
      user from JWT.

    Args:
    - user (dict, Depends): Decoded JWT payload of the current user.

    Returns:
    - dict: The decoded JWT payload of the Service Person user.

    Raises:
    - HTTPException (403): If the user is authenticated but does not have
      the Service Person role.
    - HTTPException (500): If an unexpected error occurs.
    """
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
    """
    Authorize that the current user can create employee records.

    This function checks the role in the decoded JWT payload (retrieved
    from the `get_current_user` dependency) and ensures that the user
    has either the Admin or Agent role. Only these roles are allowed
    to create new employees. An HTTPException is raised if the role
    is not permitted.

    Dependencies:
    - get_current_user: Dependency that retrieves and validates the current
      user from JWT.

    Args:
    - user (dict, Depends): Decoded JWT payload of the current user.

    Returns:
    - dict: The decoded JWT payload of the authorized user.

    Raises:
    - HTTPException (403): If the user is authenticated but not allowed
      to create employees.
    - HTTPException (500): If an unexpected error occurs.
    """

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
