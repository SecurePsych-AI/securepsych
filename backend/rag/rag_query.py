"""
rag_query.py — SecurePsych RAG

Three public functions:

  retrieve_chunks(query, top_k)         — fast vector search
  deep_retrieve_chunks(query, top_k)    — vector search + full-page expansion
  answer_question(question, mode, top_k)— routes to the right retrieval fn,
                                          builds prompt, calls Ollama LLM

parent_id schema (set during ingestion):
    "{pagenumber}_{chunk_number}"   e.g. "3_2"  → page 3, chunk 2

Deep mode uses the page portion of parent_id to fetch ALL chunks from the
same page as each matched chunk, giving the model the full section context
rather than just isolated snippets.
"""

from __future__ import annotations

import os
import re
from typing import Literal

import chromadb
from chromadb.config import Settings
from langchain_ollama import OllamaLLM

# ---------------------------------------------------------------------------
# Configuration (override via env vars)
# ---------------------------------------------------------------------------
CHROMA_PATH: str = os.getenv("CHROMA_PATH", "./chroma")
COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION", "securepsych_docs")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

DEFAULT_TOP_K: int = 3       # validated via test_top_k.py — better than original default of 2
MAX_CONTEXT_CHARS: int = 8000  # guard against oversized prompts

# ---------------------------------------------------------------------------
# Lazy singletons
# ---------------------------------------------------------------------------
_collection = None
_llm: OllamaLLM | None = None


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _get_llm() -> OllamaLLM:
    global _llm
    if _llm is None:
        _llm = OllamaLLM(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
        )
    return _llm


# ---------------------------------------------------------------------------
# Helper — extract page number from parent_id
# ---------------------------------------------------------------------------
def _page_from_parent_id(parent_id: str) -> str:
    """
    Given a parent_id like "3_2", return the page portion "3".
    Robust to unexpected formats — falls back to full string.
    """
    parts = parent_id.split("_", 1)
    return parts[0] if len(parts) == 2 else parent_id


