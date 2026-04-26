# RAG Service — SecurePsych AI

Handles PDF ingestion, semantic chunk retrieval, and LLM-powered Q&A using ChromaDB and a local Ollama model.

**Owner:** Arham N., Noble A., Mohammed A.
**Phase:** 2 — Core RAG + Summarization (Mar 11 – Mar 28)
**Port:** runs behind the API gateway on port 8001
**Checklist:** `docs/checklist/RAG_POC_Checklist_1.pdf`

---

## Setup

### 1. Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) — local LLM inference

```bash
python -m venv venv
source venv/bin/activate  # (On Windows use: venv\Scripts\activate)
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your local values — see the table below. Never commit `.env`.

### 3. Start Ollama

```bash
ollama serve
```

In a separate terminal, pull the model specified in your `.env`:

```bash
ollama pull qwen2.5:7b-instruct
```

> ⚠️ If you see a port conflict, Ollama is already running — skip `ollama serve`.

### 4. Start the API

From inside `backend/rag/`:

```bash
python -m uvicorn api:app --reload --port 8001
```

> Use `python -m uvicorn` instead of `uvicorn` on Windows if you get a PATH error.

- API: **http://localhost:8001**
- Interactive docs: **http://localhost:8001/docs**

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values. Never commit `.env`.

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Base URL for the local Ollama instance |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct` | Model name — update after benchmarking |
| `CHROMA_PATH` | `./chroma` | Path to the ChromaDB persistent store — RAG-internal only, not accessed by other services |
| `CHROMA_COLLECTION` | `securepsych_docs` | ChromaDB collection name — RAG-internal only, not shared with other services |
| `CHUNK_SIZE` | `600` | Target tokens per chunk — validated range 512–800 per Research 1 & 2 |
| `CHUNK_OVERLAP` | `0.20` | Overlap fraction for sliding-window chunking (20%) |

### `.env.example`

```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
CHROMA_PATH=./chroma
CHROMA_COLLECTION=securepsych_docs
CHUNK_SIZE=600
CHUNK_OVERLAP=0.20
```

---

## API Reference

### `POST /upload`

Upload a PDF to ingest into ChromaDB.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | PDF file | Yes | The evaluation PDF to ingest |

**Example:**
```bash
curl -X POST http://localhost:8001/upload \
     -F "file=@your_document.pdf"
```

**Response:**
```json
{
  "status": "ok",
  "document_id": "32f4419f-93d6-4a3f-a460-6c3e161318a6",
  "source": "your_document.pdf",
  "strategy": "standard",
  "chunks_added": 42,
  "avg_chunk_tokens": 487
}
```

**Error codes:**

| Code | Meaning |
|---|---|
| 400 | Non-PDF file uploaded, or file is empty |
| 422 | Text extraction failed — no readable content found in PDF |

---

### `GET /documents`

List all documents currently stored in ChromaDB.

**Example:**
```bash
curl http://localhost:8001/documents
```

**Response:**
```json
{
  "total_documents": 2,
  "documents": [
    {
      "document_id": "32f4419f-93d6-4a3f-a460-6c3e161318a6",
      "filename": "student_eval.pdf"
    }
  ]
}
```

---

### `DELETE /documents/{document_id}`

Remove a document and all its chunks from ChromaDB.

**Example:**
```bash
curl -X DELETE http://localhost:8001/documents/32f4419f-93d6-4a3f-a460-6c3e161318a6
```

**Response:**
```json
{
  "deleted": true,
  "document_id": "32f4419f-93d6-4a3f-a460-6c3e161318a6",
  "filename": "student_eval.pdf",
  "chunks_removed": 42
}
```

**Error codes:**

| Code | Meaning |
|---|---|
| 404 | No document found with that ID |

---

### `GET /documents/{document_id}/content`

Retrieve the full reconstructed text of an ingested document. Used by the API gateway when orchestrating summarization of a previously-ingested PDF — the gateway fetches content here and forwards it to the Summarizer. No other service calls this endpoint directly.

**Example:**
```bash
curl http://localhost:8001/documents/32f4419f-93d6-4a3f-a460-6c3e161318a6/content
```

**Response:**
```json
{
  "document_id": "32f4419f-93d6-4a3f-a460-6c3e161318a6",
  "filename": "student_eval.pdf",
  "page_count": 48,
  "text": "Patient Name: ..."
}
```

> **Note:** Reconstructed text contains some repeated content at chunk boundaries (due to 20% overlap). The gateway consumer is expected to forward these bytes as-is; downstream re-chunking handles the overlap.

**Error codes:**

| Code | Meaning |
|---|---|
| 404 | No document found with that ID |

---

### `POST /query`

Ask a natural-language question against an ingested document.

**Request:** JSON

| Field | Type | Required | Description |
|---|---|---|---|
| `question` | string | Yes | The question to ask |
| `document_id` | string | No | Scope query to a specific document. Omit to search all. |
| `mode` | string | No | `"fast"` (default) or `"deep"` — see below |
| `top_k` | int | No | Number of seed chunks to retrieve (default: 3) |

**Retrieval modes:**

| Mode | Description |
|---|---|
| `fast` | Vector similarity search with keyword reranking — lower latency |
| `deep` | Vector search + full-page expansion — higher accuracy for complex queries |

