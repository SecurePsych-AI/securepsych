import uuid as _uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
import os

from .backends.local_jwt import ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from db import AsyncSessionLocal, crud

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
    if req.username != _GATEWAY_USERNAME or req.password != _GATEWAY_PASSWORD:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    secret_key = os.environ["JWT_SECRET"]
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            user = await crud.get_or_create_user_by_username(
                session, req.username, role="psychologist"
            )
            user_id = user.id

    to_encode = {
        "sub": user_id,
        "username": req.username,
        "role": "psychologist",
        "jti": str(_uuid.uuid4()),
        "exp": expire,
    }
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return {"access_token": encoded_jwt, "token_type": "bearer"}


class LogoutRequest(BaseModel):
    token: str

@router.post("/logout")
async def logout(req: LogoutRequest):
    secret_key = os.environ["JWT_SECRET"]
    try:
        payload = jwt.decode(req.token, secret_key, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        raise HTTPException(status_code=400, detail="Token missing required claims")

    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await crud.revoke_token(session, jti, expires_at)

    return {"status": "ok", "detail": "Token revoked"}
