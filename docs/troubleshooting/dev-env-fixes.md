# Dev-Environment Fixes (May 3, 2026)

While bringing the live backend up for the Variation B frontend demo on a fresh Windows venv, three blocking issues surfaced that the existing pytest suite didn't catch (it uses `TestClient` and never exercises file-CWD or browser CORS paths). All three are fixed in code; this doc explains the change and the rationale so a future reviewer doesn't think the edits are accidental.

> **Audience:** anyone reviewing the May 3 changes, or running the stack from a fresh clone for the first time.
> **Status:** all three patches are live on `dev`. None alter production behavior — they make broken paths work.

---

## 1. `load_dotenv()` was reading the wrong directory

**Symptom:** Starting any of the four backend services from the project root (e.g., via `uvicorn main:app --app-dir backend/gateway`) crashed during import with `RuntimeError: GATEWAY_DB_PATH must be set in environment`. The `.env` file existed in `backend/gateway/` but `load_dotenv()` looked at the current working directory (the project root) and found nothing.

**Why it didn't show up before:** the existing dev workflow was `cd backend/gateway && uvicorn main:app`, which made CWD == service dir. The `--app-dir` invocation that's needed when running multiple services from one launch config (or VS Code, or `.claude/launch.json`) breaks that assumption.

**Fix — explicit path on every service entry point:**

```python
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
```