**Example:**
```bash
curl -X POST http://localhost:8001/query \
     -H "Content-Type: application/json" \
     -d '{"question": "What medications were prescribed?", "document_id": "32f4419f-...", "mode": "fast"}'
```

**Response:**
```json
{
  "answer": "The patient was prescribed Celexa 20mg for depression...",
  "mode": "fast",
  "top_k": 3,
  "sources": [
    {
      "source": "student_eval.pdf",
      "page": 3,
      "parent_id": "3_1",
      "document_id": "32f4419f-93d6-4a3f-a460-6c3e161318a6"
    }
  ],
  "chunks": []
}
```

> `chunks` is the full list of retrieved chunk dicts used to build the prompt — useful for debugging. Can be stripped at the gateway before forwarding to the client.

**Error codes:**

| Code | Meaning |
|---|---|
| 422 | Malformed request body |

---

## Architecture

```
POST /upload (PDF file)
        │
        ▼
  ingestion.py        ← PyMuPDF extracts text; auto-detects and strips boilerplate
        │
        ▼
  Two chunking strategies:
    standard → sliding token window (~600 tokens, 20% overlap)
    deep     → page-boundary chunks with overflow carry-forward
        │
        ▼
  ChromaDB (local persistent vector store)
        │
        ▼
POST /query (question)
        │
        ▼
  rag_query.py        ← over-fetches candidates, reranks by semantic + keyword + header score
        │
        ▼
  deep mode: page expansion around matched chunks
        │
        ▼
  Prompt construction + Ollama (local LLM)
        │
        ▼
  Answer + page citations
```

---

## What Was Built

### Ingestion Pipeline (`ingestion.py`)

Two chunking strategies selectable per ingest call:

**Standard (default):** sliding token window, ~600 tokens per chunk, 20% overlap. Suitable for fast-mode retrieval and most Q&A queries.

**Deep:** page-boundary aware chunking with overflow carry-forward. Each chunk is labeled by its origin page. Used when ingesting for deep-mode retrieval where full-page context expansion matters.

Both strategies share the same `parent_id` schema (`"{page}_{chunk_index}"`) so `rag_query.py` handles them identically.

Additional features: automatic boilerplate detection strips repeated headers/footers before chunking (threshold: line appears on ≥40% of pages). A built-in benchmark harness (`python ingestion.py --benchmark <pdf>`) compares chunk size configurations (512, 600, 768, 800 tokens) against representative queries.

### Retrieval Pipeline (`rag_query.py`)

**Fast mode:** over-fetches `top_k × 4` candidates from ChromaDB, then reranks by a weighted score combining cosine similarity (55%), keyword overlap with query expansion (30%), and section-heading boosts (15%). Returns top `top_k` after deduplication.

**Deep mode:** same vector search as fast mode for seed chunks, then expands each matched chunk to all chunks on the same page. Returns the full page context sorted in document order.

Both modes use `_prioritize_chunks_for_question()` to front-load the most relevant section heading into the prompt context.

### Local LLM Integration
- Connects to Ollama at `OLLAMA_BASE_URL`
- Model configurable via `OLLAMA_MODEL` env var (default: `qwen2.5:7b-instruct`)
- Handles timeout and connection errors gracefully

### FastAPI Backend (`api.py`)
- `POST /upload`, `GET /documents`, `DELETE /documents/{document_id}`, `GET /documents/{document_id}/content`, `POST /query`

---

## Security & FERPA Notes

- **Zero outbound network calls** during ingestion or query — all LLM inference routes through local Ollama. Never add an external API call without Natoli's approval.
- **Never commit `chroma/`** — contains embeddings derived from student documents (FERPA concern). Listed in `.gitignore`.
- **Never commit `.env`** — listed in `.gitignore`.
- **Never commit real student PDFs, IEPs, or test scores**, even as test fixtures. Use synthetic documents only.
- All disk writes for student data must go to the encrypted storage path defined in the shared architecture (LUKS/fscrypt).

---

## Known Limitations

- **Embedding quality misses:** certain query types (diagnoses, drug allergies phrased as adverse reactions) fail to retrieve the correct chunk at any `top_k`. This is an embedding model limitation, not a retrieval parameter issue. Documented in `rag_query.py`. Deep mode partially compensates via page expansion.
- **Scanned PDFs:** image-only PDFs return 422 on upload — no extractable text. Flagged for Phase 3.
- **Reconstructed text overlap:** `/content` endpoint output contains duplicate text at chunk boundaries. Acceptable for the POC; the gateway consumer forwards bytes as-is and downstream re-chunking handles overlap.

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `uvicorn: command not found` on Windows | Use `python -m uvicorn api:app --reload` |
| `/query` returns empty results | Check `CHROMA_PATH` in `.env` — must match across `api.py`, `rag_query.py`, and `ingestion.py` |
| Ollama port conflict on startup | Ollama is already running — skip `ollama serve` |
| Slow first response | Normal — model loads into memory on first request |
| JSON errors with `curl` on Windows | Use Swagger UI at `/docs` instead, or PowerShell with escaped quotes |

---

## Key Contacts

| Question | Contact |
|----------|---------|
| Architecture / scope decisions | Natoli (EL) |
| Deadlines / process | Kai (PM) |
| Psych eval domain quality | Dr. Josh Johnson |
| FERPA / compliance | Jon T. → Dr. Josh Johnson |
| Summarizer `document_id` contract | Arpita H. |
