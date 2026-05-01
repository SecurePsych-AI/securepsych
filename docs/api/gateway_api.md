# SecurePsych API Gateway — API Reference

**Base URL:** `http://localhost:8000`  
**Version:** 1.0.0  
**All traffic must remain on the school LAN. Zero external network calls are permitted by design.**

---

## Authentication

All endpoints except `/health`, `/api/config`, and `/api/auth/login` require a valid JWT in the `Authorization` header.

```
Authorization: Bearer <token>
```

Tokens carry the fields `sub` (user UUID), `role` (`psychologist` | `admin`), and `exp`. Only `psychologist` and `admin` roles are accepted.

---

### POST /api/auth/login

Obtain a JWT.

**Request**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

**curl**
```bash
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"psychuser","password":"secret"}'
```

---

### POST /api/auth/logout

Revoke a token (added to in-memory denylist).

**Request**
```json
{ "token": "eyJhbGci..." }
```

**Response 200**
```json
{ "status": "ok", "detail": "Token added to denylist" }
```

---

## Projects & History

Projects are the top-level organisational unit — one project per student case. The gateway hashes the raw student ID server-side using a keyed BLAKE2b function; the raw ID is never stored.

> **FERPA note:** `display_label` is validated against common PII patterns (SSN, DOB, 6+ digit district ID). Use case codes such as `"Case 2024-031"`, never a student name or ID number.

---

### POST /api/projects

Create a project for a student case.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `student_id` | string | yes | Raw student identifier — hashed server-side, never persisted |
| `display_label` | string | no | Max 80 chars, no PII patterns |

**Request**
```json
{
  "student_id": "district-id-98765",
  "display_label": "Case 2024-031"
}
```

**Response 201**
```json
{
  "id": "a1b2c3d4-0001-0001-0001-000000000001",
  "display_label": "Case 2024-031",
  "created_at": "2024-09-03T14:22:07.123456+00:00"
}
```

**Errors**

| Status | Detail |
|--------|--------|
| 422 | `display_label` contains PII pattern |
| 401 | Missing/invalid token |

**curl**
```bash
curl -s -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"student_id":"district-id-98765","display_label":"Case 2024-031"}'
```

---

### GET /api/projects

List all projects owned by the authenticated user.

**Response 200** — array of project objects (sorted newest first)
```json
[
  {
    "id": "a1b2c3d4-0001-0001-0001-000000000001",
    "display_label": "Case 2024-031",
    "created_at": "2024-09-03T14:22:07.123456+00:00"
  }
]
```

**curl**
```bash
curl -s http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/projects/{project_id}

Get a single project.

**Response 200** — project object  
**Response 404** — `{"detail":"Project not found"}`

**curl**
```bash
curl -s "http://localhost:8000/api/projects/a1b2c3d4-0001-0001-0001-000000000001" \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/projects/{project_id}/files

List uploaded files associated with this project.

**Response 200**
```json
[
  {
    "id": "c3d4e5f6-0003-0003-0003-000000000003",
    "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98",
    "filename_redacted": "eval_2024_REDACTED.pdf",
    "strategy": "standard",
    "chunks_added": 187,
    "uploaded_at": "2024-09-03T14:30:55.000000+00:00"
  }
]
```

**curl**
```bash
curl -s "http://localhost:8000/api/projects/a1b2c3d4-0001-0001-0001-000000000001/files" \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/projects/{project_id}/threads

List RAG conversation threads for this project (summary only — no messages).

**Response 200**
```json
[
  {
    "id": "cc1d2e3f-4a5b-6c7d-8e9f-a0b1c2d3e4f5",
    "title": null,
    "created_at": "2024-09-03T14:45:00.000000+00:00"
  }
]
```

**curl**
```bash
curl -s "http://localhost:8000/api/projects/a1b2c3d4-0001-0001-0001-000000000001/threads" \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/projects/{project_id}/threads/{thread_id}

Fetch a conversation thread with all messages, ordered by creation time.

**Response 200**
```json
{
  "id": "cc1d2e3f-4a5b-6c7d-8e9f-a0b1c2d3e4f5",
  "title": null,
  "created_at": "2024-09-03T14:45:00.000000+00:00",
  "messages": [
    {
      "id": "d1e2f3a4-b5c6-7d8e-9f0a-b1c2d3e4f5a6",
      "role": "user",
      "content": "What cognitive assessments were administered?",
      "sources": [],
      "created_at": "2024-09-03T14:45:00.000000+00:00"
    },
    {
      "id": "e2f3a4b5-c6d7-8e9f-0a1b-c2d3e4f5a6b7",
      "role": "assistant",
      "content": "The WISC-V was administered...",
      "sources": [
        {
          "source": "eval_2024_REDACTED.pdf",
          "page": 12,
          "parent_id": "12_2",
          "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98"
        }
      ],
      "created_at": "2024-09-03T14:45:03.000000+00:00"
    }
  ]
}
```

