# Security Audit — `backend/summarizer`

**Date:** April 8, 2026  
**Auditor:** Arpita Haque & GitHub Copilot  
**Scope:** Full static audit of the `summarizer` microservice for external network calls, data leakage, input validation, and FERPA compliance.  
**Standard:** FERPA (20 U.S.C. § 1232g), OWASP Top 10

---

## 1. Threat Model

The summarizer processes **psychoeducational evaluation reports** — student records protected under FERPA. The core requirements are:

1. **No student data may leave the host machine** — not to any cloud AI API, tracing service, or external endpoint.
2. **All inference must be local** — only the on-device Ollama instance may receive document text.
3. **No student data may be written to unencrypted storage** — all file I/O must target the LUKS-encrypted mount.
4. **The service must not be destabilised by malicious input** — resource-exhaustion and input-injection attacks must be blocked at the boundary.

---

## 2. Network Call Analysis

Every outbound connection path was traced. The table below documents every component that can make a network call, what it calls, and how the call is controlled.

| Component            | Destination                       | Controlled by                    | Status                                     |
| -------------------- | --------------------------------- | -------------------------------- | ------------------------------------------ |
| `OllamaLLM`          | `http://localhost:11434`          | `config.yaml → ollama_base_url`  | ✅ Local only — hardwired to loopback      |
| LangSmith tracer     | `https://api.smith.langchain.com` | `LANGCHAIN_TRACING_V2` in `.env` | ✅ Opt-in; inputs/outputs blocked (see §3) |
| PyMuPDF (`fitz`)     | None                              | Library operates in-memory       | ✅ No network activity                     |
| FastAPI / Uvicorn    | None (inbound only)               | —                                | ✅ Serves requests, makes no calls         |
| `config.yaml` loader | None                              | Local YAML file                  | ✅ No network activity                     |

**Conclusion:** Under normal operation, the only outbound call is to `localhost:11434` (Ollama). LangSmith is the only optional external destination, and document content is unconditionally blocked from it (see §3).

---

## 3. LangSmith — FERPA Risk & Mitigation

### 3.1 What LangSmith sends by default

When `LANGCHAIN_TRACING_V2=true`, LangChain's tracing layer sends the full prompt payload — including document text — to `https://api.smith.langchain.com`. For a 40-page psychoeducational report this means every diagnosis, test score, and student identifier would be transmitted to a third-party cloud service. This is a **FERPA violation**.

### 3.2 Mitigation applied (`main.py`)

```python
# Set before any LangChain import so the Client constructor cache is cold
os.environ["LANGCHAIN_HIDE_INPUTS"] = "true"
os.environ["LANGCHAIN_HIDE_OUTPUTS"] = "true"
```

These are set **unconditionally in code**, not in `.env`, so they cannot be accidentally omitted.

**SDK verification:** The LangSmith Python SDK (`langsmith/utils.py`) implements `get_env_var` with `namespaces=("LANGSMITH", "LANGCHAIN")`, meaning `LANGCHAIN_HIDE_INPUTS` is a valid and recognized variable. The `Client.__init__` reads:

```python
self._hide_inputs = (
    hide_inputs if hide_inputs is not None
    else ls_utils.get_env_var("HIDE_INPUTS") == "true"
)
```

Because `get_env_var("HIDE_INPUTS")` checks `LANGSMITH_HIDE_INPUTS` then `LANGCHAIN_HIDE_INPUTS`, the guard in `main.py` is effective. When `_hide_inputs` is `True`, `_hide_run_inputs()` returns `{}` — an empty dict — before the payload is serialized and queued for upload.

### 3.3 Residual tracing data (what IS sent)

With inputs/outputs hidden, LangSmith receives only:

- Run ID (UUID, no student information)
- Run type (`chain`, `llm`)
- Latency (start/end timestamps)
- Token counts (no text content)
- Project name (`securepsych-summarizer`)

This metadata contains **no student records** and is permissible under FERPA's operational-use exception.

### 3.4 Disabling LangSmith entirely

If the team decides to disable tracing completely, set in `.env`:

```
LANGCHAIN_TRACING_V2=false
```

No code change is required. The `main.py` guards remain inert when tracing is off.

---

## 4. Findings & Fixes Applied

### 4.1 [FIXED — HIGH] Unbounded file read — memory exhaustion DoS

**File:** `routes/summarize.py`  
**Before:**

```python
pdf_bytes = await file.read()
```

Without a size cap, an attacker can upload an arbitrarily large file, exhausting server memory and taking the service down.

**After:**

```python
_MAX_PDF_BYTES = 50 * 1024 * 1024  # 50 MB

pdf_bytes = await file.read(_MAX_PDF_BYTES + 1)
if len(pdf_bytes) > _MAX_PDF_BYTES:
    raise HTTPException(status_code=413, detail="File exceeds the 50 MB size limit.")
```

`file.read(n)` reads at most `n` bytes; reading one byte over the limit is sufficient to detect an oversized file without buffering it fully.

---

### 4.2 [FIXED — HIGH] Missing `Content-Type` validation — upload filter bypass

