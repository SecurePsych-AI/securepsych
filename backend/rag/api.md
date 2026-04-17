# RAG Microservice — API Documentation

**Base URL:** `http://localhost:8000`
**Version:** 2.0
**Owner:** Arham N., Noble A., Mohammed A.

This document describes the service-level contract for the RAG microservice.
Natoli — the five endpoints below are what the gateway should route to.

---

## Endpoints

### `POST /upload`

Ingest a PDF into ChromaDB. Returns a `document_id` that can be passed to
`/query` or `/documents/{document_id}/content` to scope requests to this file.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | PDF file | Yes | The evaluation PDF to ingest |

**Response:**
```json
{
  "status": "ok",
  "document_id": "32f4419f-93d6-4a3f-a460-6c3e161318a6",
  "source": "student_eval.pdf",
  "pages": 48,
  "chunks_added": 312
}
```

**Error codes:**

| Code | Meaning |
|---|---|
| 400 | Non-PDF file uploaded, or file is empty |
| 422 | Text extraction failed — PDF may be scanned or image-only |

---

### `GET /documents`

List all documents currently stored in ChromaDB.

**Request:** none

**Response:**
```json
{
  "total_documents": 2,
  "documents": [
    {
      "document_id": "32f4419f-93d6-4a3f-a460-6c3e161318a6",
      "filename": "student_eval.pdf"
    },
    {
      "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "filename": "psych_report_2024.pdf"
    }
  ]
}
```

---

### `DELETE /documents/{document_id}`

Remove a document and all its chunks from ChromaDB.

**Path parameter:**

| Parameter | Type | Description |
|---|---|---|
| `document_id` | string | UUID returned by `POST /upload` |

**Response:**
```json
{
  "deleted": true,
  "document_id": "32f4419f-93d6-4a3f-a460-6c3e161318a6",
  "filename": "student_eval.pdf",
  "chunks_removed": 312
}
```

**Error codes:**

| Code | Meaning |
|---|---|
| 404 | No document found with that ID |

---

### `GET /documents/{document_id}/content`

Retrieve the full reconstructed text of an ingested document.
Used internally by the Summarizer service to avoid re-uploading
an already-ingested PDF.

**Path parameter:**

| Parameter | Type | Description |
|---|---|---|
| `document_id` | string | UUID returned by `POST /upload` |

**Response:**
```json
{
  "document_id": "32f4419f-93d6-4a3f-a460-6c3e161318a6",
  "filename": "student_eval.pdf",
  "page_count": 48,
  "text": "Patient Name: Mrs. Little..."
}
```

**Error codes:**

| Code | Meaning |
|---|---|
| 404 | No document found with that ID |

---

### `POST /query`

Ask a natural-language question against an ingested document.
Supports two retrieval modes — `fast` (default) and `deep`.

**Request:** `application/json`

| Field | Type | Required | Description |
|---|---|---|---|
| `question` | string | Yes | The question to ask |
| `document_id` | string | No | Scope query to a specific document. Omit to search all. |
| `mode` | string | No | `"fast"` (default) or `"deep"` — see below |
| `top_k` | int | No | Number of chunks to retrieve (default: 3) |

**Retrieval modes:**

| Mode | Description |
|---|---|
| `fast` | Standard vector similarity search — lower latency |
| `deep` | Vector search + full page expansion — higher accuracy for complex queries |

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
  ]
}
```

**Error codes:**

| Code | Meaning |
|---|---|
| 422 | Malformed request body |

---

## Notes for Gateway Integration

- All endpoints are unauthenticated at the service level — authentication is handled at the gateway.
- `document_id` is a UUID generated at ingest time and is stable for the lifetime of that document in ChromaDB.
- The `chunks` field is included in `/query` responses for debugging but can be stripped at the gateway before forwarding to the client.
- Scanned PDFs (image-only) will return a 422 on upload — this is a known limitation flagged for Phase 3.
