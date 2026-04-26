import pytest
import respx
import httpx
from httpx import AsyncClient
from config import settings

@pytest.mark.asyncio
@respx.mock
async def test_summarizer_mode_b_document_id(async_client: AsyncClient, auth_headers):
    # Mode B testing: lookup ID via JSON, pass doc text as form data
    doc_id = "mock-uuid-1234"
    rag_url = f"{settings.services.rag_url}/documents/{doc_id}/content"
    summarizer_url = f"{settings.services.summarizer_url}/summarize"
    
    # Mock RAG response
    respx.get(rag_url).mock(return_value=httpx.Response(200, json={
        "document_id": doc_id,
        "text": "Extracted text content from RAG",
        "page_count": 5
    }))
    
    # Mock Summarizer response
    respx.post(summarizer_url).mock(return_value=httpx.Response(200, json={
        "summary": "This is an expected mock summary.",
        "page_count": 5
    }))
    
    response = await async_client.post("/api/summarize", json={"document_id": doc_id}, headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["summary"] == "This is an expected mock summary."
