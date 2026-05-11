from services.summarizer import run_summarize_chain
from services.pdf_loader import load_pdf_from_bytes
import os
from typing import Optional

import yaml
from fastapi import APIRouter, File, HTTPException, UploadFile
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

_MAX_PDF_BYTES = 50 * 1024 * 1024  # 50 MB — guard against memory-exhaustion DoS
_PDF_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}
_TEXT_CONTENT_TYPES = {"text/plain"}


router = APIRouter()


def _feature_enabled() -> bool:
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(cfg_path) as f:
        return yaml.safe_load(f).get("summarizer", {}).get("enabled", True)


class SummaryResponse(BaseModel):
    summary: str
    page_count: int


def _is_text_input(file: UploadFile) -> bool:
    name = (file.filename or "").lower()
    return file.content_type in _TEXT_CONTENT_TYPES or name.endswith(".txt")


def _is_pdf_input(file: UploadFile) -> bool:
    name = (file.filename or "").lower()
    return file.content_type in _PDF_CONTENT_TYPES or name.endswith(".pdf")


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_document(
    file: Optional[UploadFile] = File(None),
):
    """
    Summarize a document.

    Accepts either:
      - a raw PDF upload (Mode A — direct upload from the frontend), or
      - plain UTF-8 text (Mode B — gateway has already extracted the text from
        a previously ingested RAG document and forwards it as `.txt`).

    Stateless. If summarizing a document already ingested into RAG, the API
    gateway is responsible for fetching its content and forwarding it here.
    """
    if not _feature_enabled():
        raise HTTPException(status_code=503, detail="Feature unavailable")

    if file is None:
        raise HTTPException(
            status_code=422, detail="A file upload is required."
        )

    if _is_pdf_input(file):
        pdf_bytes = await file.read(_MAX_PDF_BYTES + 1)
        if len(pdf_bytes) > _MAX_PDF_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"PDF exceeds maximum allowed size of {_MAX_PDF_BYTES} bytes.",
            )
        docs, page_count = await load_pdf_from_bytes(pdf_bytes)
    elif _is_text_input(file):
        text_bytes = await file.read(_MAX_PDF_BYTES + 1)
        if len(text_bytes) > _MAX_PDF_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Document exceeds maximum allowed size of {_MAX_PDF_BYTES} bytes.",
            )
        text = text_bytes.decode("utf-8", errors="replace")
        # Cap text size for sub-90s synchronous summaries on local dev hardware.
        # The refine pipeline is one LLM call per chunk; on a 24-page eval the
        # full text fits comfortably in this cap. Larger documents are
        # truncated rather than blocked — the structured summary leans on the
        # opening sections (referral, scores, diagnoses) anyway.
        _MAX_TEXT_CHARS = 60_000
        if len(text) > _MAX_TEXT_CHARS:
            text = text[:_MAX_TEXT_CHARS]
        page_doc = Document(page_content=text, metadata={"page": 1, "source": "gateway"})
        splitter = RecursiveCharacterTextSplitter(chunk_size=8000, chunk_overlap=400)
        docs = splitter.split_documents([page_doc])
        page_count = 1
    else:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Provide a PDF or plain-text document.",
        )

    if not docs:
        raise HTTPException(
            status_code=422,
            detail="No extractable text found in the document.",
        )

    summary_text = await run_summarize_chain(docs)

    return SummaryResponse(
        summary=summary_text,
        page_count=page_count,
    )
