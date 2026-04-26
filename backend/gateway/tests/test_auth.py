import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check_no_auth(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_protected_route_requires_auth(async_client: AsyncClient):
    response = await async_client.get("/api/rag/documents")
    assert response.status_code == 401
    
@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    response = await async_client.post("/api/auth/login", json={"username": "test", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()
