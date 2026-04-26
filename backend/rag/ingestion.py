"""
ingestion.py — SecurePsych RAG

Two chunking strategies:

  build_token_chunks()      – sliding-window strategy (standard / fast mode)
  build_page_chunks()       – page-boundary strategy for deep mode

Parent-ID schema (agreed field name: "parent_id")
--------------------------------------------------
For ALL chunks (both strategies), ChromaDB metadata includes:

    parent_id: "{page_number}_{chunk_number}"

  build_token_chunks → parent_id = "{page_start}_{chunk_index}"
  build_page_chunks  → parent_id = "{origin_page}_{sub_chunk_number}"

Mohammed: the field is always "parent_id", value always "{N}_{C}" — matching rag_query.py schema.

Benchmark harness
-----------------
Run at the bottom of this file (or via CLI):

    python ingestion.py --benchmark sample_psycheval.pdf
"""

from __future__ import annotations

import io
import os
import re
import sys
import uuid
import argparse
import textwrap
import asyncio
from typing import Optional

import chromadb
from backend.shared.extraction import extract_pdf
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration (override via env vars)
# ---------------------------------------------------------------------------
CHROMA_PATH: str     = os.getenv("CHROMA_PATH",      "./chroma")
COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION", "securepsych_docs")

CHUNK_SIZE: int    = int(os.getenv("CHUNK_SIZE",    "600"))
CHUNK_OVERLAP: float = float(os.getenv("CHUNK_OVERLAP", "0.20"))  # 20% overlap (sliding-window only)


# ---------------------------------------------------------------------------
# ChromaDB client — lazy singleton (mirrors rag_query.py and api.py)
# ---------------------------------------------------------------------------
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
# Helpers
# ---------------------------------------------------------------------------

def approximate_tokens(text: str) -> int:
    """Rough token count: ~4 characters per token."""
    return len(text) // 4


# A line must appear on at least this fraction of pages to be treated as boilerplate.
BOILERPLATE_THRESHOLD = 0.4

# Lines shorter than this (in characters) are never flagged as boilerplate —
# avoids stripping things like "1" or "N/A" that happen to repeat.
BOILERPLATE_MIN_LENGTH = 15


def detect_boilerplate(raw_pages: list[str]) -> set[str]:
    """
    Automatically detect boilerplate by finding lines that repeat across pages.

    Strategy:
    - Split each page into lines and normalise whitespace.
    - Count how many pages each unique line appears on.
    - Any line present on >= BOILERPLATE_THRESHOLD of all pages is boilerplate.
    - Lines shorter than BOILERPLATE_MIN_LENGTH are excluded to avoid
      over-stripping short repeated values (page numbers, field labels, etc.).
    """
    total_pages = len(raw_pages)
    if total_pages == 0:
        return set()

    line_page_count: dict[str, int] = {}

    for page_text in raw_pages:
        seen_on_page: set[str] = set()
        for line in page_text.splitlines():
            normalised = line.strip()
            if len(normalised) >= BOILERPLATE_MIN_LENGTH and normalised not in seen_on_page:
                seen_on_page.add(normalised)
                line_page_count[normalised] = line_page_count.get(normalised, 0) + 1

    threshold_count = max(2, int(total_pages * BOILERPLATE_THRESHOLD))
    return {line for line, count in line_page_count.items() if count >= threshold_count}


def strip_boilerplate(text: str, boilerplate: set[str]) -> str:
    """Remove detected boilerplate lines from a page's extracted text."""
    lines = [line for line in text.splitlines() if line.strip() not in boilerplate]
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

