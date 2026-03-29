import os
from typing import Optional

import yaml
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from services.pdf_loader import load_pdf_from_bytes
from services.summarizer import run_summarize_chain

router = APIRouter()


def _feature_enabled() -> bool:
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(cfg_path) as f:
        return yaml.safe_load(f).get("summarizer", {}).get("enabled", True)


class SummaryResponse(BaseModel):
    summary: str
    method: str
    page_count: int


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_document(
    file: Optional[UploadFile] = File(None),
    document_id: Optional[str] = Form(None),
):
    """
    Accept a PDF upload (or a document_id from a prior RAG ingestion) and
    return a structured summary covering diagnoses, test scores,
    accommodations, and evaluation dates.

    Stateless — no session state is retained between calls.
    """
    if not _feature_enabled():
        raise HTTPException(status_code=503, detail="Feature unavailable")

    if file is None and document_id is None:
        raise HTTPException(
            status_code=422,
            detail="Provide either a PDF file or a document_id.",
        )

    if document_id is not None:
        # TODO: retrieve document bytes from the RAG ingestion store once that
        # service is live (Arham / Noble / Mohammed — coordinate on the shared
        # document ID contract).
        raise HTTPException(
            status_code=501,
            detail="document_id lookup is not yet implemented. Upload a PDF directly for now.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=422, detail="Only PDF files are supported.")

    pdf_bytes = await file.read()

    docs, page_count = load_pdf_from_bytes(pdf_bytes)

    if not docs:
        raise HTTPException(
            status_code=422,
            detail="No extractable text found in the PDF.",
        )

    summary_text = await run_summarize_chain(docs)

    return SummaryResponse(
        summary=summary_text,
        method="refine",
        page_count=page_count,
    )
