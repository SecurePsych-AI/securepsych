"""
ingestion.py
============
Two chunking strategies:

  build_token_chunks()      – original sliding-window strategy (standard mode)
  build_page_chunks()       – page-boundary strategy for deep mode

Parent-ID schema (agreed field name: "parent_id")
--------------------------------------------------
For every chunk produced by build_page_chunks(), ChromaDB metadata includes:

    parent_id: "{page_number}_{chunk_number}"



Mohammed: the field is always "parent_id", value always "{N}_{C}" — matching rag_query.py schema.

Benchmark harness
-----------------
Run at the bottom of this file (or via CLI):

    python ingestion.py --benchmark sample_psycheval.pdf

It ingests the PDF at chunk sizes 512 / 600 / 768 / 800, queries 4 fixed
questions against each, and prints a side-by-side results table so you can
pick the best chunk size with evidence rather than a guess.
"""

import sys
import uuid
import argparse
import textwrap
import fitz
import chromadb


# ---------------------------------------------------------------------------
# ChromaDB client — shared across both strategies
# ---------------------------------------------------------------------------

chroma_client = chromadb.PersistentClient(path="./chroma")
collection = chroma_client.get_or_create_collection(name="securepsych_docs")


# ---------------------------------------------------------------------------
# Config defaults
# ---------------------------------------------------------------------------

CHUNK_SIZE = 600   # target tokens per chunk
OVERLAP    = 0.20  # 20 % overlap (sliding-window strategy only)




# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def approximate_tokens(text: str) -> int:
    """Rough token count: ~4 characters per token."""
    return len(text) // 4


import re

# A line must appear on at least this fraction of pages to be treated as boilerplate.
# 0.4 = present on 40%+ of pages. Lower catches more noise; higher is more conservative.
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
        # Use a set so a line appearing twice on the same page only counts once
        seen_on_page = set()
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