**Errors**

| Status | Detail |
|--------|--------|
| 404 | Thread or project not found |

**curl**
```bash
curl -s "http://localhost:8000/api/projects/a1b2c3d4-0001-0001-0001-000000000001/threads/cc1d2e3f-4a5b-6c7d-8e9f-a0b1c2d3e4f5" \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/projects/{project_id}/summaries

List all summarizer runs logged for this project (newest first).

**Response 200**
```json
[
  {
    "id": "f3a4b5c6-d7e8-9f0a-1b2c-d3e4f5a6b7c8",
    "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98",
    "filename_redacted": "eval_2024_REDACTED.pdf",
    "summary": "Psychoeducational Evaluation Summary...",
    "page_count": 24,
    "created_at": "2024-09-03T15:02:11.000000+00:00"
  }
]
```

**curl**
```bash
curl -s "http://localhost:8000/api/projects/a1b2c3d4-0001-0001-0001-000000000001/summaries" \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/projects/{project_id}/jargon-runs

List all jargon simplification runs logged for this project (newest first).

> **FERPA note:** `input_preview` is the first 200 characters of the input only — the full input text is never stored in the gateway database.

**Response 200**
```json
[
  {
    "id": "a4b5c6d7-e8f9-0a1b-2c3d-e4f5a6b7c8d9",
    "level": 3,
    "input_preview": "The examinee demonstrated significant deficits in phonological processing...",
    "simplified_text": "The testing showed that your child has difficulty...",
    "fk_grade": 7.1,
    "created_at": "2024-09-03T15:10:45.000000+00:00"
  }
]
```

**curl**
```bash
curl -s "http://localhost:8000/api/projects/a1b2c3d4-0001-0001-0001-000000000001/jargon-runs" \
  -H "Authorization: Bearer $TOKEN"
```

---

## RAG — Secure Document Q&A

Port 8001 internally. All requests go through the gateway.

> **FERPA note:** `project_id` is required on all write and query routes. The gateway resolves `project_id` to an internal `student_id_hash` before forwarding — the raw student identifier never appears in RAG requests. `student_id` is injected as a mandatory ChromaDB metadata filter, preventing cross-student data leakage.

---

### POST /api/rag/upload/preview

Step 1 of two-step upload. Extracts text and PII entity map for user review before committing.

**Request** — multipart/form-data

| Field | Type | Required |
|-------|------|----------|
| `file` | PDF | yes |

**Response 200**
```json
{
  "preview_token": "9f8e7d6c-5b4a-3210-fedc-ba9876543210",
  "sample_text": "This psychoeducational evaluation was conducted for STUDENT_NAME_1...",
  "entity_map": {
    "STUDENT_NAME_1": "Marcus Johnson",
    "DATE_OF_BIRTH_1": "01/15/2012"
  },
  "page_count": 24,
  "filename": "eval_2024.pdf"
}
```

**curl**
```bash
curl -s -X POST http://localhost:8000/api/rag/upload/preview \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@eval_2024.pdf"
```

---

### POST /api/rag/upload

Ingest a PDF into the RAG vector store, scoped to the given project.

**Request** — multipart/form-data

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `file` | PDF | yes (unless `preview_token`) | |
| `project_id` | string | yes | Gateway resolves to `student_id_hash` |
| `strategy` | string | no | `"standard"` (default) or `"deep"` |
| `preview_token` | string | no | From `/upload/preview`; skips re-extraction |

**Response 200**
```json
{
  "status": "ok",
  "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98",
  "source": "eval_2024_REDACTED.pdf",
  "strategy": "standard",
  "chunks_added": 187,
  "avg_chunk_tokens": 512
}
```

> **FERPA note:** `student_id` (the internal hash) and `redaction_key` are present in the RAG service's raw response but are stripped by the gateway before this response is returned to the client. They must not appear in frontend code or logs.

**Errors**

| Status | Detail |
|--------|--------|
| 400 | Non-PDF file |
| 404 | `project_id` not found or not owned by caller |
| 422 | Text extraction failed |