def extract_pages(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Extract text from each PDF page with automatic boilerplate removal.
    Uses shared extract_pdf which falls back to Ollama vision.
    """
    extraction_result = asyncio.run(extract_pdf(file_bytes, filename, OLLAMA_URL))

    # Pass 1: collect raw text
    raw = [page.text for page in extraction_result.pages]

    # Pass 2: detect and strip boilerplate
    boilerplate = detect_boilerplate(raw)
    if boilerplate:
        print(f"  Auto-detected {len(boilerplate)} boilerplate line(s) — stripping before chunking.")

    pages = []
    for page_obj in extraction_result.pages:
        cleaned = strip_boilerplate(page_obj.text, boilerplate)
        if cleaned:
            pages.append({"page": page_obj.page_num, "text": cleaned})

    return pages


# ---------------------------------------------------------------------------
# Strategy 1 — sliding token window (standard mode)
# ---------------------------------------------------------------------------

def build_token_chunks(
    pages: list[dict],
    chunk_size: int = CHUNK_SIZE,
    overlap: float = CHUNK_OVERLAP,
) -> list[dict]:
    """
    Split the full document text into overlapping token-sized chunks.

    Each chunk gets a parent_id of "{page_start}_{chunk_index}" so that
    rag_query.py's deep_retrieve_chunks() can extract the page number via
    _page_from_parent_id() without special-casing this strategy.
    """
    word_list:  list[str] = []
    word_pages: list[int] = []

    for page in pages:
        words = page["text"].split()
        word_list.extend(words)
        word_pages.extend([page["page"]] * len(words))

    if not word_list:
        return []

    words_per_chunk = max(1, int(chunk_size * 0.75))
    step            = max(1, int(words_per_chunk * (1 - overlap)))

    chunks:      list[dict] = []
    chunk_index: int        = 0
    start:       int        = 0

    while start < len(word_list):
        end         = min(start + words_per_chunk, len(word_list))
        chunk_words = word_list[start:end]
        chunk_text  = " ".join(chunk_words)

        pages_covered = word_pages[start:end]
        page_start    = pages_covered[0]
        page_end      = pages_covered[-1]

        chunks.append({
            "chunk_index":    chunk_index,
            "text":           chunk_text,
            "page_start":     page_start,
            "page_end":       page_end,
            # FIX: parent_id added here so rag_query.py can always rely on it
            "parent_id":      f"{page_start}_{chunk_index}",
            "token_estimate": approximate_tokens(chunk_text),
        })

        chunk_index += 1
        start       += step

        remaining = len(word_list) - start
        if 0 < remaining < int(words_per_chunk * 0.10):
            last             = chunks[-1]
            extra_words      = word_list[start:]
            last["text"]    += " " + " ".join(extra_words)
            last["page_end"] = word_pages[-1]
            last["token_estimate"] = approximate_tokens(last["text"])
            break

    return chunks


# ---------------------------------------------------------------------------
# Strategy 2 — page-boundary chunking (deep mode)
# ---------------------------------------------------------------------------

def build_page_chunks(
    pages: list[dict],
    chunk_size: int = CHUNK_SIZE,
) -> list[dict]:
    """
    Deep-mode chunking: page-boundary aware, with overflow carry-forward.

    Rules
    -----
    1.  Process pages one at a time.  Each page's words are prepended with any
        overflow words carried forward from the previous page.
    2.  Slice the combined word list into full chunks of `chunk_size` tokens.
        Each full chunk is labeled with the ORIGIN page (the page whose words
        started the overflow), not the current page.
    3.  Whatever remains after the last full chunk on a page becomes the
        overflow buffer, carrying its origin page label into the next page.
    4.  After all pages are processed, any remaining overflow is emitted as a
        final partial chunk under its origin page label.

    parent_id format: "{origin_page}_{sub_chunk_number}"
    Examples across a 3-page doc:
        1_1            ← first full chunk from page 1
        1_2            ← overflow from page 1 + start of page 2, labeled page 1
        2_1            ← remainder of page 2 after overflow chunk, fresh start
        3_1            ← page 3 fits in one chunk
    """
    chunks:          list[dict] = []
    chunk_index:     int        = 0
    words_per_chunk: int        = max(1, int(chunk_size * 0.75))

    overflow_words:   list[str] = []
    overflow_origin:  int       = 0
    overflow_sub_num: int       = 1

    for page in pages:
        page_num   = page["page"]
        page_words = page["text"].split()

        if overflow_words:
            origin_page = overflow_origin
            sub_num     = overflow_sub_num
        else:
            origin_page = page_num
            sub_num     = 1

        combined = overflow_words + page_words

        start = 0
        while start + words_per_chunk <= len(combined):
            end        = start + words_per_chunk
            chunk_text = " ".join(combined[start:end])
            parent_id  = f"{origin_page}_{sub_num}"

            chunks.append({
                "chunk_index":    chunk_index,
                "text":           chunk_text,
                "page_start":     origin_page,
                "page_end":       page_num,
                "parent_id":      parent_id,
                "token_estimate": approximate_tokens(chunk_text),
            })
            chunk_index += 1
            sub_num     += 1
            start        = end

        overflow_words   = combined[start:]
        overflow_origin  = origin_page
        overflow_sub_num = sub_num

        if not overflow_words:
            overflow_origin  = 0
            overflow_sub_num = 1

    # Emit any remaining overflow as a final partial chunk
    if overflow_words:
        chunk_text = " ".join(overflow_words)
        parent_id  = f"{overflow_origin}_{overflow_sub_num}"
        chunks.append({
            "chunk_index":    chunk_index,
            "text":           chunk_text,
            "page_start":     overflow_origin,
            "page_end":       pages[-1]["page"],
            "parent_id":      parent_id,
            "token_estimate": approximate_tokens(chunk_text),
        })

    return chunks


# ---------------------------------------------------------------------------
# Ingest helpers
# ---------------------------------------------------------------------------

def _store_chunks(
    chunks:      list[dict],
    filename:    str,
    document_id: str,
    strategy:    str,
) -> dict:
    """Write chunks to ChromaDB and return a summary dict."""
    collection = _get_collection()

    ids:       list[str]  = []
    documents: list[str]  = []
    metadatas: list[dict] = []

    for chunk in chunks:
        # ID format matches the rest of the codebase: "{source}::{parent_id}"
        ids.append(f"{filename}::{chunk['parent_id']}")
        documents.append(chunk["text"])
        metadatas.append({
            "document_id":    document_id,
            "parent_id":      chunk["parent_id"],
            "source":         filename,
            "chunk_idx":      chunk["chunk_index"],
            "page":           chunk["page_start"],
            "page_end":       chunk["page_end"],
            "token_estimate": chunk["token_estimate"],
            "strategy":       strategy,
        })

    # FIX: upsert (not add) so re-ingesting the same PDF is safe / idempotent
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i : i + batch_size],
            documents=documents[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )

    avg_tokens = sum(c["token_estimate"] for c in chunks) // len(chunks)
    return {
        "status":           "ok",
        "document_id":      document_id,
        "source":           filename,
        "strategy":         strategy,
        "chunks_added":     len(chunks),
        "avg_chunk_tokens": avg_tokens,
    }


def ingest_pdf_bytes(
    file_bytes: bytes,
    filename:   str,
    strategy:   str = "standard",
    chunk_size: int = CHUNK_SIZE,
) -> dict:
    """
    Ingest a PDF from raw bytes (used by the FastAPI upload endpoint).

    Parameters
    ----------
    file_bytes : Raw bytes of the PDF file.
    filename   : Original filename, used as the ``source`` metadata field.
    strategy   : "standard" → sliding token window | "deep" → page-boundary chunks
    chunk_size : Target tokens per chunk.

    Returns
    -------
    dict  {"status", "document_id", "source", "strategy", "chunks_added", "avg_chunk_tokens"}
    """
    if not file_bytes:
        return {"error": "Empty file bytes received.", "source": filename}

    pages = extract_pages(file_bytes, filename)
    if not pages:
        return {"error": f"No extractable text found in {filename}", "source": filename}

    if strategy == "deep":
        chunks = build_page_chunks(pages, chunk_size=chunk_size)
    else:
        chunks = build_token_chunks(pages, chunk_size=chunk_size)

    if not chunks:
        return {"error": f"Could not produce any chunks from {filename}", "source": filename}

    document_id = str(uuid.uuid4())
    return _store_chunks(chunks, filename, document_id, strategy)


def ingest_pdf(
    filepath:   str,
    strategy:   str = "standard",
    chunk_size: int = CHUNK_SIZE,
) -> dict:
    """
    Ingest a PDF from a file path.

    Parameters
    ----------
    filepath  : Absolute or relative path to the PDF file.
    strategy  : "standard" → sliding token window | "deep" → page-boundary chunks
    chunk_size: Target tokens per chunk.

    Returns
    -------
    dict  Same shape as ingest_pdf_bytes().
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"PDF not found: {filepath}")

    with open(filepath, "rb") as f:
        file_bytes = f.read()

    filename = os.path.basename(filepath)
    pages    = extract_pages(file_bytes, filename)

    if not pages:
        return {"error": f"No extractable text found in {filename}", "source": filename}

    if strategy == "deep":
        chunks = build_page_chunks(pages, chunk_size=chunk_size)
    else:
        chunks = build_token_chunks(pages, chunk_size=chunk_size)

    if not chunks:
        return {"error": f"Could not produce any chunks from {filename}", "source": filename}

    document_id = str(uuid.uuid4())
    summary     = _store_chunks(chunks, filename, document_id, strategy)

    print(f"\nIngestion successful!")
    print(f"  File:            {summary['source']}")
    print(f"  Strategy:        {summary['strategy']}")
    print(f"  Document ID:     {summary['document_id']}")
    print(f"  Chunks stored:   {summary['chunks_added']}")
    print(f"  Avg chunk size:  ~{summary['avg_chunk_tokens']} tokens")

    return summary


