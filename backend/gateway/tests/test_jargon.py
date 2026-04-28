import pytest
import respx
import httpx
from httpx import AsyncClient
from config import settings

pytestmark = [pytest.mark.gateway, pytest.mark.unit]

JARGON_URL = f"{settings.services.jargon_url}/simplify"

_MOCK_RESPONSE = {
    "simplified_text": "Your child has some challenges with reading but is making great progress.",
    "flesch_kincaid_grade": 6.2,
    "level": 3,
}


@pytest.mark.asyncio
@respx.mock
async def test_jargon_simplify_happy_path(async_client: AsyncClient, auth_headers):
    respx.post(JARGON_URL).mock(return_value=httpx.Response(200, json=_MOCK_RESPONSE))

    response = await async_client.post(
        "/api/jargon/simplify",
        json={"text": "The student demonstrates phonological processing deficits.", "level": 3},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["simplified_text"] == _MOCK_RESPONSE["simplified_text"]
    assert body["flesch_kincaid_grade"] == _MOCK_RESPONSE["flesch_kincaid_grade"]
    assert body["level"] == 3


@pytest.mark.asyncio
async def test_jargon_simplify_requires_auth(async_client: AsyncClient):
    response = await async_client.post(
        "/api/jargon/simplify",
        json={"text": "Some clinical text.", "level": 3},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
@respx.mock
async def test_jargon_forwards_level_in_body(async_client: AsyncClient, auth_headers):
    """Verify the gateway passes the full request body (including level) to the jargon service."""
    captured = {}

    def capture_request(request: httpx.Request) -> httpx.Response:
        import json
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={**_MOCK_RESPONSE, "level": captured["body"]["level"]})

    respx.post(JARGON_URL).mock(side_effect=capture_request)

    await async_client.post(
        "/api/jargon/simplify",
        json={"text": "Clinical text.", "level": 2},
        headers=auth_headers,
    )

    assert captured["body"]["level"] == 2
    assert captured["body"]["text"] == "Clinical text."


@pytest.mark.asyncio
@respx.mock
async def test_jargon_injects_user_id_header(async_client: AsyncClient, auth_headers):
    """X-User-ID must be forwarded to the jargon service — FERPA access trail."""
    captured_headers = {}

    def capture_headers(request: httpx.Request) -> httpx.Response:
        captured_headers.update(dict(request.headers))
        return httpx.Response(200, json=_MOCK_RESPONSE)

    respx.post(JARGON_URL).mock(side_effect=capture_headers)

    await async_client.post(
        "/api/jargon/simplify",
        json={"text": "Clinical text.", "level": 3},
        headers=auth_headers,
    )

    assert "x-user-id" in captured_headers, "X-User-ID header missing — FERPA access trail broken"


@pytest.mark.asyncio
@respx.mock
async def test_jargon_multipart_passthrough(async_client: AsyncClient, auth_headers):
    """Gateway should forward multipart PDF uploads to the jargon service."""
    respx.post(JARGON_URL).mock(return_value=httpx.Response(200, json=_MOCK_RESPONSE))

    resp = await async_client.post(
        "/api/jargon/simplify",
        files={"file": ("report.pdf", b"%PDF-1.4 fake", "application/pdf")},
        data={"level": "3"},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    assert resp.json()["level"] == 3


@pytest.mark.asyncio
@respx.mock
async def test_jargon_passes_through_downstream_error(async_client: AsyncClient, auth_headers):
    """Validation errors from the jargon service (e.g. level out of range) must pass through."""
    respx.post(JARGON_URL).mock(
        return_value=httpx.Response(422, json={"detail": "level must be between 1 and 5"})
    )

    response = await async_client.post(
        "/api/jargon/simplify",
        json={"text": "Clinical text.", "level": 9},
        headers=auth_headers,
    )

    assert response.status_code == 422