**curl**
```bash
curl -s -X POST http://localhost:8000/api/rag/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@eval_2024.pdf" \
  -F "project_id=a1b2c3d4-0001-0001-0001-000000000001" \
  -F "strategy=standard"
```

---

### POST /api/rag/query

Ask a question against ingested documents for a project. Persists the exchange to a conversation thread.

**Request** — application/json

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `question` | string | yes | |
| `project_id` | string | yes | |
| `document_id` | string | no | Scope to a single document |
| `thread_id` | string | no | Append to existing thread; omit to create new |
| `mode` | string | no | `"fast"` (default) or `"deep"` |
| `top_k` | int | no | Number of chunks to retrieve (default 3) |

**Request body**
```json
{
  "question": "What cognitive assessments were administered and what were the composite scores?",
  "project_id": "a1b2c3d4-0001-0001-0001-000000000001",
  "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98",
  "thread_id": null,
  "mode": "fast",
  "top_k": 3
}
```

**Response 200**
```json
{
  "answer": "The WISC-V was administered. The student obtained a Full Scale IQ of 88 (Low Average, 25th percentile).",
  "mode": "fast",
  "top_k": 3,
  "thread_id": "cc1d2e3f-4a5b-6c7d-8e9f-a0b1c2d3e4f5",
  "sources": [
    {
      "source": "eval_2024_REDACTED.pdf",
      "page": 12,
      "parent_id": "12_2",
      "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98"
    }
  ]
}
```

> Note: `chunks` (raw chunk text) is stripped by the gateway before this response is returned to the client.

**Errors**

| Status | Detail |
|--------|--------|
| 400 | `project_id` missing |
| 404 | Project not found or not owned by caller |

**curl**
```bash
curl -s -X POST http://localhost:8000/api/rag/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the recommended accommodations?",
    "project_id": "a1b2c3d4-0001-0001-0001-000000000001",
    "mode": "fast",
    "top_k": 3
  }'
```

---

### GET /api/rag/documents

List all documents ingested for a project.

**Query params**

| Param | Required |
|-------|----------|
| `project_id` | yes |

**Response 200**
```json
{
  "total_documents": 1,
  "documents": [
    {
      "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98",
      "filename": "eval_2024_REDACTED.pdf"
    }
  ]
}
```

**curl**
```bash
curl -s "http://localhost:8000/api/rag/documents?project_id=a1b2c3d4-0001-0001-0001-000000000001" \
  -H "Authorization: Bearer $TOKEN"
```

---

### GET /api/rag/documents/{document_id}/content

Retrieve the full reconstructed text of a document. Used internally by Mode B summarization.

**Response 200**
```json
{
  "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98",
  "filename": "eval_2024_REDACTED.pdf",
  "text": "...",
  "page_count": 24
}
```

---

### DELETE /api/rag/documents/{document_id}

Remove a document and all its chunks from the vector store.

The gateway verifies ownership before forwarding: it checks that the document belongs to a project owned by the authenticated user. A document that exists in ChromaDB but is not registered under the caller's project is rejected with 403. On success the gateway also removes the corresponding `UploadedFile` record from its own database.

**Query params**

| Param | Required |
|-------|----------|
| `project_id` | yes |

**Response 200**
```json
{
  "deleted": true,
  "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98",
  "filename": "eval_2024_REDACTED.pdf",
  "chunks_removed": 187
}
```

**Errors**

| Status | Detail |
|--------|--------|
| 403 | Project not found or access denied |
| 403 | Document not found in this project |
| 404 | Document not found in ChromaDB (RAG service) |

**curl**
```bash
curl -s -X DELETE "http://localhost:8000/api/rag/documents/f7e6d5c4-b3a2-9180-7654-3210fedcba98?project_id=a1b2c3d4-0001-0001-0001-000000000001" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Summarizer

Port 8002 internally. Two modes: direct file upload (Mode A) or summarize a previously-ingested RAG document (Mode B).

> Providing `project_id` causes the gateway to persist the summary output to the database for history retrieval. Omitting it is allowed but the run will not be logged.

---

### POST /api/summarize

**Mode A — direct PDF upload** (`multipart/form-data`)

| Field | Type | Required |
|-------|------|----------|
| `file` | PDF ≤ 50 MB | yes |
| `project_id` | string | no (recommended) |

**curl**
```bash
curl -s -X POST http://localhost:8000/api/summarize \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@eval_2024.pdf" \
  -F "project_id=a1b2c3d4-0001-0001-0001-000000000001"
