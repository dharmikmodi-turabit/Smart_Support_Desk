from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.exceptions import HTTPException

SECRET_KEY = "SUPER_SECRET_KEY_CHANGE_THIS"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    """
    Create a JWT access token with an expiration time.

    This function generates a JSON Web Token (JWT) containing the provided
    payload (`data`) and an expiration timestamp. The token is signed using
    the configured secret key and algorithm.

    Args:
    - data (dict): The payload to encode in the JWT. Typically includes
      user identifiers, roles, or other claims. Sensitive information
      (like passwords) should not be included.

    Returns:
    - str: Encoded JWT as a string.

    Raises:
    - RuntimeError: If an error occurs during token creation.
    """

    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        raise RuntimeError(f"Failed to create access token: {e}")
