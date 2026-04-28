"""
Basic smoke tests for the Summarizer service.
Run with: pytest tests/ -v

These tests do NOT require Ollama or a real PDF. They verify the FastAPI
app boots and the health endpoint responds correctly.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

pytestmark = [pytest.mark.summarizer, pytest.mark.unit]

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_payload():
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "summarizer"


def test_summarize_requires_input():
    """Calling /summarize with no file and no document_id must return 422."""
    response = client.post("/summarize")
    assert response.status_code == 422


def test_summarize_rejects_non_pdf(tmp_path):
    """Uploading a non-PDF file must return 422."""
    fake_file = tmp_path / "test.txt"
    fake_file.write_text("not a pdf")
    with open(fake_file, "rb") as f:
        response = client.post(
            "/summarize", files={"file": ("test.txt", f, "text/plain")})
    assert response.status_code == 422



