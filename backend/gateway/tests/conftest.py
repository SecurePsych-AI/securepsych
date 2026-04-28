import os

# Set test-credential defaults BEFORE load_dotenv.
# load_dotenv() does not override already-set env vars, so a real .env
# (if present in the gateway directory) still takes precedence.
os.environ.setdefault("GATEWAY_USERNAME", "test")
os.environ.setdefault("GATEWAY_PASSWORD", "password")
os.environ.setdefault("JWT_SECRET", "super-secret-default-key-for-dev")

from dotenv import load_dotenv
load_dotenv()

import sys
import pytest
import pytest_asyncio
import httpx
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from auth.backends.local_jwt import ALGORITHM
from jose import jwt
from datetime import datetime, timedelta, timezone


@pytest_asyncio.fixture
async def async_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def auth_token():
    secret_key = os.environ["JWT_SECRET"]
    expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode = {"sub": "test-user", "role": "admin", "exp": expire}
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
