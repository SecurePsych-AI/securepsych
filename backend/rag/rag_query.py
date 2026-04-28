from __future__ import annotations

import os
import re
from collections import Counter
from typing import Literal

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration (override via env vars)
# ---------------------------------------------------------------------------
CHROMA_PATH: str     = os.environ["CHROMA_PATH"]
COLLECTION_NAME: str = os.environ["CHROMA_COLLECTION"]
OLLAMA_BASE_URL: str = os.environ["OLLAMA_BASE_URL"]
OLLAMA_MODEL: str    = os.environ["OLLAMA_MODEL"]

DEFAULT_TOP_K: int = 3
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
# Fast-mode reranking helpers
# ---------------------------------------------------------------------------
STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "what", "which", "who",
    "does", "do", "did", "of", "in", "on", "for", "to", "and", "or",
    "this", "that", "with", "from", "it", "as", "be", "by", "at", "about",
    "into", "through", "using", "used", "say", "says"
}

PHRASE_HINTS = {
    "background": ["student background"],
    "student background": ["student background"],
    "age": ["age", "date of birth", "dob", "grade", "school"],
    "date of birth": ["date of birth", "dob", "age", "grade", "school"],
    "dob": ["date of birth", "dob", "age", "grade", "school"],
    "grade": ["grade", "school", "date of birth", "age"],
    "school": ["school", "grade", "date of birth", "age"],
    "report header": ["date of birth", "age", "grade", "school", "name"],

    "recommendation": ["recommendations", "areas of support", "optional areas of support"],
    "recommendations": ["recommendations", "areas of support", "optional areas of support"],

    "assessment tools": ["assessment instruments", "assessment tools", "evaluated using", "using the following"],
    "tests used": ["assessment instruments", "evaluated using", "using the following"],
    "assessment instruments": ["assessment instruments", "evaluated using", "using the following"],

    "diagnosis": ["diagnosis", "diagnoses", "summary", "eligibility"],
    "diagnoses": ["diagnosis", "diagnoses", "summary", "eligibility"],
    "medications": ["medications", "prescribed", "start"],

    "observation": ["observation", "observed", "school psychologist observed"],
    "observations": ["observation", "observed", "school psychologist observed"],
    "observations made by the school psychologist": ["observation", "school psychologist observed"],
    "school psychologist": ["observation", "school psychologist observed"],
}


