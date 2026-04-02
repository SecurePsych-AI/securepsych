"""
ingestion.py — SecurePsych RAG

Ingests a PDF into ChromaDB.

Every chunk gets metadata:
    parent_id  = "{pagenumber}_{chunk_number}"   e.g. "3_2"
    page       = page number (int, 1-indexed)
    source     = original PDF filename
    chunk_idx  = chunk index within the page (0-indexed)
    char_start = character offset inside the page text where chunk starts

parent_id uniquely identifies an individual chunk AND lets deep_retrieve_chunks()
fetch every sibling chunk on the same page by matching the page portion of the id.
"""

from __future__ import annotations

import io
import os
from typing import Optional
import uuid
import fitz  # PyMuPDF
import chromadb
from chromadb.config import Settings

# ---------------------------------------------------------------------------
# Configuration (override via env vars)
# ---------------------------------------------------------------------------
CHROMA_PATH: str = os.getenv("CHROMA_PATH", "./chroma")
COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION", "securepsych_docs")

CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "600"))       # characters
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100")) # characters


# ---------------------------------------------------------------------------
# ChromaDB client (lazy singleton)
# ---------------------------------------------------------------------------
# NOTE: In ChromaDB >=1.x, chromadb.Client is a factory function, not a class.
# We use Optional[Any] here to stay compatible across all versions and Python
# runtimes that don't support X | None on non-class objects.
_client: Optional[object] = None
_collection: Optional[object] = None


def _get_collection():
    """Return (and lazily create) the ChromaDB collection."""
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
# Chunking helper
# ---------------------------------------------------------------------------
def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Split *text* into overlapping character-level chunks.

    Returns a list of dicts:
        {"text": str, "char_start": int, "chunk_idx": int}
    """
    chunks = []
    start = 0
    chunk_idx = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end].strip()

        if chunk_text:  # skip whitespace-only slices
            chunks.append({
                "text": chunk_text,
                "char_start": start,
                "chunk_idx": chunk_idx,
            })
            chunk_idx += 1

        if end == len(text):
            break
        start = end - overlap  # slide window back by overlap

    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def ingest_pdf(pdf_path: str) -> dict:
    """
    Ingest a PDF file into ChromaDB.

    Parameters
    ----------
    pdf_path : str
        Absolute or relative path to the PDF file.

    Returns
    -------
    dict
        {"status": "ok", "pages": int, "chunks_added": int, "source": str}
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    source_name = os.path.basename(pdf_path)
    collection = _get_collection()

    doc = fitz.open(pdf_path)
    total_chunks = 0

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for page_index, page in enumerate(doc):
        pagenumber = page_index + 1  # 1-indexed, human-friendly
        page_text = page.get_text("text")

        if not page_text.strip():
            continue  # skip blank/image-only pages

        chunks = _chunk_text(page_text)

        for chunk in chunks:
            chunk_number = chunk["chunk_idx"]

            # ----------------------------------------------------------------
            # parent_id schema: "{pagenumber}_{chunk_number}"
            # Example: page 3, 2nd chunk  →  "3_2"
            # ----------------------------------------------------------------
            parent_id = f"{pagenumber}_{chunk_number}"

            # Stable, reproducible doc ID so re-ingesting is idempotent
            doc_id = f"{source_name}::{parent_id}"

            ids.append(doc_id)
            documents.append(chunk["text"])
            metadatas.append({
                "parent_id":  parent_id,
                "page":       pagenumber,
                "chunk_idx":  chunk_number,
                "char_start": chunk["char_start"],
                "source":     source_name,
            })
            total_chunks += 1

    num_pages = len(doc)  # must capture BEFORE doc.close()
    doc.close()

    if not ids:
        return {"status": "empty", "pages": 0, "chunks_added": 0, "source": source_name}

    # Upsert in batches of 100 to stay memory-friendly on large PDFs
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i : i + batch_size],
            documents=documents[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )

    return {
        "status": "ok",
        "pages": num_pages,
        "chunks_added": total_chunks,
        "source": source_name,
    }


def ingest_pdf_bytes(file_bytes: bytes, filename: str) -> dict:
    """
    Ingest a PDF from raw bytes (used by the FastAPI upload endpoint).

    Parameters
    ----------
    file_bytes : Raw bytes of the PDF file.
    filename   : Original filename, used as the ``source`` metadata field.

    Returns
    -------
    dict  Same shape as ingest_pdf():
        {"status": str, "pages": int, "chunks_added": int, "source": str}
    """
    if not file_bytes:
        return {"error": "Empty file bytes received.", "source": filename}

    collection = _get_collection()
    source_name = filename
    total_chunks = 0

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    try:
        doc = fitz.open(stream=io.BytesIO(file_bytes), filetype="pdf")
    except Exception as exc:
        return {"error": f"Failed to open PDF: {exc}", "source": source_name}

    for page_index, page in enumerate(doc):
        pagenumber = page_index + 1
        page_text = page.get_text("text")

        if not page_text.strip():
            continue

        chunks = _chunk_text(page_text)

        for chunk in chunks:
            chunk_number = chunk["chunk_idx"]
            parent_id = f"{pagenumber}_{chunk_number}"
            doc_id = f"{source_name}::{parent_id}"

            ids.append(doc_id)
            documents.append(chunk["text"])
            metadatas.append({
                "parent_id":  parent_id,
                "page":       pagenumber,
                "chunk_idx":  chunk_number,
                "char_start": chunk["char_start"],
                "source":     source_name,
            })
            total_chunks += 1

    num_pages = len(doc)
    doc.close()

    if not ids:
        return {"status": "empty", "pages": 0, "chunks_added": 0, "source": source_name}

    batch_size = 100
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i : i + batch_size],
            documents=documents[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )

    return {
        "status": "ok",
        "pages": num_pages,
        "chunks_added": total_chunks,
        "source": source_name,
    }


def list_sources() -> list[str]:
    """Return unique source filenames that have been ingested."""
    collection = _get_collection()
    results = collection.get(include=["metadatas"])
    sources = {m["source"] for m in results["metadatas"] if m}
    return sorted(sources)


def delete_source(source_name: str) -> int:
    """Remove all chunks belonging to *source_name*. Returns number of deleted chunks."""
    collection = _get_collection()
    results = collection.get(include=["metadatas"], where={"source": source_name})
    ids_to_delete = results["ids"]
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
    return len(ids_to_delete)


# ---------------------------------------------------------------------------
# CLI convenience
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ingestion.py <path/to/file.pdf>")
        sys.exit(1)

    result = ingest_pdf(sys.argv[1])
    print(result)