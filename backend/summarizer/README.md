# Summarizer Service

Accepts a psychoeducational evaluation PDF and returns a structured summary of diagnoses, test scores, accommodations, and timeline information; runs on port 8002.

## What it does
Uses LangChain's Refine chain to process long reports (40–60 pages) sequentially, carrying a running summary forward so cross-page relationships are preserved (e.g., a page-45 recommendation citing a page-12 score). Stateless — one document in, one summary out; no session state between requests. Intermediate files are written to a LUKS-encrypted path and explicitly deleted after each request.

## How to run
```bash
pip install -r requirements.txt   # or: poetry install
uvicorn main:app --reload --port 8002
```

Configuration lives in `config.yaml`. Copy `.env.example` → `.env` and fill in your values; never commit `.env`.


## What to know as a developer
- **Never call RAG or any other service directly** — the gateway fetches document bytes from RAG and forwards them here; this service never contacts RAG itself.
- **`LANGCHAIN_HIDE_INPUTS/OUTPUTS=true` is code-enforced** in `main.py` before any LangChain import. Do not move these to `.env` — doing so risks transmitting document content to LangSmith externally, which is a FERPA violation.
- **Temp files fail closed** — if the encrypted mount at `encrypted_storage_path` is unavailable, the service raises `FileNotFoundError` rather than silently falling back to `/tmp`.
- **Never commit real student PDFs or `.env`** — use synthetic documents for testing only.
- Spec: `docs/checklist/Summarization_POC_Checklist.pdf`
