import pytest
import pytest_asyncio
import httpx
import sys
import os
from dotenv import load_dotenv
load_dotenv()

# Ensure the gateway backend directory is in the PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from auth.backends.local_jwt import ALGORITHM
import os
from jose import jwt
from datetime import datetime, timedelta, timezone

@pytest_asyncio.fixture
async def async_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

@pytest.fixture
def auth_token():
    secret_key = os.environ.get("JWT_SECRET", "super-secret-default-key-for-dev")
    expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode = {"sub": "test-user", "role": "admin", "exp": expire}
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)

@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