Applied to:
- [`backend/gateway/main.py`](../../backend/gateway/main.py)
- [`backend/rag/api.py`](../../backend/rag/api.py) (already had `load_dotenv()`, just made the path explicit)
- [`backend/summarizer/main.py`](../../backend/summarizer/main.py) (didn't call `load_dotenv` at all — `OLLAMA_BASE_URL` lookup was crashing on import)
- [`backend/jargon/main.py`](../../backend/jargon/main.py) (same — added `load_dotenv` and reordered imports so `LANGCHAIN_HIDE_*` env vars are still set before LangChain imports happen)

**Compatibility:** zero. Each service still finds the same `.env` it already used, regardless of CWD.

---

## 2. JWT middleware blocked CORS preflights

**Symptom:** Every browser-initiated POST/PUT/DELETE to a protected endpoint silently failed with `TypeError: Failed to fetch`. Gateway logs showed `OPTIONS /api/projects HTTP/1.1 401 Unauthorized` — the browser preflight never made it past auth.

**Why it didn't show up before:** the existing test suite uses Starlette's `TestClient`, which speaks WSGI directly and never issues CORS preflights. The flaw was invisible until a real browser tried to talk to the gateway.

**Why preflights need to pass through auth:** the browser sends an `OPTIONS` request without an `Authorization` header to negotiate cross-origin permissions before the real request. The browser only proceeds if the preflight succeeds — and a 401 is a failure. Standard CORS-aware backends always exempt `OPTIONS` from auth.

**Fix — short-circuit `OPTIONS` in the auth dispatch:**

```python
# backend/gateway/auth/middleware.py
async def dispatch(self, request: Request, call_next):
    # CORS preflight requests must pass through so the browser can
    # negotiate cross-origin headers before the real request is sent.
    if request.method == "OPTIONS":
        return await call_next(request)
    if request.url.path in EXEMPT_PATHS:
        return await call_next(request)
    # ... existing auth logic ...
```

**Security note:** this does NOT reduce auth coverage. A preflight `OPTIONS` request carries no body and has no privilege; the actual request that follows it (the GET/POST/etc.) still goes through `EXEMPT_PATHS` + token verification + RBAC + revocation check exactly as before. We're only letting the browser ask "may I send a real request?" without auth, which is what every CORS-aware service does.

**Test gap to close:** add a smoke test that issues `OPTIONS /api/projects` with `Origin: http://localhost:5173` and asserts a 200 with the right CORS headers. Punted for the demo — flag on the post-demo PR.

---

## 3. `student_id` was required despite being designed as optional

**Symptom:** Creating a project from the UI worked the first time (because the user entered a value in the optional `student_id` field), then on retry without that field returned `422 Field required: body.student_id`.

**Why it didn't show up before:** the existing pytest fixtures always supply a `student_id`, so the strict pydantic field passed every test. The contradiction surfaced only when a real user followed the UI label that says "Internal student ID (optional)".

**Why both the API and the DB had to change:**
- `CreateProjectRequest.student_id: str` was required at the API layer.
- `Project.student_id_hash` is `nullable=False` at the DB layer.

So just relaxing the API field would have moved the crash into the DB write. Two places to fix.

**Fix — relax the API and synthesize a random hash when omitted:**

```python
# backend/gateway/routes/projects.py
class CreateProjectRequest(BaseModel):
    student_id: str | None = None
    display_label: str | None = None

# In the handler:
raw_student_id = (body.student_id or "").strip() or f"anon-{uuid.uuid4()}"
h = hash_student_id(raw_student_id)
```

**Privacy note:** the synthesized `anon-<uuid>` is hashed with the same keyed BLAKE2b function as a real district ID, so it cannot be used for cross-referencing. Projects created without an external ID simply don't link to one — which matches the design intent of the optional field.

**Test gap to close:** add a pytest case for `POST /api/projects` with just `display_label` and assert 201. Punted for the demo.

---

## 4. `asyncio.run()` inside async FastAPI handlers

**Symptom:** Uploading a PDF (preview or commit) returned `500 Internal Server Error` with `RuntimeError: asyncio.run() cannot be called from a running event loop`.

**Why it didn't show up before:** `extract_pages()` in `backend/rag/ingestion.py` calls `asyncio.run(extract_pdf(...))` to invoke the async PDF extractor. That works fine when called from a sync context (CLI scripts, pytest), but the FastAPI route handler is already inside a running event loop, so `asyncio.run()` raises.

**Fix:** off-load the sync chain to a worker thread from the async handler — the new thread gets its own event loop.

```python
# backend/rag/api.py
import asyncio
result = await asyncio.to_thread(preview_pdf_bytes, file_bytes, file.filename)
```

Applied to both `/upload/preview` and `/upload` in [`backend/rag/api.py`](../../backend/rag/api.py).

---

## 5. `file: UploadFile = File(...)` rejected preview-token-only ingest

**Symptom:** `POST /api/rag/upload` with just `preview_token + project_id` returned `422 Field required: body.file`. The design says `file` and `preview_token` are mutually exclusive — you either upload fresh OR commit a previously previewed token.

**Where it bit us:** **two layers** had the bug:
1. [`backend/gateway/proxy/rag.py`](../../backend/gateway/proxy/rag.py) — gateway proxy required `file: UploadFile = File(...)`.
2. [`backend/rag/api.py`](../../backend/rag/api.py) — RAG service's own `/upload` route also required it.

`File(None)` with `UploadFile | None` did **not** make the field optional in this FastAPI version — multipart still rejected the request.

**Fix:** in both layers, drop the typed parameter and parse the form manually:

```python
@router.post("/upload")
async def upload_document(request: Request):
    form = await request.form()
    project_id = form.get("project_id")
    preview_token = form.get("preview_token")
    file = form.get("file")
    if not file and not preview_token:
        return JSONResponse(status_code=422, content={"detail": "Either 'file' or 'preview_token' must be provided."})
    # ... handle both paths
```

**Test gap to close:** the existing pytest suite always passes a `file`, so this branch was never exercised. Add a test that posts `preview_token + project_id` with no file and asserts 200. Punted for the demo.

---

## 6. Default Ollama model `mistral:7b` crashed the runner

**Symptom:** Any LLM call (jargon, summarize, RAG) returned `500: llama runner process has terminated` after ~25–45s. Ollama stayed up; only the model-load died.

**Likely cause:** memory pressure during `mistral:7b` load on this machine. The quantized `llama3.1:8b-instruct-q4_K_M` (~5GB) loads cleanly and produces good output for all three tools.

**Fix:** changed the dev `.env` for all three services to `OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M`. Updated [`scripts/setup_backend_dev_env.py`](../../scripts/setup_backend_dev_env.py) so future runs use the working model by default.

**Operator note:** the production deploy still uses whichever model the school operator chose (per the README's tech-stack table). This is a dev-only default. If `mistral:7b` works on the school server (more RAM), it remains the official choice.

---

## 7. Summarizer rejected gateway-forwarded text as "unsupported file type"

**Symptom:** Mode B summarize (pick an existing document) returned `422 Only PDF files are supported.` even though the user picked a real PDF.

**Why:** the gateway proxy's Mode B path **fetches the document text from RAG** (which already extracted it during ingest) and forwards it to the summarizer service as `text/plain` with a `.txt` filename — sensible, since the text is already extracted. But the summarizer's `/summarize` route was hard-coded to require `application/pdf` + `.pdf` filename, so it rejected its own gateway's payload.

**Fix:** [`backend/summarizer/routes/summarize.py`](../../backend/summarizer/routes/summarize.py) now accepts both:
- PDF input → goes through `load_pdf_from_bytes()` (vision fallback via Ollama).
- `text/plain` input → decoded as UTF-8 and chunked directly with `RecursiveCharacterTextSplitter`. No PDF re-parse needed.

This also makes the service interface honest: it summarizes **documents**, not specifically PDFs. Mode A and Mode B now both pass.

---

## 8. SQLAlchemy "transaction already begun" on run-history persistence

**Symptom:** Mode B summarize and any project-scoped jargon call succeeded at the LLM layer (200 from the downstream service), but the gateway then 500'd while trying to persist the run to history. Frontend showed a generic `Failed to fetch`. Logs: `sqlalchemy.exc.InvalidRequestError: A transaction is already begun on this Session.`

**Why:** [`backend/gateway/proxy/summarizer.py`](../../backend/gateway/proxy/summarizer.py) and [`backend/gateway/proxy/jargon.py`](../../backend/gateway/proxy/jargon.py) both opened a session, ran a `SELECT` (which auto-begins a transaction in SQLAlchemy 2.x), then called `session.begin()` to wrap the `INSERT` — and the explicit begin clashed with the auto-begun transaction.

**Fix:** in both proxies, restructure the block so the read and the write share a single transaction:

```python
async with AsyncSessionLocal() as session:
    async with session.begin():
        project = await crud.get_project_by_id(session, project_id, user_id)
        if project:
            await crud.log_summary_run(...)  # or log_jargon_run(...)
```

This matches the pattern already used in `proxy/rag.py`, which is why RAG persistence wasn't affected. Both proxies needed the same surgical fix.

---

## 9. Gateway httpx timeout too short for live LLM calls

**Symptom:** Mode A or Mode B summarize against a real PDF returned `500 Internal Server Error` after a few seconds with `httpx.ReadTimeout` in the gateway logs, even though the summarizer service was still working.

**Why:** the shared httpx `AsyncClient` was instantiated with `timeout=60.0`. A real summarize takes 30–90s; the gateway hung up well before the downstream service could respond.

**Fix:** [`backend/gateway/proxy/client.py`](../../backend/gateway/proxy/client.py) — granular timeouts via `httpx.Timeout`:

```python
shared_client = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=10.0, read=300.0, write=60.0, pool=10.0)
)
```

`read=300.0` accommodates cold-loaded models plus long summarize/RAG calls. Connect/pool stay short so a wedged downstream service still fails fast.

---

## 10. Summarizer over-chunked real PDFs into ~5,000 chunks

**Symptom:** The summarize-from-existing-document path (Mode B) on a real evaluation PDF produced **4,784 chunks**, each driving one LLM call in the refine pipeline. At ~1s per call that's ~80 minutes per summary — clearly broken for a sub-90s sync demo.

**Why:** when the gateway forwards already-extracted text (Mode B), the summarizer's text-input branch chunked at `chunk_size=2000` and didn't cap input length. A long IEP/eval bundle (~10MB of OCR'd text) became thousands of small chunks.

**Fix:** [`backend/summarizer/routes/summarize.py`](../../backend/summarizer/routes/summarize.py) — for the text-input path:
- Cap input at `_MAX_TEXT_CHARS = 60_000` chars (≈25 dense pages — the structured summary leans on referral / scores / diagnoses sections at the front anyway).
- Bumped `chunk_size` from 2000 → 8000, `chunk_overlap` 200 → 400.

Result: ~10 chunks × ~5s each, well under a minute end-to-end.

**Operator note:** the cap is dev-only. On the school server with more RAM and a faster GPU, raise `_MAX_TEXT_CHARS` (or remove it) and lower `chunk_size` again to get richer per-document summaries.

---

## 11. `dev_data/` and `SECUREPSYCH_ENV=test`

**Not a bug, but a setup convention worth documenting.**

The RAG service refuses to start in production unless `CHROMA_PATH` points under `/mnt/securepsych/` — the LUKS-encrypted mount. That guard is intentional and FERPA-required.

For local dev on a Windows laptop, that path doesn't exist. The escape hatch is `SECUREPSYCH_ENV=test`, which the codebase already supports.

[`scripts/setup_backend_dev_env.py`](../../scripts/setup_backend_dev_env.py) wires this up: it generates `.env` files for all four services with random secrets, sets `SECUREPSYCH_ENV=test`, and points data paths at a project-local `dev_data/` directory (gitignored).

**Important:** never copy a dev `.env` to the school server. The production deploy generates secrets out-of-band and uses the LUKS-mount paths.

---

## Verifying the fixes locally

```bash
# 1. Start the gateway via the launch config
# (or: backend\.venv\Scripts\python -m uvicorn main:app --reload --port 8000 --app-dir backend/gateway)

# 2. From the running frontend at localhost:5173, in DevTools console:
fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'dr.lee', password: 'demo-pass-2026' }),
}).then(r => r.json()).then(console.log)
```

Expected: a JSON response with `access_token` (200). If you get a CORS error or a 401 on the preflight, fix #2 didn't take effect — check `backend/gateway/auth/middleware.py:25`.
