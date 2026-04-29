import pytest
import respx
import httpx
from httpx import AsyncClient
from config import settings

pytestmark = [pytest.mark.gateway, pytest.mark.unit, pytest.mark.ferpa]


@pytest.mark.asyncio
@respx.mock
async def test_proxy_rag_query_redacts_chunks(async_client: AsyncClient, auth_headers):
    # Create a project first so the gateway can resolve project_id → student_id_hash
    proj_resp = await async_client.post(
        "/api/projects",
        json={"student_id": "test-student-9001", "display_label": "Test Case"},
        headers=auth_headers,
    )
    assert proj_resp.status_code == 201, proj_resp.text
    project_id = proj_resp.json()["id"]

    # Mock downstream RAG service
    rag_url = f"{settings.services.rag_url}/query"
    mock_response = {
        "answer": "This is a mock answer",
        "chunks": [{"text": "sensitive data hidden!"}],
        "mode": "fast",
        "top_k": 3,
        "sources": [],
    }
    respx.post(rag_url).mock(return_value=httpx.Response(200, json=mock_response))

    response = await async_client.post(
        "/api/rag/query",
        json={"question": "test", "project_id": project_id},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    # FERPA compliance — raw chunks must be stripped before reaching client
    assert "chunks" not in data


@pytest.mark.asyncio
async def test_rag_query_requires_project_id(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/rag/query",
        json={"question": "test"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "project_id" in response.json()["detail"]
