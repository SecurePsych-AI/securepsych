from services.summarizer import run_summarize_chain
from services.pdf_loader import load_pdf_from_bytes
import os
from typing import Optional

import yaml
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

_MAX_PDF_BYTES = 50 * 1024 * 1024  # 50 MB — guard against memory-exhaustion DoS
_ALLOWED_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}


router = APIRouter()


def _feature_enabled() -> bool:
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(cfg_path) as f:
        return yaml.safe_load(f).get("summarizer", {}).get("enabled", True)


class SummaryResponse(BaseModel):
    summary: str
    page_count: int


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_document(
    file: Optional[UploadFile] = File(None),
):
    """
    Summarize a PDF document.

    Accepts raw PDF bytes only. This service is intentionally stateless.
    If summarizing a document already ingested into RAG, the API gateway
    is responsible for fetching its content and forwarding it here.
    """
    if not _feature_enabled():
        raise HTTPException(status_code=503, detail="Feature unavailable")

    if file is None:
        raise HTTPException(
            status_code=422, detail="A PDF file upload is required."
        )

    if file.filename is None or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=422, detail="Only PDF files are supported.")

    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415, detail="Only PDF files are supported.")

    pdf_bytes = await file.read(_MAX_PDF_BYTES + 1)
    if len(pdf_bytes) > _MAX_PDF_BYTES:
        raise HTTPException(
            status_code=413, detail=f"PDF exceeds maximum allowed size of {_MAX_PDF_BYTES} bytes.")

    docs, page_count = load_pdf_from_bytes(pdf_bytes)

    if not docs:
        raise HTTPException(
            status_code=422,
            detail="No extractable text found in the PDF.",
        )

    summary_text = await run_summarize_chain(docs)

    return SummaryResponse(
        summary=summary_text,
        page_count=page_count,
    )
