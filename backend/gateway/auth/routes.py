from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from jose import jwt
import os

from .backends.local_jwt import ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from .store import token_denylist

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

_GATEWAY_USERNAME = os.environ.get("GATEWAY_USERNAME")
_GATEWAY_PASSWORD = os.environ.get("GATEWAY_PASSWORD")
if not _GATEWAY_USERNAME or not _GATEWAY_PASSWORD:
    raise RuntimeError("GATEWAY_USERNAME and GATEWAY_PASSWORD must be set in environment.")

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    if req.username == _GATEWAY_USERNAME and req.password == _GATEWAY_PASSWORD:
        secret_key = os.environ["JWT_SECRET"]
        
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": "mock-uuid-1234",  # A mock user UUID for FERPA
            "role": "psychologist",
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
        return {"access_token": encoded_jwt, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

class LogoutRequest(BaseModel):
    token: str

@router.post("/logout")
async def logout(req: LogoutRequest):
    # Depending on client setup, token could be pulled from Auth header instead of body
    token_denylist.add(req.token)
    return {"status": "ok", "detail": "Token added to denylist"}