def extract_pages(file_bytes: bytes) -> list[dict]:
    """
    Extract text from each PDF page with automatic boilerplate removal.

    Two-pass process:
    1. Extract raw text from all pages.
    2. Detect boilerplate lines that repeat across pages.
    3. Strip those lines and return clean page texts.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    # Pass 1: collect raw text
    raw = []
    for page in doc:
        raw.append(page.get_text("text").strip())
    doc.close()

    # Pass 2: detect and strip boilerplate
    boilerplate = detect_boilerplate(raw)
    if boilerplate:
        print(f"  Auto-detected {len(boilerplate)} boilerplate line(s) — stripping before chunking.")

    pages = []
    for page_num, text in enumerate(raw, start=1):
        cleaned = strip_boilerplate(text, boilerplate)
        if cleaned:
            pages.append({"page": page_num, "text": cleaned})

    return pages


# ---------------------------------------------------------------------------
# Strategy 1 — sliding token window (standard mode, unchanged)
# ---------------------------------------------------------------------------

def build_token_chunks(
    pages: list[dict],
    chunk_size: int = CHUNK_SIZE,
    overlap: float = OVERLAP,
) -> list[dict]:
    """
    Split the full document text into overlapping token-sized chunks.

    Strategy:
    - Concatenate all page text, tracking which characters belong to which page.
    - Split into words (proxy for tokens at ~0.75 words/token).
    - Slide a window of `chunk_size` tokens forward by `chunk_size * (1 - overlap)` each step.
    - Record the page range covered by each chunk for citation metadata.
    """
    word_list  = []
    word_pages = []

    for page in pages:
        words = page["text"].split()
        word_list.extend(words)
        word_pages.extend([page["page"]] * len(words))

    if not word_list:
        return []

    words_per_chunk = max(1, int(chunk_size * 0.75))
    step            = max(1, int(words_per_chunk * (1 - overlap)))

    chunks      = []
    chunk_index = 0
    start       = 0

    while start < len(word_list):
        end         = min(start + words_per_chunk, len(word_list))
        chunk_words = word_list[start:end]
        chunk_text  = " ".join(chunk_words)

        pages_covered = word_pages[start:end]
        page_start    = pages_covered[0]
        page_end      = pages_covered[-1]

        chunks.append({
            "chunk_index":   chunk_index,
            "text":          chunk_text,
            "page_start":    page_start,
            "page_end":      page_end,
            "token_estimate": approximate_tokens(chunk_text),
        })

        chunk_index += 1
        start       += step

        remaining = len(word_list) - start
        if 0 < remaining < int(words_per_chunk * 0.10):
            last            = chunks[-1]
            extra_words     = word_list[start:]
            last["text"]   += " " + " ".join(extra_words)
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
        e.g. page 3 fills chunk page_3_1, has 200 tokens left →
             those 200 tokens are prepended to page 4's words →
             the resulting full chunk is labeled page_3_2.
    3.  Whatever remains after the last full chunk on a page becomes the
        overflow buffer, carrying its origin page label into the next page.
    4.  After all pages are processed, any remaining overflow is emitted as a
        final partial chunk under its origin page label.

    parent_id format (agreed with Mohammed): "page_{page_number}_{chunk_number}"
    - page_number  : 1-indexed PDF page of the overflow origin (not physical page)
    - chunk_number : 1-indexed, resets to 1 whenever a new page's content starts
                     (i.e. whenever the overflow buffer was empty going into a page)
    Examples across a 3-page doc:
        1_1            ← first full chunk from page 1
        1_2            ← overflow from page 1 + start of page 2, labeled page 1
        2_1            ← remainder of page 2 after overflow chunk, fresh start
        3_1            ← page 3 fits in one chunk
    """
    chunks          = []
    chunk_index     = 0
    words_per_chunk = max(1, int(chunk_size * 0.75))

    # Carry-forward state
    overflow_words    : list[str] = []   # leftover words from previous page
    overflow_origin   : int       = 0    # page number those words came from
    overflow_sub_num  : int       = 1    # next sub-chunk number for that origin page

    for page in pages:
        page_num    = page["page"]
        page_words  = page["text"].split()

        # Decide origin label for chunks produced during this page
        if overflow_words:
            # We're continuing from a previous page's overflow
            origin_page = overflow_origin
            sub_num     = overflow_sub_num
        else:
            # Fresh start — this page owns its own chunks
            origin_page = page_num
            sub_num     = 1

        # Combine overflow + this page's words
        combined = overflow_words + page_words

        # Emit as many full chunks as possible
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

        # Whatever is left becomes the new overflow, still attributed to origin_page
        overflow_words   = combined[start:]
        overflow_origin  = origin_page
        overflow_sub_num = sub_num

        # If we fully consumed the combined buffer (no overflow), next page is fresh
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
    ids       = []
    documents = []
    metadatas = []

    for chunk in chunks:
        ids.append(f"{document_id}_chunk{chunk['chunk_index']}")
        documents.append(chunk["text"])
        meta = {
            "document_id":    document_id,
            "source":         filename,
            "chunk_idx":      chunk["chunk_index"],
            "page":           chunk["page_start"],
            "page_end":       chunk["page_end"],
            "token_estimate": chunk["token_estimate"],
            "strategy":       strategy,
        }
        if "parent_id" in chunk:
            meta["parent_id"] = chunk["parent_id"]
        metadatas.append(meta)

    collection.add(ids=ids, documents=documents, metadatas=metadatas)

    avg_tokens = sum(c["token_estimate"] for c in chunks) // len(chunks)
    return {
        "document_id":    document_id,
        "filename":       filename,
        "strategy":       strategy,
        "chunks_stored":  len(chunks),
        "avg_chunk_tokens": avg_tokens,
    }


def ingest_pdf_bytes(
    file_bytes: bytes,
    filename:   str,
    strategy:   str = "standard",
    chunk_size: int = CHUNK_SIZE,
) -> dict:
    """
    Ingest a PDF from raw bytes.
    strategy: "standard"  → sliding token window (build_token_chunks)
              "deep"      → page-boundary chunks  (build_page_chunks)
    Returns a summary dict for the FastAPI response.
    """
    pages = extract_pages(file_bytes)
    if not pages:
        return {"error": f"No extractable text found in {filename}"}

    if strategy == "deep":
        chunks = build_page_chunks(pages, chunk_size=chunk_size)
    else:
        chunks = build_token_chunks(pages, chunk_size=chunk_size)

    if not chunks:
        return {"error": f"Could not produce any chunks from {filename}"}

    document_id = str(uuid.uuid4())
    return _store_chunks(chunks, filename, document_id, strategy)


