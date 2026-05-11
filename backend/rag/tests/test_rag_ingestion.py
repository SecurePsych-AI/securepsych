import pytest
from unittest.mock import patch
from backend.rag.ingestion import extract_pages, ingest_pdf_bytes
from backend.shared.extraction import ExtractionResult, PageResult, ExtractionMeta

pytestmark = pytest.mark.rag


def _passthrough_redact(text, counters, entity_map):
    """Identity stand-in for redact_page — no spaCy required."""
    return text


@pytest.mark.unit
def test_extract_pages_with_boilerplate():
    meta = ExtractionMeta(is_scanned=False, word_count=20, estimated_tokens=5, extraction_method="fitz")

    page1 = PageResult(page_num=1, text="CONFIDENTIAL REPORT HEADER\nHere is valid text one.\nPAGE NUMBER FOOTER", char_count=100, used_vision=False)
    page2 = PageResult(page_num=2, text="CONFIDENTIAL REPORT HEADER\nHere is valid text two.\nPAGE NUMBER FOOTER", char_count=100, used_vision=False)
    page3 = PageResult(page_num=3, text="CONFIDENTIAL REPORT HEADER\nHere is valid text three.\nPAGE NUMBER FOOTER", char_count=100, used_vision=False)

    result = ExtractionResult(
        filename="test.pdf",
        page_count=3,
        full_text="...",
        pages=[page1, page2, page3],
        metadata=meta,
    )

    async def mock_extract(*args, **kwargs):
        return result

    with patch('backend.rag.ingestion.extract_pdf', new=mock_extract), \
         patch('backend.rag.ingestion.redact_page', side_effect=_passthrough_redact):
        pages, entity_map = extract_pages(b"fake", "test.pdf")

        assert len(pages) == 3
        # Ensure boilerplate is stripped
        assert "CONFIDENTIAL REPORT HEADER" not in pages[0]["text"]
        assert "PAGE NUMBER FOOTER" not in pages[1]["text"]
        assert "Here is valid text one." in pages[0]["text"]
        assert isinstance(entity_map, dict)


@pytest.mark.integration
@pytest.mark.requires_spacy
def test_extract_pages_redacts_real_name():
    meta = ExtractionMeta(is_scanned=False, word_count=20, estimated_tokens=5, extraction_method="fitz")
    page1 = PageResult(
        page_num=1,
        text="Student: Marcus Johnson\nDate of Birth: 1/15/2012\nHere is clinical text.",
        char_count=70,
        used_vision=False,
    )
    result = ExtractionResult(
        filename="test_pii.pdf",
        page_count=1,
        full_text="...",
        pages=[page1],
        metadata=meta,
    )

    async def mock_extract(*args, **kwargs):
        return result

    with patch('backend.rag.ingestion.extract_pdf', new=mock_extract):
        pages, entity_map = extract_pages(b"fake", "test_pii.pdf")
        assert len(pages) == 1
        assert "Marcus Johnson" not in pages[0]["text"]
        assert "STUDENT_NAME_1" in pages[0]["text"]


@pytest.mark.integration
@pytest.mark.requires_spacy
def test_extract_pages_entity_map_populated():
    meta = ExtractionMeta(is_scanned=False, word_count=20, estimated_tokens=5, extraction_method="fitz")
    page1 = PageResult(
        page_num=1,
        text="Student: Marcus Johnson was evaluated for learning disabilities.",
        char_count=65,
        used_vision=False,
    )
    result = ExtractionResult(
        filename="test_map.pdf",
        page_count=1,
        full_text="...",
        pages=[page1],
        metadata=meta,
    )

    async def mock_extract(*args, **kwargs):
        return result

    with patch('backend.rag.ingestion.extract_pdf', new=mock_extract):
        pages, entity_map = extract_pages(b"fake", "test_map.pdf")
        assert "Marcus Johnson" in entity_map.values()


@pytest.mark.integration
@pytest.mark.requires_spacy
def test_extract_pages_real_pdf(redacted_eval_pdf_1):
    """Full extraction + PII redaction pipeline on a hand-scrubbed eval PDF (no Ollama)."""
    pages, entity_map = extract_pages(
        redacted_eval_pdf_1.read_bytes(), redacted_eval_pdf_1.name
    )
    assert len(pages) > 0
    assert all(p["text"] for p in pages)
    assert isinstance(entity_map, dict)


@pytest.mark.ai
@pytest.mark.rag
def test_ingest_produces_chunks(redacted_eval_pdf_1):
    """Ingest a real PDF end-to-end and verify at least one chunk is stored in ChromaDB."""
    result = ingest_pdf_bytes(
        redacted_eval_pdf_1.read_bytes(),
        "redacted_eval_1.pdf",
        "test-student-001",
        "standard",
    )
    assert result["status"] == "ok"
    assert result["chunks_added"] > 0