# ---------------------------------------------------------------------------
# retrieve_chunks — FAST MODE
# ---------------------------------------------------------------------------
def retrieve_chunks(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Run a ChromaDB vector similarity search and return the top_k chunks.

    Parameters
    ----------
    query  : The user's question or search string.
    top_k  : Number of chunks to return (2–5 recommended; validate with test_top_k.py).

    Returns
    -------
    List of dicts, each containing:
        text      : chunk text
        parent_id : "{pagenumber}_{chunk_number}"
        page      : page number (int)
        source    : source PDF filename
        distance  : cosine distance (lower = more similar)
    """
    collection = _get_collection()

    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text":      doc,
            "parent_id": meta.get("parent_id", ""),
            "page":      meta.get("page", -1),
            "source":    meta.get("source", ""),
            "distance":  dist,
        })

    return chunks


# ---------------------------------------------------------------------------
# deep_retrieve_chunks — DEEP MODE
# ---------------------------------------------------------------------------
def deep_retrieve_chunks(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Two-step retrieval that expands matched chunks to their full page section.

    Step 1 — Vector search:
        Same as retrieve_chunks() — find the top_k most relevant chunks.

    Step 2 — Page expansion:
        For each matched chunk, extract the page number from its parent_id,
        then fetch ALL chunks whose parent_id starts with "{page}_".
        This returns the entire section around the match rather than just
        the isolated snippet.

    NOTE: Coordinate with Noble on the parent_id field name before changing
    the metadata key below. Currently assumes the ingestion.py schema where
    parent_id = "{pagenumber}_{chunk_number}".

    Returns
    -------
    Deduplicated, sorted list of chunk dicts (same shape as retrieve_chunks).
    Sorted by (page, chunk_idx) so context is in document order.
    """
    # --- Step 1: vector search ---
    seed_chunks = retrieve_chunks(query, top_k=top_k)
    if not seed_chunks:
        return []

    # Collect the unique page numbers that were matched
    matched_pages: set[str] = set()
    for chunk in seed_chunks:
        page_str = _page_from_parent_id(chunk["parent_id"])
        matched_pages.add(page_str)

    collection = _get_collection()
    expanded: dict[str, dict] = {}  # keyed by parent_id to deduplicate

    # --- Step 2: page expansion ---
    for page_str in matched_pages:
        # ChromaDB doesn't support starts_with so we regex-filter on the page
        # portion after fetching all chunks for that page number.
        # We use a $eq filter on the integer "page" metadata field for speed.
        try:
            page_int = int(page_str)
        except ValueError:
            continue

        results = collection.get(
            where={"page": page_int},
            include=["documents", "metadatas"],
        )

        for doc, meta in zip(results["documents"], results["metadatas"]):
            pid = meta.get("parent_id", "")
            if pid not in expanded:
                expanded[pid] = {
                    "text":      doc,
                    "parent_id": pid,
                    "page":      meta.get("page", -1),
                    "chunk_idx": meta.get("chunk_idx", 0),
                    "source":    meta.get("source", ""),
                    "distance":  None,  # expanded chunks have no vector distance
                }

    # Also make sure seed chunks are in the set (they always should be, but safety first)
    for chunk in seed_chunks:
        pid = chunk["parent_id"]
        if pid not in expanded:
            expanded[pid] = chunk

    # Sort by (page, chunk_idx) so context reads in document order
    sorted_chunks = sorted(
        expanded.values(),
        key=lambda c: (c.get("page", 0), c.get("chunk_idx", 0)),
    )

    return sorted_chunks


# ---------------------------------------------------------------------------
# answer_question — main entry point
# ---------------------------------------------------------------------------
def answer_question(
    question: str,
    mode: Literal["fast", "deep"] = "fast",
    top_k: int = DEFAULT_TOP_K,
) -> dict:
    """
    Answer a question using the RAG pipeline.

    Parameters
    ----------
    question : The psychologist's question about a student document.
    mode     : "fast" — standard top_k vector retrieval (default, existing behavior)
               "deep" — vector search + full-page expansion for richer context
    top_k    : Number of seed chunks to retrieve (recommended: 3 or 4 for psych evals).
               Use test_top_k.py to validate the best value for your documents.

    Returns
    -------
    dict with keys:
        answer   : LLM-generated answer string
        mode     : retrieval mode used
        top_k    : top_k value used
        sources  : list of {"source", "page", "parent_id"} for each context chunk
        chunks   : full list of chunk dicts used as context
    """
    # --- Retrieve context ---
    if mode == "deep":
        chunks = deep_retrieve_chunks(question, top_k=top_k)
    else:
        chunks = retrieve_chunks(question, top_k=top_k)

    if not chunks:
        return {
            "answer":  "No relevant content found in the ingested documents.",
            "mode":    mode,
            "top_k":   top_k,
            "sources": [],
            "chunks":  [],
        }

    # --- Build context string (cap at MAX_CONTEXT_CHARS) ---
    context_parts: list[str] = []
    total_chars = 0
    for chunk in chunks:
        snippet = f"[Page {chunk['page']} | {chunk['source']}]\n{chunk['text']}"
        if total_chars + len(snippet) > MAX_CONTEXT_CHARS:
            break
        context_parts.append(snippet)
        total_chars += len(snippet)

    context_text = "\n\n---\n\n".join(context_parts)

    # --- Prompt ---
    prompt = (
        "You are a helpful AI assistant supporting a school psychologist.\n"
        "Answer the question below using ONLY the provided document excerpts.\n"
        "If the answer is not in the excerpts, say you don't know — do not guess.\n"
        "Be concise and professional.\n\n"
        f"Document Excerpts:\n{context_text}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

    # --- Call LLM ---
    llm = _get_llm()
    answer_text = llm.invoke(prompt)

    sources = [
        {"source": c["source"], "page": c["page"], "parent_id": c["parent_id"]}
        for c in chunks
    ]

    return {
        "answer":  answer_text.strip(),
        "mode":    mode,
        "top_k":   top_k,
        "sources": sources,
        "chunks":  chunks,
    }


# ---------------------------------------------------------------------------
# CLI convenience
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys, json

    if len(sys.argv) < 2:
        print("Usage: python rag_query.py '<question>' [fast|deep] [top_k]")
        sys.exit(1)

    q = sys.argv[1]
    m = sys.argv[2] if len(sys.argv) > 2 else "fast"
    k = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_TOP_K

    result = answer_question(q, mode=m, top_k=k)
    print(json.dumps({"answer": result["answer"], "mode": result["mode"], "top_k": result["top_k"]}, indent=2))