# ---------------------------------------------------------------------------
# Utility functions (used by api.py and test_top_k.py)
# ---------------------------------------------------------------------------

def list_sources() -> list[str]:
    """Return unique source filenames that have been ingested."""
    collection = _get_collection()
    results    = collection.get(include=["metadatas"])
    sources    = {m["source"] for m in results["metadatas"] if m}
    return sorted(sources)


def delete_source(source_name: str) -> int:
    """Remove all chunks belonging to *source_name*. Returns number of deleted chunks."""
    collection     = _get_collection()
    results        = collection.get(include=["metadatas"], where={"source": source_name})
    ids_to_delete  = results["ids"]
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
    return len(ids_to_delete)


# ---------------------------------------------------------------------------
# Benchmark harness
# ---------------------------------------------------------------------------

BENCHMARK_QUESTIONS = [
    "What assessment tools or psychological tests were used?",
    "What are the main diagnostic conclusions or clinical impressions?",
    "What recommendations were made for treatment or intervention?",
    "What cognitive or intellectual functioning scores are reported?",
]

CHUNK_SIZES_TO_TEST = [512, 600, 768, 800]


def run_benchmark(filepath: str, n_results: int = 3) -> None:
    """
    Ingest `filepath` four times (once per chunk size) and query each
    ingestion with BENCHMARK_QUESTIONS.  Prints a formatted comparison table.

    Uses an ephemeral ChromaDB client so benchmark runs don't pollute
    the production chroma store.
    """
    print("\n" + "=" * 72)
    print("CHUNK SIZE BENCHMARK")
    print(f"File: {filepath}")
    print("=" * 72)

    bench_client     = chromadb.EphemeralClient()
    bench_collection = bench_client.get_or_create_collection(name="securepsych_docs_benchmark")

    with open(filepath, "rb") as f:
        file_bytes = f.read()

    filename = os.path.basename(filepath)
    pages    = extract_pages(file_bytes, filename)

    if not pages:
        print("ERROR: No extractable text found — aborting benchmark.")
        return

    run_ids: dict[int, str] = {}

    for cs in CHUNK_SIZES_TO_TEST:
        chunks      = build_token_chunks(pages, chunk_size=cs)
        document_id = str(uuid.uuid4())
        run_ids[cs] = document_id

        bench_collection.add(
            ids=[f"{document_id}_chunk{c['chunk_index']}" for c in chunks],
            documents=[c["text"] for c in chunks],
            metadatas=[
                {
                    "document_id":    document_id,
                    "chunk_size_cfg": cs,
                    "chunk_index":    c["chunk_index"],
                    "page_start":     c["page_start"],
                    "page_end":       c["page_end"],
                }
                for c in chunks
            ],
        )
        print(f"\n  Ingested with chunk_size={cs}: {len(chunks)} chunks stored")

    scores: dict[int, list[float]] = {cs: [] for cs in CHUNK_SIZES_TO_TEST}

    for q_idx, question in enumerate(BENCHMARK_QUESTIONS, start=1):
        print(f"\n{'─' * 72}")
        print(f"Q{q_idx}: {question}")
        print(f"{'─' * 72}")

        for cs in CHUNK_SIZES_TO_TEST:
            results = bench_collection.query(
                query_texts=[question],
                n_results=n_results,
                where={"document_id": run_ids[cs]},
            )
            docs    = results["documents"][0]
            avg_len = sum(len(d) for d in docs) / max(len(docs), 1)
            scores[cs].append(avg_len)

            print(f"\n  chunk_size={cs}  |  {len(docs)} results  |  avg chunk len={avg_len:.0f} chars")
            for i, doc in enumerate(docs, start=1):
                snippet = textwrap.shorten(doc, width=160, placeholder=" …")
                print(f"    [{i}] {snippet}")

    print(f"\n{'=' * 72}")
    print("SUMMARY — average chunk length across all questions (higher = more context per result)")
    print(f"{'─' * 40}")
    ranked = sorted(scores.items(), key=lambda kv: sum(kv[1]) / len(kv[1]), reverse=True)
    for rank, (cs, vals) in enumerate(ranked, start=1):
        avg = sum(vals) / len(vals)
        bar = "█" * int(avg / 60)
        print(f"  #{rank}  chunk_size={cs:>4}   avg={avg:>7.0f} chars   {bar}")
    print(f"\n  Recommended chunk_size: {ranked[0][0]}  ← highest average context")
    print("  (Verify by reading the snippets above — the heuristic is a starting point)")
    print("=" * 72 + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF ingestion + benchmark tool")
    parser.add_argument("filepath", nargs="?", help="Path to PDF file")
    parser.add_argument(
        "--strategy",
        choices=["standard", "deep"],
        default="standard",
        help="Chunking strategy: 'standard' (sliding window) or 'deep' (page-boundary)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CHUNK_SIZE,
        help=f"Target tokens per chunk (default: {CHUNK_SIZE})",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run chunk-size benchmark instead of a single ingest",
    )
    args = parser.parse_args()

    if not args.filepath:
        prompt_msg = "Enter the path to your PDF for benchmarking: " if args.benchmark else "Enter the path to your PDF: "
        args.filepath = input(prompt_msg).strip()

    if args.benchmark:
        run_benchmark(args.filepath)
    else:
        ingest_pdf(args.filepath, strategy=args.strategy, chunk_size=args.chunk_size)