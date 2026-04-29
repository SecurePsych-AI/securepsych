import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

# Load the gateway .env first so all required secrets come from there.
# Explicit path prevents CWD-dependent lookup failures.
load_dotenv(Path(__file__).parent.parent / ".env")

# Must be set BEFORE any gateway module is imported — engine.py reads
# GATEWAY_DB_PATH at import time and enforces the LUKS path boundary.
# SECUREPSYCH_ENV=test suspends that check so tests can use a temp file.
os.environ["SECUREPSYCH_ENV"] = "test"

_test_db_fd, _test_db_path = tempfile.mkstemp(prefix="securepsych_gw_test_", suffix=".db")
os.close(_test_db_fd)
os.environ["GATEWAY_DB_PATH"] = _test_db_path

import sys
import pytest
import pytest_asyncio
import httpx
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from auth.backends.local_jwt import ALGORITHM
from db.engine import create_all_tables
from jose import jwt
from datetime import datetime, timedelta, timezone


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _setup_test_db():
    # ASGITransport does not fire lifespan events, so we create tables explicitly.
    await create_all_tables()
    yield
    try:
        os.unlink(_test_db_path)
    except FileNotFoundError:
        pass


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
