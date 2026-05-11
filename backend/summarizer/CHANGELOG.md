# Changelog — `backend/summarizer`

All notable changes to the summarizer microservice are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.3.0] — 2026-04-18

### Changed

- **`routes/summarize.py`** — Endpoint is now PDF-upload-only. The `document_id`
  form parameter and its HTTP 501 stub have been removed. Responsibility for fetching
  a previously-ingested document's bytes and forwarding them to this endpoint belongs
  to the API gateway layer, keeping this service stateless and single-purpose.

- **`routes/summarize.py`** — Removed `method` field from `SummaryResponse`. The
  summarization strategy (Refine) is an internal implementation detail; callers do
  not need it in the response contract.

- **`routes/summarize.py`** — HTTP 413 error message now includes the numeric byte
  limit: `"PDF exceeds maximum allowed size of {_MAX_PDF_BYTES} bytes."` so clients
  receive an actionable value rather than a fixed string.

---

## [0.2.0] — 2026-04-08

### Security

- **`main.py`** — Set `LANGCHAIN_HIDE_INPUTS=true` and `LANGCHAIN_HIDE_OUTPUTS=true`
  unconditionally in code, before any LangChain import. Prevents LangSmith from
  capturing prompt payloads (which contain full document text) regardless of `.env`
  configuration. Required for FERPA compliance. Verified against LangSmith SDK source:
  `get_env_var("HIDE_INPUTS", namespaces=("LANGSMITH","LANGCHAIN"))` is the authoritative
  read path in `Client.__init__`.

- **`routes/summarize.py`** — Three input-validation fixes:
  - Added `_MAX_PDF_BYTES = 50 MB` constant and bounded `file.read(_MAX_PDF_BYTES + 1)`
    with HTTP 413 response. Prevents memory-exhaustion DoS from large uploads.
  - Added `Content-Type` header check against `{"application/pdf", "application/octet-stream"}`.
    Returns HTTP 415. Blocks upload-filter bypass via file rename.
  - Added `file.filename is None` guard before calling `.lower()`. Prevents uncaught
    `AttributeError` (HTTP 500) on fileless multipart requests.

- **`utils/cleanup.py`** — `temp_file_context` now reads `encrypted_storage_path` from
  `config.yaml` and passes it as `dir=` to `tempfile.mkstemp()`. All temporary files
  are written to the LUKS-encrypted mount (`/mnt/securepsych/data`). Fails closed
  (`FileNotFoundError`) if the mount is absent — will not silently fall back to `/tmp`.

### Changed

- **`services/summarizer.py`** — Corrected module docstring. Previous text claimed
  "zero document content" is transmitted to LangSmith as a structural property. The
  correct statement is that it depends on the `LANGCHAIN_HIDE_INPUTS/OUTPUTS` guards
  in `main.py`. Docstring now explicitly references those guards.

### Added

- **`docs/SECURITY_AUDIT.md`** — Full security audit report covering: network call map,
  LangSmith SDK deep-dive and FERPA risk analysis, all findings with before/after code,
  accepted risks, and a FERPA compliance matrix.

---

## [0.1.0] — 2026-03-28

### Added

- `main.py` — FastAPI application entry point with root logger configuration
- `config.yaml` — Model name, Ollama base URL, chunk settings, and encrypted storage paths
- `pyproject.toml` / `requirements.txt` — Dependency declarations
- `.env.example` — Required environment variable reference for LangSmith tracing
- `routes/health.py` — `GET /health` liveness endpoint
- `routes/summarize.py` — `POST /summarize` file-upload endpoint; accepts PDF via
  multipart form or a `document_id` reference (document_id path returns HTTP 501 pending
  RAG service integration)
- `services/pdf_loader.py` — In-memory PDF text extraction and chunking via PyMuPDF
  (`fitz.open(stream=...)`) and LangChain `RecursiveCharacterTextSplitter`; no disk writes
- `services/summarizer.py` — LangChain Refine summarization chain using local
  `OllamaLLM`; initial prompt on first chunk, iterative refinement on subsequent chunks;
  INFO logging for chunk progress and LLM configuration
- `utils/cleanup.py` — Async `temp_file_context` context manager (guaranteed deletion
  on exit) and `cleanup_dir` utility for purging orphaned temp files
- `tests/test_health.py` — Health endpoint smoke test
- `README.md` — Service overview, setup instructions, and design rationale
