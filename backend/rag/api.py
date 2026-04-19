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
from typing import Literal

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

load_dotenv()

from rag_query import answer_question
from ingestion import ingest_pdf_bytes

# ---------------------------------------------------------------------------
# Configuration (override via env vars)
# ---------------------------------------------------------------------------
CHROMA_PATH: str = os.getenv("CHROMA_PATH", "./chroma")
COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION", "securepsych_docs")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="RAG API", version="2.0")

# ---------------------------------------------------------------------------
# ChromaDB client (lazy singleton — mirrors ingestion.py and rag_query.py)
# ---------------------------------------------------------------------------
_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    question: str
    document_id: str | None = None
    mode: Literal["fast", "deep"] = "fast"
    top_k: int = 3


# ---------------------------------------------------------------------------
# POST /upload
# Upload and ingest a PDF file into ChromaDB.
#
# Usage:
#   curl -X POST http://localhost:8000/upload \
#        -F "file=@sample_psycheval.pdf"
# ---------------------------------------------------------------------------

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    result = ingest_pdf_bytes(file_bytes, file.filename)

    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])

    return result


# ---------------------------------------------------------------------------
# GET /documents
# List all documents currently stored in ChromaDB.
#
# Usage:
#   curl http://localhost:8000/documents
# ---------------------------------------------------------------------------

@app.get("/documents")
def list_documents():
    collection = _get_collection()
    results = collection.get(include=["metadatas"])
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
#   curl -X DELETE http://localhost:8000/documents/32f4419f-93d6-4a3f-a460-6c3e161318a6
# ---------------------------------------------------------------------------

@app.delete("/documents/{document_id}")
def delete_document(document_id: str):
    collection = _get_collection()

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
#   curl http://localhost:8000/documents/32f4419f-93d6-4a3f-a460-6c3e161318a6/content
# ---------------------------------------------------------------------------

@app.get("/documents/{document_id}/content")
def get_document_content(document_id: str):
    collection = _get_collection()

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
#   curl -X POST http://localhost:8000/query \
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
    )
    return result