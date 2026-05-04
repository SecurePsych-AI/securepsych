"""
api.py — SecurePsych RAG

FastAPI backend for the RAG microservice.

Endpoints:
    POST   /upload                          — ingest a PDF into ChromaDB
    GET    /documents                       — list all ingested documents
    DELETE /documents/{document_id}         — remove a document and all its chunks
    GET    /documents/{document_id}/content — retrieve full document text (used by API gateway)
    POST   /query                           — RAG Q&A endpoint
"""

import os
import sys

# ── Security: enforce LangSmith data-scrubbing before any LangChain import ────
os.environ["LANGCHAIN_HIDE_INPUTS"] = "true"
os.environ["LANGCHAIN_HIDE_OUTPUTS"] = "true"
# ─────────────────────────────────────────────────────────────────────────────

from typing import Literal

from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from pydantic import BaseModel, field_validator

load_dotenv(Path(__file__).parent / ".env")

# ── FERPA: CHROMA_PATH must resolve to the LUKS-encrypted mount in production ─
_chroma_path = os.environ.get("CHROMA_PATH", "")
if os.environ.get("SECUREPSYCH_ENV") != "test" and not _chroma_path.startswith("/mnt/securepsych/"):
    sys.exit(
        "FERPA VIOLATION: CHROMA_PATH must be set to the LUKS-encrypted mount "
        f"(e.g. /mnt/securepsych/data/chroma). Current value: '{_chroma_path}'. "
        "Set SECUREPSYCH_ENV=test to bypass in development."
    )
# ─────────────────────────────────────────────────────────────────────────────

from rag_query import answer_question
from ingestion import ingest_pdf_bytes, ingest_from_preview, preview_pdf_bytes
from chroma_client import _ensure_collection

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="RAG API", version="2.0")

_MAX_PDF_BYTES = 50 * 1024 * 1024  # 50 MB — guard against memory-exhaustion DoS
_ALLOWED_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    question:    str
    student_id:  str
    document_id: str | None = None
    mode:        Literal["fast", "deep"] = "fast"
    top_k:       int = 3

    @field_validator("student_id")
    @classmethod
    def student_id_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("student_id is required and must not be empty")
        return v


# ---------------------------------------------------------------------------
# POST /upload
# Upload and ingest a PDF file into ChromaDB.
#
# Usage:
#   curl -X POST http://localhost:8001/upload \
#        -F "file=@sample_psycheval.pdf"
# ---------------------------------------------------------------------------

@app.post("/upload/preview")
async def preview_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF files are supported.")

    file_bytes = await file.read(_MAX_PDF_BYTES + 1)
    if len(file_bytes) > _MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF exceeds maximum allowed size.")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # preview_pdf_bytes is sync but internally calls asyncio.run() to invoke
    # the async PDF extractor. Running it directly inside this async handler
    # would crash with "asyncio.run() cannot be called from a running event
    # loop". Off-loading to a thread gives the inner call its own event loop.
    import asyncio
    result = await asyncio.to_thread(preview_pdf_bytes, file_bytes, file.filename)

    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])

    return result


from fastapi import Request

@app.post("/upload")
async def upload_document(request: Request):
    """Accept either `file` (multipart upload) OR `preview_token` (commit a
    pre-staged preview). Manual form parsing because FastAPI's `File(None)`
    still rejects requests that omit the file field on this version."""
    form = await request.form()
    student_id = form.get("student_id")
    strategy = form.get("strategy") or "standard"
    preview_token = form.get("preview_token")
    file = form.get("file")

    if not student_id:
        raise HTTPException(status_code=422, detail="student_id is required")
    if not file and not preview_token:
        raise HTTPException(
            status_code=422,
            detail="Either 'file' or 'preview_token' must be provided.",
        )
    if file:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        if file.content_type not in _ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=415, detail="Only PDF files are supported.")

    import asyncio
    if preview_token:
        # Same asyncio.run() concern as the preview handler — run in a thread.
        result = await asyncio.to_thread(
            ingest_from_preview, preview_token, student_id, strategy
        )
    else:
        file_bytes = await file.read(_MAX_PDF_BYTES + 1)
        if len(file_bytes) > _MAX_PDF_BYTES:
            raise HTTPException(status_code=413, detail="PDF exceeds maximum allowed size.")
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        result = await asyncio.to_thread(
            ingest_pdf_bytes, file_bytes, file.filename, student_id, strategy
        )

    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])

    return result