```

**Mode B — summarize an ingested document** (`application/json`)

| Field | Type | Required |
|-------|------|----------|
| `document_id` | string | yes |
| `project_id` | string | no (recommended) |

```json
{
  "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98",
  "project_id": "a1b2c3d4-0001-0001-0001-000000000001"
}
```

**curl**
```bash
curl -s -X POST http://localhost:8000/api/summarize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"document_id":"f7e6d5c4-b3a2-9180-7654-3210fedcba98","project_id":"a1b2c3d4-0001-0001-0001-000000000001"}'
```

**Response 200** (both modes)
```json
{
  "summary": "Psychoeducational Evaluation Summary\n\nDiagnoses: Specific Learning Disability in Reading (Dyslexia)...",
  "page_count": 24
}
```

**Errors**

| Status | Detail |
|--------|--------|
| 400 | Missing `document_id` (Mode B) or missing `file` (Mode A) |
| 415 | Unsupported Content-Type |
| 422 | Non-PDF file or no extractable text |

---

## Jargon Simplifier

Port 8003 internally. Rewrites clinical text for five audience levels.

| Level | Audience |
|-------|----------|
| 1 | Psychologist (clinical terminology preserved) |
| 2 | Educator / coordinator (acronyms defined) |
| 3 | Parent / guardian — **default** |
| 4 | High school student |
| 5 | Elementary-age child |

> Providing `project_id` causes the gateway to persist the run (first 200 chars of input only). Omitting it is allowed but the run will not be logged.

---

### POST /api/jargon/simplify

**JSON mode** (`application/json`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `text` | string | yes | Clinical text to simplify |
| `level` | int | no | 1–5, default 3 |
| `project_id` | string | no | Enables history logging |

**Request**
```json
{
  "text": "The examinee demonstrated significant deficits in phonological processing as measured by the CTOPP-2...",
  "level": 3,
  "project_id": "a1b2c3d4-0001-0001-0001-000000000001"
}
```

**Response 200**
```json
{
  "simplified_text": "The testing showed that your child has difficulty with the sound-based building blocks of reading...",
  "flesch_kincaid_grade": 7.1,
  "level": 3
}
```

**curl**
```bash
curl -s -X POST http://localhost:8000/api/jargon/simplify \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"The examinee demonstrated...","level":3,"project_id":"a1b2c3d4-0001-0001-0001-000000000001"}'
```

**PDF upload mode** (`multipart/form-data`)

| Field | Type | Required |
|-------|------|----------|
| `file` | PDF ≤ 50 MB | yes |
| `level` | string (int) | no |
| `project_id` | string | no |

**curl**
```bash
curl -s -X POST http://localhost:8000/api/jargon/simplify \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@eval_excerpt.pdf" \
  -F "level=3" \
  -F "project_id=a1b2c3d4-0001-0001-0001-000000000001"
```

**Errors**

| Status | Detail |
|--------|--------|
| 422 | `level` out of range (must be 1–5) |
| 422 | `text` missing (JSON mode) |
| 503 | Jargon service disabled in config |

---

## System

### GET /health

```json
{ "status": "ok", "service": "gateway" }
```

### GET /api/config

Returns non-sensitive feature flags.

```json
{
  "rag_enabled": true,
  "summarizer_enabled": true,
  "jargon_enabled": true
}
```

---

## IT Deployment Notes

| Environment Variable | Required | Notes |
|---------------------|----------|-------|
| `JWT_SECRET` | yes | 256-bit hex; no fallback |
| `GATEWAY_USERNAME` | yes | Login username |
| `GATEWAY_PASSWORD` | yes | Login password |
| `GATEWAY_DB_PATH` | yes | Must be under `/mnt/securepsych/`; e.g. `/mnt/securepsych/data/gateway/gateway.db` |
| `STUDENT_HASH_SECRET` | yes | 64-char hex; treat like LUKS master key — never rotate without a migration |

**CORS:** The gateway currently allows all origins (`*`). For production, restrict `allow_origins` in `main.py` to the school frontend's origin (e.g., `http://10.0.1.50:3000`).

**LUKS mount:** All service data paths must be under `/mnt/securepsych/`. The gateway validates this at startup for `GATEWAY_DB_PATH` and at service URL validation for all microservice URLs.

**Mock data:** Sample request/response payloads for each service are in `docs/api/mock/`.
