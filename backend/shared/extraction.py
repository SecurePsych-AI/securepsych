import base64
import logging
from typing import List

import fitz  # PyMuPDF
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

MIN_TEXT_CHARS = 50

class ExtractionMeta(BaseModel):
    is_scanned: bool
    word_count: int
    estimated_tokens: int
    extraction_method: str


class PageResult(BaseModel):
    page_num: int
    text: str
    char_count: int
    used_vision: bool


class ExtractionResult(BaseModel):
    filename: str
    page_count: int
    full_text: str
    pages: List[PageResult]
    metadata: ExtractionMeta


async def _call_ollama_vision(base64_image: str, ollama_url: str) -> str:
    """Async POST request to Ollama's vision model."""
    payload = {
        "model": "llava:7b",
        "prompt": (
            "Transcribe all visible text exactly as it appears. "
            "Describe any charts, tables, or score grids in full detail. "
            "Context: This is a psychological assessment report."
        ),
        "images": [base64_image],
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{ollama_url}/api/generate", json=payload)
            response.raise_for_status()
            return response.json().get("response", "").strip()
    except Exception as e:
        logger.warning(f"Ollama vision call failed: {e}")
        return ""


async def extract_pdf(file_bytes: bytes, filename: str, ollama_url: str) -> ExtractionResult:
    """
    Extract text from a PDF. If a page has fewer than MIN_TEXT_CHARS,
    it falls back to an Ollama vision extraction.
    """
    pdf = fitz.open(stream=file_bytes, filetype="pdf")
    page_count = len(pdf)
    
    pages_results: List[PageResult] = []
    total_words = 0
    scanned_pages_count = 0
    
    for page_num_0_idx, page in enumerate(pdf):
        page_num = page_num_0_idx + 1
        text = page.get_text().strip()
        used_vision = False
        
        if len(text) < MIN_TEXT_CHARS:
            used_vision = True
            scanned_pages_count += 1
            try:
                pix = page.get_pixmap(dpi=150)
                png_bytes = pix.tobytes("png")
                b64_img = base64.b64encode(png_bytes).decode("utf-8")
                
                vision_text = await _call_ollama_vision(b64_img, ollama_url)
                if vision_text:
                    text = vision_text
            except Exception as e:
                logger.warning(f"Failed to process page {page_num} with vision: {e}")
                text = ""
                
        char_count = len(text)
        pages_results.append(
            PageResult(
                page_num=page_num,
                text=text,
                char_count=char_count,
                used_vision=used_vision
            )
        )
        total_words += len(text.split())
        
    pdf.close()
    
    full_text = "\n\n".join(p.text for p in pages_results if p.text)
    estimated_tokens = len(full_text) // 4
    is_scanned = scanned_pages_count > 0
    extraction_method = "hybrid (fitz + ollama)" if is_scanned else "fitz"
    
    meta = ExtractionMeta(
        is_scanned=is_scanned,
        word_count=total_words,
        estimated_tokens=estimated_tokens,
        extraction_method=extraction_method
    )
    
    return ExtractionResult(
        filename=filename,
        page_count=page_count,
        full_text=full_text,
        pages=pages_results,
        metadata=meta
    )
