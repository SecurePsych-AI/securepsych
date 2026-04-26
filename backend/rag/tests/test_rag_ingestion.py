import pytest
from unittest.mock import patch
from backend.rag.ingestion import extract_pages
from backend.shared.extraction import ExtractionResult, PageResult, ExtractionMeta

def test_extract_pages_with_boilerplate():
    # Setup mock shared extraction result
    meta = ExtractionMeta(is_scanned=False, word_count=20, estimated_tokens=5, extraction_method="fitz")
    
    page1 = PageResult(page_num=1, text="CONFIDENTIAL REPORT HEADER\nHere is valid text one.\nPAGE NUMBER FOOTER", char_count=100, used_vision=False)
    page2 = PageResult(page_num=2, text="CONFIDENTIAL REPORT HEADER\nHere is valid text two.\nPAGE NUMBER FOOTER", char_count=100, used_vision=False)
    page3 = PageResult(page_num=3, text="CONFIDENTIAL REPORT HEADER\nHere is valid text three.\nPAGE NUMBER FOOTER", char_count=100, used_vision=False)
    
    result = ExtractionResult(
        filename="test.pdf",
        page_count=3,
        full_text="...",
        pages=[page1, page2, page3],
        metadata=meta
    )

    async def mock_extract(*args, **kwargs):
        return result

    with patch('backend.rag.ingestion.extract_pdf', new=mock_extract):
        pages = extract_pages(b"fake", "test.pdf")
        
        assert len(pages) == 3
        # Ensure boilerplate is stripped
        assert "CONFIDENTIAL REPORT HEADER" not in pages[0]["text"]
        assert "PAGE NUMBER FOOTER" not in pages[1]["text"]
        assert "Here is valid text one." in pages[0]["text"]
