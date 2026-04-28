import pytest
from unittest.mock import patch, MagicMock
from backend.shared.extraction import extract_pdf

pytestmark = [pytest.mark.unit]

@pytest.mark.asyncio
async def test_extract_pdf_vision_fallback():
    # Mock fitz to return a page with < 50 chars
    mock_pdf = MagicMock()
    mock_pdf.__len__.return_value = 1
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Short text under fifty chars"
    
    mock_pixmap = MagicMock()
    mock_pixmap.tobytes.return_value = b"fake_png"
    mock_page.get_pixmap.return_value = mock_pixmap
    
    mock_pdf.__iter__.return_value = [mock_page]

    with patch('backend.shared.extraction.fitz.open', return_value=mock_pdf):
        with patch('backend.shared.extraction._call_ollama_vision', return_value="Vision Extracted Text") as mock_vision:
            result = await extract_pdf(b"fakebytes", "test.pdf", "http://fake")
            
            assert result.page_count == 1
            assert len(result.pages) == 1
            assert result.pages[0].used_vision is True
            assert result.pages[0].text == "Vision Extracted Text"
            mock_vision.assert_called_once()