def _normalize_text(text: str) -> str:
    """
    Lowercase, remove punctuation, collapse whitespace, and normalize common
    plural/variant forms used in user questions.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\bstudents\b", "student", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokenize(text: str) -> list[str]:
    return [t for t in _normalize_text(text).split() if t and t not in STOPWORDS]


def _expanded_query_terms(query: str) -> set[str]:
    """
    Expand the query with a few domain-specific hints so obvious section/header
    questions have a better chance in fast mode.
    """
    q_norm = _normalize_text(query)
    terms = set(_tokenize(query))

    for trigger, hints in PHRASE_HINTS.items():
        if trigger in q_norm:
            for hint in hints:
                terms.update(_tokenize(hint))

    return terms


def _keyword_overlap_score(query: str, chunk_text: str) -> float:
    """
    Returns a score from 0 to 1 based on whether important query terms appear
    in the chunk text.
    """
    q_terms = _expanded_query_terms(query)
    if not q_terms:
        return 0.0

    c_terms = _tokenize(chunk_text)
    if not c_terms:
        return 0.0

    c_counts = Counter(c_terms)
    overlap = sum(min(1, c_counts[t]) for t in q_terms if t in c_counts)
    return overlap / max(len(q_terms), 1)


def _header_boost(query: str, chunk_text: str, page: int) -> float:
    """
    Small targeted boosts for obvious report headings / demographic fields.
    """
    q_norm = _normalize_text(query)
    c_norm = _normalize_text(chunk_text)

    boost = 0.0

    if any(x in q_norm for x in ["age", "date of birth", "dob", "grade", "school", "report header", "name"]):
        if any(x in c_norm for x in ["date of birth", "age", "grade", "school", "name"]):
            boost += 0.35
        if page == 1:
            boost += 0.20

    if "background" in q_norm and "student background" in c_norm:
        boost += 0.50

    if any(x in q_norm for x in ["recommendation", "recommendations"]):
        if any(x in c_norm for x in ["recommendations", "areas of support", "optional areas of support"]):
            boost += 0.65

    if any(x in q_norm for x in ["assessment tools", "tests used", "assessment instruments"]):
        if any(x in c_norm for x in ["assessment instruments", "evaluated using", "using the following"]):
            boost += 0.45

    if any(x in q_norm for x in ["diagnosis", "diagnoses"]):
        if any(x in c_norm for x in ["diagnoses", "summary", "eligibility"]):
            boost += 0.30

    if any(x in q_norm for x in ["observation", "observations"]):
        if any(x in c_norm for x in ["observation", "observed", "school psychologist observed"]):
            boost += 0.45

    if "school psychologist" in q_norm and "observation" in q_norm:
        if "observation" in c_norm or "the school psychologist observed" in c_norm:
            boost += 0.50

    return boost


def _rerank_score(query: str, chunk: dict) -> float:
    """
    Combine Chroma semantic similarity with keyword overlap and header boosts.

    Lower distance is better in Chroma cosine distance, so convert it into a
    simple bounded similarity score.
    """
    distance = chunk.get("distance", 1.0)
    semantic_score = 1.0 / (1.0 + max(distance, 0.0))

    keyword_score = _keyword_overlap_score(query, chunk["text"])
    header_score = _header_boost(query, chunk["text"], chunk.get("page", -1))

    return (
        0.55 * semantic_score +
        0.30 * keyword_score +
        0.15 * header_score
    )


# ---------------------------------------------------------------------------
# retrieve_chunks — FAST MODE
# ---------------------------------------------------------------------------
def retrieve_chunks(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    document_id: str | None = None,
) -> list[dict]:
    """
    Run a ChromaDB vector similarity search, over-fetch candidates, rerank them,
    and return the best top_k chunks.
    """
    collection = _get_collection()

    where_filter = {"document_id": document_id} if document_id else None
    fetch_k = max(top_k * 4, 8)

    results = collection.query(
        query_texts=[query],
        n_results=fetch_k,
        include=["documents", "metadatas", "distances"],
        where=where_filter,
    )

    candidates = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        candidates.append({
            "text":        doc,
            "parent_id":   meta.get("parent_id", ""),
            "page":        meta.get("page", -1),
            "source":      meta.get("source", ""),
            "document_id": meta.get("document_id", ""),
            "distance":    dist,
        })

    reranked = sorted(
        candidates,
        key=lambda c: _rerank_score(query, c),
        reverse=True,
    )

    seen: set[str] = set()
    final_chunks: list[dict] = []

    for chunk in reranked:
        pid = chunk["parent_id"]
        if pid in seen:
            continue
        seen.add(pid)
        final_chunks.append(chunk)
        if len(final_chunks) >= top_k:
            break

    return final_chunks


# ---------------------------------------------------------------------------
# deep_retrieve_chunks — DEEP MODE
# ---------------------------------------------------------------------------
def deep_retrieve_chunks(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    document_id: str | None = None,
) -> list[dict]:
    """
    Two-step retrieval that expands matched chunks to their full page section.
    """
    seed_chunks = retrieve_chunks(query, top_k=top_k, document_id=document_id)
    if not seed_chunks:
        return []

    matched_pages: set[str] = set()
    for chunk in seed_chunks:
        page_str = _page_from_parent_id(chunk["parent_id"])
        matched_pages.add(page_str)

    collection = _get_collection()
    expanded: dict[str, dict] = {}

    for page_str in matched_pages:
        try:
            page_int = int(page_str)
        except ValueError:
            continue

        if document_id:
            where_clause = {
                "$and": [
                    {"page": {"$eq": page_int}},
                    {"document_id": {"$eq": document_id}},
                ]
            }
        else:
            where_clause = {"page": page_int}

        results = collection.get(
            where=where_clause,
            include=["documents", "metadatas"],
        )

        for doc, meta in zip(results["documents"], results["metadatas"]):
            pid = meta.get("parent_id", "")
            if pid not in expanded:
                expanded[pid] = {
                    "text":        doc,
                    "parent_id":   pid,
                    "page":        meta.get("page", -1),
                    "chunk_idx":   meta.get("chunk_idx", 0),
                    "source":      meta.get("source", ""),
                    "document_id": meta.get("document_id", ""),
                    "distance":    None,
                }

    for chunk in seed_chunks:
        pid = chunk["parent_id"]
        if pid not in expanded:
            expanded[pid] = chunk

    sorted_chunks = sorted(
        expanded.values(),
        key=lambda c: (c.get("page", 0), c.get("chunk_idx", 0)),
    )

    return sorted_chunks


# ---------------------------------------------------------------------------
# References helpers
# ---------------------------------------------------------------------------
def _unique_sources(chunks: list[dict]) -> list[dict]:
    seen = set()
    refs = []

    for c in chunks:
        ref = (c["source"], c["page"], c["parent_id"], c["document_id"])
        if ref in seen:
            continue
        seen.add(ref)
        refs.append({
            "source": c["source"],
            "page": c["page"],
            "parent_id": c["parent_id"],
            "document_id": c["document_id"],
        })

    return refs


def _question_heading_priority(question: str) -> list[str]:
    q_norm = _normalize_text(question)
    priorities: list[str] = []

    if "student background" in q_norm or "background" in q_norm:
        priorities.extend(["student background"])
    if "assessment instruments" in q_norm or "assessment tools" in q_norm or "tests used" in q_norm:
        priorities.extend(["assessment instruments", "evaluated using"])
    if "recommendation" in q_norm:
        priorities.extend(["recommendations", "areas of support", "optional areas of support"])
    if "observation" in q_norm:
        priorities.extend(["observation", "the school psychologist observed"])

    return priorities


def _prioritize_chunks_for_question(question: str, chunks: list[dict]) -> list[dict]:
    """
    Sort chunks so those containing the requested section heading appear earlier
    in the prompt context.
    """
    priorities = _question_heading_priority(question)
    if not priorities:
        return chunks

    def sort_key(chunk: dict):
        text_norm = _normalize_text(chunk["text"])
        heading_hit = any(p in text_norm for p in priorities)
        return (
            0 if heading_hit else 1,
            chunk.get("page", 0),
            chunk.get("chunk_idx", 0),
        )

    return sorted(chunks, key=sort_key)


# ---------------------------------------------------------------------------
# answer_question — main entry point
# ---------------------------------------------------------------------------
def answer_question(
    question: str,
    mode: Literal["fast", "deep"] = "fast",
    top_k: int = DEFAULT_TOP_K,
    document_id: str | None = None,
) -> dict:
    """
    Answer a question using the RAG pipeline.
    """
    if mode == "deep":
        chunks = deep_retrieve_chunks(question, top_k=top_k, document_id=document_id)
    else:
        chunks = retrieve_chunks(question, top_k=top_k, document_id=document_id)

    if not chunks:
        return {
            "answer": "No relevant content found in the ingested documents.",
            "mode": mode,
            "top_k": top_k,
            "sources": [],
            "chunks": [],
        }

    chunks = _prioritize_chunks_for_question(question, chunks)

    context_parts: list[str] = []
    total_chars = 0

    for chunk in chunks:
        snippet = (
            f"[Source: {chunk['source']} | Page: {chunk['page']} | Chunk: {chunk['parent_id']}]\n"
            f"{chunk['text']}"
        )
        if total_chars + len(snippet) > MAX_CONTEXT_CHARS:
            break
        context_parts.append(snippet)
        total_chars += len(snippet)

    context_text = "\n\n---\n\n".join(context_parts)

    mode_note = (
        "FAST mode means a smaller set of directly retrieved chunks was provided. "
        "Be careful not to infer missing details."
        if mode == "fast"
        else
        "DEEP mode means the system expanded retrieval to include broader page-level context "
        "around the best matches."
    )

    prompt = (
        "You are a helpful AI assistant supporting a school psychologist.\n"
        f"Retrieval mode used: {mode.upper()}.\n"
        f"{mode_note}\n"
        "Answer the question using ONLY the provided document excerpts.\n"
        "If the excerpts contain the answer, provide a direct, natural answer in 1-3 sentences.\n"
        "For summary questions, summarize only the excerpts that directly answer the requested section or topic.\n"
        "If the question names a section such as Observation, Student Background, Assessment Instruments, or Recommendations, "
        "prioritize that section heading and its contents.\n"
        "Use neutral professional wording close to the excerpts.\n"
        "Do NOT paraphrase into unusual, stronger, or more interpretive language than the text supports.\n"
        "Do NOT estimate, infer, or add facts that are not supported by the excerpts.\n"
        "Do NOT generate a References section yourself.\n"
        "If the answer is not present in the excerpts, say exactly: I don't know.\n\n"
        f"Document Excerpts:\n{context_text}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

    llm = _get_llm()
    answer_text = llm.invoke(prompt).strip()

    sources = _unique_sources(chunks)

    return {
        "answer": answer_text,
        "mode": mode,
        "top_k": top_k,
        "sources": sources,
        "chunks": chunks,
    }


# ---------------------------------------------------------------------------
# CLI convenience
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python rag_query.py '<question>' [fast|deep] [top_k] [document_id]")
        sys.exit(1)

    q = sys.argv[1]
    m = sys.argv[2] if len(sys.argv) > 2 else "fast"
    k = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_TOP_K
    d = sys.argv[4] if len(sys.argv) > 4 else None

    result = answer_question(q, mode=m, top_k=k, document_id=d)
    print(json.dumps({
        "answer": result["answer"],
        "mode": result["mode"],
        "top_k": result["top_k"],
        "sources": result["sources"],
    }, indent=2))