def ingest_pdf(
    filepath:   str,
    strategy:   str = "standard",
    chunk_size: int = CHUNK_SIZE,
) -> dict:
    """Ingest a PDF from a file path (CLI / benchmark use)."""
    with open(filepath, "rb") as f:
        file_bytes = f.read()
    filename = filepath.split("/")[-1]
    pages    = extract_pages(file_bytes)

    if not pages:
        print(f"No extractable text found in {filename}")
        return {}

    if strategy == "deep":
        chunks = build_page_chunks(pages, chunk_size=chunk_size)
    else:
        chunks = build_token_chunks(pages, chunk_size=chunk_size)

    if not chunks:
        print(f"Could not produce any chunks from {filename}")
        return {}

    document_id = str(uuid.uuid4())
    summary     = _store_chunks(chunks, filename, document_id, strategy)

    print(f"\nIngestion successful!")
    print(f"  File:            {summary['filename']}")
    print(f"  Strategy:        {summary['strategy']}")
    print(f"  Document ID:     {summary['document_id']}")
    print(f"  Chunks stored:   {summary['chunks_stored']}")
    print(f"  Avg chunk size:  ~{summary['avg_chunk_tokens']} tokens")
    print(f"  Chunk size cfg:  {chunk_size} tokens" +
          (f"  |  Overlap: {int(OVERLAP * 100)}%" if strategy == "standard" else "  |  Overlap: none (deep mode)"))

    return summary


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

    Scoring heuristic
    -----------------
    For each (question, chunk_size) pair we record:
      - how many result chunks were returned
      - the average character length of those chunks (longer → more context)
    These are rough proxies for "completeness" — a human should still read the
    snippets and confirm.  The heuristic is printed alongside the snippets so
    the final decision is yours.
    """
    print("\n" + "=" * 72)
    print("CHUNK SIZE BENCHMARK")
    print(f"File: {filepath}")
    print("=" * 72)

    # We use a throw-away ephemeral client so benchmark runs don't pollute
    # the production chroma_db.
    bench_client     = chromadb.EphemeralClient()
    bench_collection = bench_client.get_or_create_collection(name="securepsych_docs_benchmark")

    with open(filepath, "rb") as f:
        file_bytes = f.read()
    filename = filepath.split("/")[-1]
    pages    = extract_pages(file_bytes)

    if not pages:
        print("ERROR: No extractable text found — aborting benchmark.")
        return

    # Map chunk_size → document_id so we can filter queries per run
    run_ids: dict[int, str] = {}

    for cs in CHUNK_SIZES_TO_TEST:
        chunks      = build_token_chunks(pages, chunk_size=cs)
        document_id = str(uuid.uuid4())
        run_ids[cs] = document_id

        bench_collection.add(
            ids       =[f"{document_id}_chunk{c['chunk_index']}" for c in chunks],
            documents =[c["text"] for c in chunks],
            metadatas =[
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

    # --- Query loop ----------------------------------------------------------
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
            docs = results["documents"][0]  # list of chunk texts

            avg_len = sum(len(d) for d in docs) / max(len(docs), 1)
            scores[cs].append(avg_len)

            print(f"\n  chunk_size={cs}  |  {len(docs)} results  |  avg chunk len={avg_len:.0f} chars")
            for i, doc in enumerate(docs, start=1):
                snippet = textwrap.shorten(doc, width=160, placeholder=" …")
                print(f"    [{i}] {snippet}")

    # --- Summary table -------------------------------------------------------
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
        if args.benchmark:
            args.filepath = input("Enter the path to your PDF for benchmarking: ").strip()
        else:
            args.filepath = input("Enter the path to your PDF: ").strip()

    if args.benchmark:
        run_benchmark(args.filepath)
    else:
        ingest_pdf(args.filepath, strategy=args.strategy, chunk_size=args.chunk_size)