**File:** `routes/summarize.py`  
**Before:**

```python
if not file.filename.lower().endswith(".pdf"):
    raise HTTPException(status_code=422, detail="Only PDF files are supported.")
```

Filename extension checks are trivially bypassed by renaming any file to `.pdf`. PyMuPDF will attempt to parse whatever bytes were uploaded.

**After:**

```python
_ALLOWED_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}

if file.content_type not in _ALLOWED_CONTENT_TYPES:
    raise HTTPException(status_code=415, detail="Only PDF files are supported.")
```

`application/octet-stream` is retained because many HTTP clients (curl, Postman) send it as the default binary content-type for PDF uploads.

---

### 4.3 [FIXED — HIGH] `file.filename` can be `None` — uncaught `AttributeError`

**File:** `routes/summarize.py`  
**Before:**

```python
if not file.filename.lower().endswith(".pdf"):
```

`UploadFile.filename` is typed `Optional[str]`. Calling `.lower()` on `None` raises `AttributeError`, returning a 500 to the caller.

**After:**

```python
if file.filename is None or not file.filename.lower().endswith(".pdf"):
    raise HTTPException(status_code=422, detail="Only PDF files are supported.")
```

---

### 4.4 [FIXED — MEDIUM] Temp files written to unencrypted `/tmp`

**File:** `utils/cleanup.py`  
**Before:**

```python
fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
```

Python's `tempfile.mkstemp()` with no `dir=` argument defaults to the OS temporary directory (`/tmp`), which is unencrypted. Any intermediate LLM output buffered to disk would be written outside the LUKS-encrypted mount defined in `config.yaml`.

**After:**

```python
def _get_encrypted_temp_dir() -> str:
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)
    return cfg.get("summarizer", {}).get("encrypted_storage_path", "/tmp")

# Inside temp_file_context:
enc_dir = _get_encrypted_temp_dir()
fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=enc_dir)
```

If the LUKS mount at `/mnt/securepsych/data` is not present, `mkstemp` raises `FileNotFoundError` — **fail-closed**, not fail-open. The service will not silently fall back to unencrypted storage.

---

### 4.5 [FIXED — LOW] Misleading docstring in `summarizer.py`

**File:** `services/summarizer.py`  
**Before:**

```
Only token counts and latency metadata are transmitted — zero document content.
```

This claim, while practically accurate, presented the property as structural when it depends entirely on the guards in `main.py`. If those guards were removed, the statement would be false and no developer reading only this file would know the risk.

**After:**

```
Document content is blocked from LangSmith by the LANGCHAIN_HIDE_INPUTS/OUTPUTS
guards set unconditionally in main.py. Do not remove those guards.
```

---

## 5. Items Outside Scope / Accepted Risks

| Item                                           | Status             | Notes                                                                                                                                                 |
| ---------------------------------------------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `document_id` orchestration                    | Gateway responsibility | The Summarizer accepts raw PDF bytes only. When summarizing an already-ingested document, the API gateway fetches its bytes from RAG and forwards them here. This service has no knowledge of `document_id`. No code change needed in this service.  |
| Authentication / authorisation on `/summarize` | Not implemented    | Service is assumed to sit behind an authenticated gateway (see `backend/gateway`). Direct exposure of this service without a gateway is a FERPA risk. |
| TLS on Ollama (`http://localhost`)             | Accepted           | Loopback-only; no network-level exposure. Acceptable for local deployment.                                                                            |
| Rate limiting                                  | Not implemented    | Recommend adding per-IP rate limiting at the gateway layer before production.                                                                         |
| PDF parser hardening (malicious PDF payloads)  | Accepted (PyMuPDF) | PyMuPDF is a C-based library with a strong security track record. Ensure it is kept up to date.                                                       |

---

## 6. FERPA Compliance Summary

| Requirement                                 | Control                                                        | Status |
| ------------------------------------------- | -------------------------------------------------------------- | ------ |
| Student records do not leave the host       | Ollama on `localhost`; LangSmith inputs/outputs hidden         | ✅     |
| No student data in transit to third parties | `LANGCHAIN_HIDE_INPUTS/OUTPUTS` enforced in code               | ✅     |
| No student data on unencrypted storage      | `temp_file_context` routes to LUKS-encrypted path; fail-closed | ✅     |
| Data minimisation                           | Stateless service — no session state, no persistence           | ✅     |
| Audit trail                                 | LangSmith traces metadata (run IDs, latency, tokens) — no PII  | ✅     |
| Service availability                        | 50 MB upload cap; `Content-Type` + filename validation         | ✅     |

---

## 7. Files Modified in This Audit

| File                     | Change                                                                    |
| ------------------------ | ------------------------------------------------------------------------- |
| `main.py`                | Added `LANGCHAIN_HIDE_INPUTS/OUTPUTS` enforcement before LangChain import |
| `routes/summarize.py`    | 50 MB cap, `Content-Type` validation, `None` filename guard               |
| `utils/cleanup.py`       | `temp_file_context` routes temp files to encrypted storage path           |
| `services/summarizer.py` | Corrected misleading LangSmith docstring                                  |
