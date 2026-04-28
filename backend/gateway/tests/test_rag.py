import pytest
import respx
import httpx
from httpx import AsyncClient
from config import settings

pytestmark = [pytest.mark.gateway, pytest.mark.unit, pytest.mark.ferpa]

@pytest.mark.asyncio
@respx.mock
async def test_proxy_rag_query_redacts_chunks(async_client: AsyncClient, auth_headers):
    # Mock downstream RAG service
    rag_url = f"{settings.services.rag_url}/query"
    
    mock_response = {
        "answer": "This is a mock answer",
        "chunks": [{"text": "sensitive data hidden!"}],
        "mode": "fast",
        "top_k": 3
    }
    respx.post(rag_url).mock(return_value=httpx.Response(200, json=mock_response))
    
    response = await async_client.post(
        "/api/rag/query",
        json={"question": "test", "student_id": "1234567"},
        headers=auth_headers,
    )

    # Assert successful forward
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    # Assert FERPA compliance — chunk redaction
    assert "chunks" not in data


@pytest.mark.asyncio
async def test_rag_query_requires_student_id(async_client: AsyncClient, auth_headers):
    response = await async_client.post(
        "/api/rag/query",
        json={"question": "test"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "student_id" in response.json()["detail"]
