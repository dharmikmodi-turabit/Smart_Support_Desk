from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.exceptions import HTTPException

SECRET_KEY = "SUPER_SECRET_KEY_CHANGE_THIS"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    """
    Generate a signed JWT access token with expiration.

    This function creates a JSON Web Token (JWT) by:
        1. Copying the provided payload data.
        2. Adding an expiration claim ("exp") based on
           ACCESS_TOKEN_EXPIRE_MINUTES.
        3. Encoding the payload using the configured SECRET_KEY
           and ALGORITHM.

    Args:
        data (dict):
            Payload data to embed inside the JWT.
            Typically includes user identification fields
            such as user_id, email, role, or emp_id.

    Returns:
        str:
            Encoded JWT access token.

    Raises:
        HTTPException:
            500 Internal Server Error if token encoding fails.

    Notes:
        - Expiration time is calculated using UTC.
        - The "exp" claim is mandatory for token validation.
        - SECRET_KEY and ALGORITHM must be securely configured.
    """
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        raise RuntimeError(f"Failed to create access token: {e}")
