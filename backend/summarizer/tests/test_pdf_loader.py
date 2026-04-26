import pytest
from unittest.mock import patch
from backend.summarizer.services.pdf_loader import load_pdf_from_bytes
from backend.shared.extraction import ExtractionResult, PageResult, ExtractionMeta

def test_load_pdf_from_bytes():
    meta = ExtractionMeta(is_scanned=False, word_count=20, estimated_tokens=5, extraction_method="fitz")
    page1 = PageResult(page_num=1, text="Some extracted text for summarizer", char_count=34, used_vision=False)
    
    result = ExtractionResult(
        filename="uploaded_pdf",
        page_count=1,
        full_text="Some extracted text for summarizer",
        pages=[page1],
        metadata=meta
    )
    
    async def mock_extract(*args, **kwargs):
        return result

    with patch('backend.summarizer.services.pdf_loader.extract_pdf', new=mock_extract):
        docs, count = load_pdf_from_bytes(b"fake", chunk_size=100, chunk_overlap=10)
        
        assert count == 1
        assert len(docs) == 1
        assert docs[0].page_content == "Some extracted text for summarizer"
        assert docs[0].metadata["page"] == 1
