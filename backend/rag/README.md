# RAG Service — SecurePsych AI

Handles PDF ingestion, semantic chunk retrieval, and LLM-powered Q&A using ChromaDB and a local Ollama model.

---

## How to Run

### 1. Prerequisites

Make sure you have the following installed:

- Python 3.10+
- [Ollama](https://ollama.com/) — local LLM inference
- The following Python packages:

```bash
pip install fastapi uvicorn pymupdf chromadb requests
```

---

### 2. Start Ollama

Ollama must be running before you start the API. Open a terminal and run:

```bash
ollama serve
```

Then in a separate terminal, pull the model if you haven't already:

```bash
ollama pull llama3.2:1b
```

> ⚠️ If you see a port conflict error, Ollama is already running in the background — you can skip `ollama serve` and proceed.

---

### 3. Start the API

From inside the `backend/rag/` folder, run:

```bash
python -m uvicorn api:app --reload
```

> Use `python -m uvicorn` instead of just `uvicorn` if you're on Windows and get a PATH error.

The API will be available at: **http://localhost:8000**

You can explore all endpoints interactively at: **http://localhost:8000/docs**

---

## API Endpoints

### `POST /upload`
Upload a PDF to ingest into ChromaDB.

```bash
curl -X POST http://localhost:8000/upload \
     -F "file=@your_document.pdf"
```

Returns a `document_id` you can use to query against a specific file.

---

### `GET /documents`
List all documents currently stored in ChromaDB.

```bash
curl http://localhost:8000/documents
```

---

### `DELETE /documents/{document_id}`
Remove a document and all its chunks from ChromaDB.

```bash
curl -X DELETE http://localhost:8000/documents/<document_id>
```

---

### `POST /query`
Ask a question against an ingested document (or all documents).

```bash
curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"question": "What medications were prescribed?", "document_id": "<document_id>"}'
```

Leave out `document_id` to search across all ingested documents.

---

## What Was Built

### Ingestion Pipeline (`ingestion.py`)
- Replaced page-based chunking with **token-based chunking** (~600 tokens per chunk)
- Added **20% overlap** between consecutive chunks to preserve context at boundaries
- Added approximate token counting (character-based, ~4 chars/token)
- Added `page_start` and `page_end` metadata per chunk instead of a single page reference
- Implemented `ingest_pdf_bytes()` to support byte-stream ingestion from the API upload endpoint
- Returns structured JSON responses instead of printing to console

### Retrieval Pipeline (`rag_query.py`)
- Semantic chunk retrieval from ChromaDB using vector similarity
- Optional filtering by `document_id` for document-scoped queries
- Page-range citation support with deduplication logic

### Local LLM Integration
- Connected to Ollama at `localhost:11434`
- Uses `llama3.2:1b` (switched from `llama3.2:3b` for faster inference)
- Handles timeout and connection errors gracefully

### FastAPI Backend (`api.py`)
- `POST /upload` — PDF ingestion endpoint
- `GET /documents` — lists all stored documents
- `DELETE /documents/{document_id}` — removes a document and its chunks
- `POST /query` — RAG Q&A endpoint

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `uvicorn: command not found` on Windows | Use `python -m uvicorn api:app --reload` |
| Swagger `/query` returns empty results | Make sure `chroma_db/` path in `api.py` and `rag_query.py` match |
| Ollama port conflict on startup | Ollama is already running — skip `ollama serve` |
| Slow first response from Ollama | Normal — model loads into memory on first request, subsequent ones are faster |
| JSON formatting errors with `curl` on Windows | Use the Swagger UI at `/docs` instead, or use PowerShell with escaped quotes |

---

## Notes

- `chroma_db/` is listed in `.gitignore` — do not commit it (contains embeddings derived from student documents, FERPA concern)
- Do not commit any real student PDFs or IEPs to the repo
- If migrating to a larger vector database in the future, the architecture is designed to support a swap to **Qdrant** without rewriting the ingestion or query logic