# ---------------------------------------------------------------------------
# GET /documents
# List all documents currently stored in ChromaDB.
#
# Usage:
#   curl http://localhost:8001/documents
# ---------------------------------------------------------------------------

@app.get("/documents")
def list_documents(student_id: str):
    collection = _ensure_collection()
    results = collection.get(
        include=["metadatas"],
        where={"student_id": student_id},
    )
    metadatas = results.get("metadatas", [])

    # Deduplicate by document_id — one entry per document, not per chunk
    seen = {}
    for meta in metadatas:
        doc_id = meta.get("document_id")
        if doc_id and doc_id not in seen:
            seen[doc_id] = {
                "document_id": doc_id,
                "filename":    meta.get("source", "Unknown"),
            }

    documents = list(seen.values())

    return {
        "total_documents": len(documents),
        "documents":       documents,
    }


# ---------------------------------------------------------------------------
# DELETE /documents/{document_id}
# Remove all chunks belonging to a document from ChromaDB.
#
# Usage:
#   curl -X DELETE http://localhost:8001/documents/32f4419f-93d6-4a3f-a460-6c3e161318a6
# ---------------------------------------------------------------------------

@app.delete("/documents/{document_id}")
def delete_document(document_id: str):
    collection = _ensure_collection()

    results = collection.get(
        where={"document_id": document_id},
        include=["metadatas"],
    )

    ids_to_delete = results.get("ids", [])

    if not ids_to_delete:
        raise HTTPException(
            status_code=404,
            detail=f"No document found with ID: {document_id}"
        )

    filename = results["metadatas"][0].get("source", "Unknown") if results.get("metadatas") else "Unknown"
    chunks_removed = len(ids_to_delete)

    collection.delete(ids=ids_to_delete)

    return {
        "deleted":        True,
        "document_id":    document_id,
        "filename":       filename,
        "chunks_removed": chunks_removed,
    }


# ---------------------------------------------------------------------------
# GET /documents/{document_id}/content
# Retrieve the full reconstructed text of a document from ChromaDB.
# Used by the API gateway when orchestrating summarization of a previously-ingested
# document — the gateway fetches content here and forwards it to the Summarizer.
# NOTE: Chunks contain some repeated content at chunk boundaries (20% overlap).
# The gateway consumer forwards bytes as-is; downstream re-chunking handles the overlap.
#
# Usage:
#   curl http://localhost:8001/documents/32f4419f-93d6-4a3f-a460-6c3e161318a6/content
# ---------------------------------------------------------------------------

@app.get("/documents/{document_id}/content")
def get_document_content(document_id: str):
    collection = _ensure_collection()

    results = collection.get(
        where={"document_id": document_id},
        include=["documents", "metadatas"],
    )

    if not results.get("ids"):
        raise HTTPException(
            status_code=404,
            detail=f"No document found with ID: {document_id}"
        )

    # Sort by (page, chunk_idx) to reconstruct in original document order
    chunks = sorted(
        zip(results["documents"], results["metadatas"]),
        key=lambda x: (x[1].get("page", 0), x[1].get("chunk_idx", 0)),
    )

    filename = chunks[0][1].get("source", "Unknown")
    page_count = max(meta.get("page", 0) for _, meta in chunks)
    full_text = "\n\n".join(doc for doc, _ in chunks)

    return {
        "document_id": document_id,
        "filename":    filename,
        "text":        full_text,
        "page_count":  page_count,
    }


# ---------------------------------------------------------------------------
# POST /query
# Ask a question against an ingested document (or all documents).
#
# Usage:
#   curl -X POST http://localhost:8001/query \
#        -H "Content-Type: application/json" \
#        -d '{"question": "What medications were prescribed?", "document_id": "...", "mode": "fast"}'
# ---------------------------------------------------------------------------

@app.post("/query")
def query_document(request: QueryRequest):
    result = answer_question(
        question=request.question,
        mode=request.mode,
        top_k=request.top_k,
        document_id=request.document_id,
        student_id=request.student_id,
    )
    return result