# Summarizer Service

**Owner:** Arpita Haque
**Phase:** 2 — Core RAG + Summarization (Mar 11 – Mar 28)
**Port:** runs behind the API gateway on port 8002
**Checklist:** `docs/checklist/Summarization_POC_Checklist.pdf`

---

## What This Service Does

Accepts a psychoeducational evaluation PDF and returns a **structured summary** covering:

- Diagnoses and eligibility findings (e.g., SLD, OHI, autism determinations)
- Key test scores and assessment results (instrument names, score types, values, percentiles)
- Accommodations and recommendations
- Evaluation dates and relevant timeline information

**Stateless** — no session state is retained between requests. One document in, one summary out.

---

## Architecture

```
POST /summarize (PDF upload)
        │
        ▼
  pdf_loader.py          ← PyMuPDF extracts text page by page, preserving page numbers
        │
        ▼
  summarizer.py          ← LangChain Refine chain
        │
   ┌────┴──────────────────────────────────────────┐
   │                                               │
chunk 1 → initial_prompt → LLM (Ollama)           │
                 │                                 │
             summary_0 ──► refine_prompt ──► LLM  │
                                  │                │
                              summary_1 ──► ...    │
                                  │                │
                              final summary ───────┘
        │
        ▼
  SummaryResponse (JSON)
```

### Why Refine?

Psychoeducational reports are 40–60 pages and self-referential — a recommendation on page 45 may cite a score from page 12. The **Refine method** processes chunks sequentially and carries a running summary forward, preserving these cross-page relationships. Map-reduce summarizes chunks independently and loses these connections.

Decision documented per checklist item 2 (Research 3).

---

## File Structure

```
summarizer/
├── main.py                  ← FastAPI app, loads config, registers routes
├── config.yaml              ← Feature flag, Ollama model, chunking params, storage paths
├── pyproject.toml           ← Poetry dependencies
├── requirements.txt         ← pip fallback
├── .env.example             ← LangSmith env vars — copy to .env, never commit .env
├── routes/
│   ├── health.py            ← GET /health
│   └── summarize.py         ← POST /summarize
├── services/
│   ├── pdf_loader.py        ← PyMuPDF extraction + LangChain text splitting
│   └── summarizer.py        ← Refine chain implementation
├── utils/
│   └── cleanup.py           ← Temp file context manager + directory purge
└── tests/
    └── test_health.py       ← Smoke tests (no Ollama or real PDF needed)
```

---

## Setup

```bash
cd backend/summarizer

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # (On Windows use: venv\Scripts\activate)

# Using pip
pip install -r requirements.txt

# OR using Poetry
poetry install

# Copy env template and fill in your LangSmith API key
cp .env.example .env
```

---

## Running Locally

```bash
cd backend/summarizer
uvicorn main:app --reload --port 8002
```

Test the health endpoint:

```bash
curl http://localhost:8002/health
# → {"status": "ok", "service": "summarizer"}
```

Test summarization with a sample PDF:

```bash
curl -X POST http://localhost:8002/summarize \
  -F "file=@/path/to/sample_eval.pdf"
```

> **FERPA reminder:** Never use real student documents for local testing. Use synthetic/dummy PDFs only.

---

## Configuration (`config.yaml`)

| Key                                 | Default                       | Description                                                          |
| ----------------------------------- | ----------------------------- | -------------------------------------------------------------------- |
| `summarizer.enabled`                | `true`                        | Feature flag — set to `false` to return 503 from gateway             |
| `summarizer.model`                  | `llama3.2`                    | Ollama model name — update after Phase 1 benchmarking                |
| `summarizer.ollama_base_url`        | `http://localhost:11434`      | Local Ollama instance URL                                            |
| `summarizer.chunk_size`             | `2000`                        | Characters per text chunk — revisit after RAG team Research findings |
| `summarizer.chunk_overlap`          | `200`                         | Overlap between chunks                                               |
| `summarizer.encrypted_storage_path` | `/mnt/securepsych/data`       | LUKS-encrypted mount — all disk writes go here                       |
| `summarizer.temp_dir`               | `/tmp/securepsych/summarizer` | Temp file location (if disk buffering is needed)                     |

---

## API Reference

### `GET /health`

Returns 200 if the service is up.

```json
{ "status": "ok", "service": "summarizer" }
```

### `POST /summarize`

**Form fields:**

| Field  | Type            | Required | Description                     |
| ------ | --------------- | -------- | ------------------------------- |
| `file` | PDF file upload | Yes      | The evaluation PDF to summarize |

> If summarizing a document already ingested into RAG, the API gateway is responsible for fetching its bytes and forwarding them here as a file upload. This service does not accept a `document_id` directly.

**Response:**

```json
{
  "summary": "...",
  "page_count": 48
}
```

**Error codes:**

| Code | Meaning                                                                              |
| ---- | ------------------------------------------------------------------------------------ |
| 413  | PDF exceeds 50 MB size limit                                                         |
| 415  | Unsupported `Content-Type` (must be `application/pdf` or `application/octet-stream`) |
| 422  | Missing file or non-PDF filename                                                     |
| 503  | Feature disabled via `config.yaml`                                                   |

---

## Running Tests

```bash
cd backend/summarizer
pytest tests/ -v
```

Tests do not require Ollama or a real PDF — they verify the app boots and endpoints behave correctly.

---

## Security & FERPA Notes

- **Zero outbound network calls** during summarization — all LLM inference routes through local Ollama. Never add an external LLM API call without Natoli's explicit approval.
- **LangSmith tracing** is configured for metadata only (`LANGCHAIN_HIDE_INPUTS=true`, `LANGCHAIN_HIDE_OUTPUTS=true`). Do not change these settings — doing so would transmit document content externally and is a FERPA violation.
- **Never commit student data** — no real PDFs, IEPs, test scores, or names, even as test fixtures.
- **Never commit `.env`** — contains LangSmith API key.
- Any intermediate outputs written to disk must go to `encrypted_storage_path` from `config.yaml`.

---

## Open TODOs Before Merge

- [ ] Confirm summarization method with Research 3 findings — document decision in PR
- [ ] Test on a 48–60 page sample psychoeducational evaluation document
- [ ] Get at least one sample summary reviewed by Dr. Josh Johnson (checklist item 6)
- [ ] Spot-check 2–3 cross-page references in the test document (checklist item 8)
- [ ] Verify LangSmith dashboard shows only metadata — no document content (checklist item 11)
- [ ] Coordinate `document_id` → bytes lookup contract with Arham / Noble / Mohammed so the gateway can fetch and forward document content to this endpoint
- [ ] Fill in `/health` gateway routing once gateway service is scaffolded

---

## Key Contacts

| Question                                   | Contact                   |
| ------------------------------------------ | ------------------------- |
| Architecture / scope decisions             | Natoli (EL)               |
| Deadlines / process                        | Kai (PM)                  |
| Psych eval domain / summary quality        | Dr. Josh Johnson          |
| FERPA / compliance                         | Jon T. → Dr. Josh Johnson |
| RAG ingestion store / document_id contract | Arham / Noble / Mohammed  |
