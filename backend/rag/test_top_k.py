"""
test_top_k.py — SecurePsych RAG top_k benchmark

Tests top_k values 2, 3, 4, 5 in both fast and deep retrieval modes
against realistic school-psych evaluation questions.

Usage:
    1. Drop sample_psycheval.pdf into backend/rag/
    2. Run:  python test_top_k.py
    3. Read the printed table to pick the best top_k for your documents.

Requirements:
    - Ollama running locally (http://localhost:11434)
    - sample_psycheval.pdf present in this directory
    - pip install -r requirements.txt already done
"""

import sys
import os
import textwrap

# Make sure we can import from this directory
sys.path.insert(0, os.path.dirname(__file__))

from ingestion import ingest_pdf, list_sources
from rag_query import answer_question

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SAMPLE_PDF = os.path.join(os.path.dirname(__file__), "sample_psycheval.pdf")

# Realistic questions a school psychologist might ask
QUESTIONS = [
    "What is the student's name and age?",
    "What is the student's IQ?",
    "do he have any Allergies?",
    "do he have any Disabilities?",
]

TOP_K_VALUES = [2, 3, 4, 5]
MODES = ["fast", "deep"]

DIVIDER = "=" * 80
THIN = "-" * 80


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
def wrap(text: str, width: int = 72, indent: str = "    ") -> str:
    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent)


def print_result(mode: str, top_k: int, question: str, result: dict):
    print(f"\n  [mode={mode}  top_k={top_k}]")
    print(f"  Answer preview:")
    preview = result["answer"][:400] + ("..." if len(result["answer"]) > 400 else "")
    print(wrap(preview))
    sources = {f"p{s['page']}" for s in result["sources"]}
    print(f"  Pages referenced: {', '.join(sorted(sources)) or 'none'}")
    print(f"  Chunks used: {len(result['chunks'])}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print(DIVIDER)
    print("  SecurePsych RAG — top_k Benchmark")
    print(DIVIDER)

    # --- Ingest if needed ---
    if not os.path.isfile(SAMPLE_PDF):
        print(f"\n[ERROR] sample_psycheval.pdf not found at:\n  {SAMPLE_PDF}")
        print("\nDrop the PDF there and re-run the script.")
        sys.exit(1)

    known_sources = list_sources()
    pdf_name = os.path.basename(SAMPLE_PDF)
    if pdf_name not in known_sources:
        print(f"\nIngesting {pdf_name} ...")
        result = ingest_pdf(SAMPLE_PDF)
        print(f"  ✓ Ingested {result['chunks_added']} chunks across {result['pages']} pages.\n")
    else:
        print(f"\n  ✓ {pdf_name} already ingested — skipping re-ingest.\n")

    # --- Run benchmark ---
    for q_idx, question in enumerate(QUESTIONS, start=1):
        print(DIVIDER)
        print(f"  Question {q_idx}/{len(QUESTIONS)}")
        print(f"  {question}")
        print(THIN)

        for mode in MODES:
            for top_k in TOP_K_VALUES:
                try:
                    res = answer_question(question, mode=mode, top_k=top_k)
                    print_result(mode, top_k, question, res)
                except Exception as exc:
                    print(f"\n  [mode={mode}  top_k={top_k}]  ERROR: {exc}")

        print()

    print(DIVIDER)
    print("  Benchmark complete.")
    print("  Recommendation: pick the top_k where answers are complete but not repetitive.")
    print("  Update DEFAULT_TOP_K in rag_query.py once you've decided.")
    print(DIVIDER)


if __name__ == "__main__":
    main()
