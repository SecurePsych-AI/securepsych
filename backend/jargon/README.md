# Jargon Simplifier Service

Simplifies clinical jargon in psychoeducational evaluation text to one of five reading levels; runs on port 8003.

## What it does
Accepts raw text or a PDF upload, processes it through a local Ollama model via LangChain, and returns simplified text alongside a Flesch-Kincaid reading grade metric. Supports five reading levels (1–5), allowing output to be tailored for different audiences (parents, students, administrators). Stateless — no student data is retained between requests.

## How to run
```bash
pip install -r requirements.txt   # or: poetry install
uvicorn main:app --host 0.0.0.0 --port 8003
```

Copy `.env.example` → `.env` and fill in deployment-specific values; never commit `.env`.

## What to know as a developer
- **Never call another service directly** — the gateway routes `/api/jargon/simplify` here; this service does not contact RAG, Summarizer, or any other microservice.
- **`LANGCHAIN_HIDE_INPUTS/OUTPUTS=true` is code-enforced** in `main.py` before any LangChain import. Do not move these to `.env` — they prevent document content from being captured by LangSmith telemetry.
- **PDF uploads are capped at 50 MB** — enforced in the route handler (`routes/simplify.py`).
- **Never commit real student data** — use synthetic text for testing only.
- Gateway routing config: `backend/gateway/config.yaml`
