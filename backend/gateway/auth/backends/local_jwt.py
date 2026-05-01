import os
from typing import Dict, Any
from jose import jwt, JWTError
from .base import BaseAuthBackend

ACCESS_TOKEN_EXPIRE_MINUTES = 8 * 60
ALGORITHM = "HS256"

class LocalJWTBackend(BaseAuthBackend):
    def __init__(self):
        self.secret_key = os.environ.get("JWT_SECRET")
        if not self.secret_key:
            raise RuntimeError("JWT_SECRET environment variable is not set.")

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise ValueError("Token missing 'sub' claim")
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
