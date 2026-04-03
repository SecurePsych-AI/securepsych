# RAG Service — SecurePsych AI

Handles PDF ingestion, semantic chunk retrieval, and LLM-powered Q&A using ChromaDB and a local Ollama model.

**Owner:** Arham N., Noble A., Mohammed A.
**Phase:** 2 — Core RAG + Summarization (Mar 11 – Mar 28)
**Port:** runs behind the API gateway on port 8000
**Checklist:** `docs/checklist/RAG_POC_Checklist_1.pdf`

---

## Setup

### 1. Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) — local LLM inference

```bash
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
ollama pull llama3.2:1b
```

> ⚠️ If you see a port conflict, Ollama is already running — skip `ollama serve`.

### 4. Start the API

From inside `backend/rag/`:

```bash
python -m uvicorn api:app --reload
```

> Use `python -m uvicorn` instead of `uvicorn` on Windows if you get a PATH error.

- API: **http://localhost:8000**
- Interactive docs: **http://localhost:8000/docs**

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values. Never commit `.env`.

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Base URL for the local Ollama instance |
| `OLLAMA_MODEL` | `llama3.2` | Model name to use for inference — update after Phase 1 benchmark |
| `CHROMA_PATH` | `./chroma` | Path to the ChromaDB persistent store — must match across all three files |
| `CHROMA_COLLECTION` | `securepsych_docs` | ChromaDB collection name — must match across all three files |
| `CHUNK_SIZE` | `600` | Characters per chunk — validated range is 512–800 per Research 1 & 2 |
| `CHUNK_OVERLAP` | `100` | Overlap between chunks in characters (~17%, within the 15–20% target) |

### `.env.example`

```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
CHROMA_PATH=./chroma
CHROMA_COLLECTION=securepsych_docs
CHUNK_SIZE=600
CHUNK_OVERLAP=100
```

---

## API Reference

### `POST /upload`

Upload a PDF to ingest into ChromaDB.

**Request:** multipart/form-data

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | PDF file | Yes | The evaluation PDF to ingest |

**Example:**
```bash
curl -X POST http://localhost:8000/upload \
     -F "file=@your_document.pdf"
```

**Response:**
```json
{
  "document_id": "32f4419f-93d6-4a3f-a460-6c3e161318a6",
  "filename": "your_document.pdf",
  "chunks_stored": 42,
  "avg_chunk_tokens": 587
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
curl http://localhost:8000/documents
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
curl -X DELETE http://localhost:8000/documents/32f4419f-93d6-4a3f-a460-6c3e161318a6
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

### `POST /query`

Ask a natural-language question against an ingested document.

**Request:** JSON

| Field | Type | Required | Description |
|---|---|---|---|
| `question` | string | Yes | The question to ask |
| `document_id` | string | No | Scope query to a specific document. Omit to search all. |
| `top_k` | int | No | Number of chunks to retrieve (default: 2) |

**Example:**
```bash
curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"question": "What medications were prescribed?", "document_id": "32f4419f-..."}'
```

**Response:**
```json
{
  "answer": "The patient was prescribed Celexa 20mg for depression...",
  "citations": [
    {
      "filename": "student_eval.pdf",
      "page_start": 3,
      "page_end": 3
    }
  ]
}
```

---

## Architecture

```
POST /upload (PDF file)
        │
        ▼
  ingestion.py        ← PyMuPDF extracts text page by page
        │
        ▼
  Token-based chunking (~600 tokens, 20% overlap)
        │
        ▼
  ChromaDB (local persistent vector store)
        │
        ▼
POST /query (question)
        │
        ▼
  rag_query.py        ← vector similarity search → top-K chunks
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
- Token-based chunking (~600 tokens per chunk, within the 512–800 token range confirmed by Research 1 & 2)
- 20% overlap between consecutive chunks to preserve context at boundaries
- `page_start` / `page_end` metadata per chunk for citation support
- `ingest_pdf_bytes()` for byte-stream ingestion from the upload endpoint

### Retrieval Pipeline (`rag_query.py`)
- Semantic chunk retrieval from ChromaDB using vector similarity
- Optional `document_id` filtering for document-scoped queries
- Page-range citation support with deduplication

### Local LLM Integration
- Connects to Ollama at `OLLAMA_BASE_URL`
- Model configurable via `OLLAMA_MODEL` env var
- Handles timeout and connection errors gracefully

### FastAPI Backend (`api.py`)
- `POST /upload`, `GET /documents`, `DELETE /documents/{document_id}`, `POST /query`

---

## Security & FERPA Notes

- **Zero outbound network calls** during ingestion or query — all LLM inference routes through local Ollama. Never add an external API call without Natoli's approval.
- **Never commit `chroma_db/`** — it contains embeddings derived from student documents (FERPA concern). It is listed in `.gitignore`.
- **Never commit `.env`** — it is listed in `.gitignore`.
- **Never commit real student PDFs, IEPs, or test scores**, even as test fixtures. Use synthetic documents only.
- All disk writes for student data must go to the encrypted storage path defined in the shared architecture (`LUKS/fscrypt`).

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `uvicorn: command not found` on Windows | Use `python -m uvicorn api:app --reload` |
| `/query` returns empty results | Make sure `CHROMA_DB_PATH` in `.env` matches across both `api.py` and `rag_query.py` |
| Ollama port conflict on startup | Ollama is already running — skip `ollama serve` |
| Slow first response | Normal — model loads into memory on first request |
| JSON errors with `curl` on Windows | Use Swagger UI at `/docs` instead, or PowerShell with escaped quotes |

---

## Key Contacts

| Question | Contact |
|---|---|
| Architecture / scope decisions | Natoli (EL) |
| Deadlines / process | Kai (PM) |
| Psych eval domain quality | Dr. Josh Johnson |
| FERPA / compliance | Jon T. → Dr. Josh Johnson |
| Summarizer document_id contract | Arpita H. |
