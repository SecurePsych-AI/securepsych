import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

_SAMPLE_OUTPUT = "Your child has some challenges with reading but is making great progress."


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "jargon"}


def test_simplify_default_level():
    with patch("routes.simplify.run_simplify_chain", new=AsyncMock(return_value=_SAMPLE_OUTPUT)):
        resp = client.post("/simplify", json={"text": "The student demonstrates phonological deficits."})
    assert resp.status_code == 200
    body = resp.json()
    assert body["level"] == 3
    assert body["simplified_text"] == _SAMPLE_OUTPUT
    assert isinstance(body["flesch_kincaid_grade"], float)


@pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
def test_simplify_all_levels_succeed(level):
    with patch("routes.simplify.run_simplify_chain", new=AsyncMock(return_value=_SAMPLE_OUTPUT)):
        resp = client.post("/simplify", json={"text": "Sample clinical text.", "level": level})
    assert resp.status_code == 200
    assert resp.json()["level"] == level


def test_simplify_correct_template_passed():
    """Verify the route passes the template for the requested level, not a different one."""
    captured = {}

    async def capture_chain(text: str, template: str) -> str:
        captured["template"] = template
        return _SAMPLE_OUTPUT

    with patch("routes.simplify.run_simplify_chain", new=capture_chain):
        client.post("/simplify", json={"text": "text", "level": 2})

    assert "{text}" in captured["template"]
    # Level 2 prompt contains "acronym" as a distinctive marker
    assert "acronym" in captured["template"].lower()


def test_level_zero_rejected():
    resp = client.post("/simplify", json={"text": "Sample text.", "level": 0})
    assert resp.status_code == 422


def test_level_six_rejected():
    resp = client.post("/simplify", json={"text": "Sample text.", "level": 6})
    assert resp.status_code == 422


def test_missing_text_rejected():
    resp = client.post("/simplify", json={"level": 3})
    assert resp.status_code == 422


def test_fk_grade_in_response():
    """FK grade should be computed from the LLM output, not the input."""
    with patch("routes.simplify.run_simplify_chain", new=AsyncMock(return_value="The cat sat. The dog ran.")):
        resp = client.post("/simplify", json={"text": "ignored", "level": 3})
    assert resp.status_code == 200
    assert isinstance(resp.json()["flesch_kincaid_grade"], float)


def test_simplify_pdf_upload(tmp_path):
    fake_pdf = tmp_path / "report.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 fake content")

    mock_result = MagicMock()
    mock_result.full_text = "The student has significant reading difficulties."

    with patch("routes.simplify.extract_pdf", new=AsyncMock(return_value=mock_result)), \
         patch("routes.simplify.run_simplify_chain", new=AsyncMock(return_value="Your child struggles with reading.")):
        with open(fake_pdf, "rb") as f:
            resp = client.post(
                "/simplify",
                files={"file": ("report.pdf", f, "application/pdf")},
                data={"level": "3"},
            )

    assert resp.status_code == 200
    body = resp.json()
    assert body["level"] == 3
    assert body["simplified_text"] == "Your child struggles with reading."
    assert isinstance(body["flesch_kincaid_grade"], float)


def test_simplify_pdf_empty_text_rejected(tmp_path):
    fake_pdf = tmp_path / "blank.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 blank")

    mock_result = MagicMock()
    mock_result.full_text = "   "  # whitespace only — no extractable text

    with patch("routes.simplify.extract_pdf", new=AsyncMock(return_value=mock_result)):
        with open(fake_pdf, "rb") as f:
            resp = client.post(
                "/simplify",
                files={"file": ("blank.pdf", f, "application/pdf")},
                data={"level": "3"},
            )

    assert resp.status_code == 422


def test_simplify_pdf_invalid_level_rejected(tmp_path):
    fake_pdf = tmp_path / "report.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 fake")

    with open(fake_pdf, "rb") as f:
        resp = client.post(
            "/simplify",
            files={"file": ("report.pdf", f, "application/pdf")},
            data={"level": "9"},
        )

    assert resp.status_code == 422


def test_simplify_unsupported_content_type():
    resp = client.post("/simplify", content=b"plain text", headers={"content-type": "text/plain"})
    assert resp.status_code == 415
