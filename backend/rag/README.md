# RAG Service

Handles PDF ingestion, semantic chunk retrieval, and LLM-powered Q&A using ChromaDB and a local Ollama model; runs on port 8001.

## What it does
Accepts psychoeducational evaluation PDFs and ingests them into a local ChromaDB vector store using two chunking strategies — a sliding token window (standard) or page-boundary chunks (deep). Answers natural-language questions by over-fetching candidates and reranking by semantic similarity (55%), keyword overlap (30%), and section-heading boosts (15%). Deep mode additionally expands matched chunks to full-page context. Zero outbound network calls; all LLM inference routes through local Ollama.

## How to run
```bash
pip install -r requirements.txt
python -m uvicorn api:app --reload --port 8001
```

Copy `.env.example` → `.env` and fill in your values. Never commit `.env`.


## What to know as a developer
- **Never call another service directly** — inter-service orchestration belongs to the gateway, not here.
- **Never commit `chroma/`** — it contains embeddings derived from student documents (FERPA). Listed in `.gitignore`.
- **Zero outbound network calls** — all LLM inference routes through local Ollama. Never add an external API call without Natoli's approval.
- **Never commit real student PDFs, IEPs, or `.env`** — use synthetic documents for testing only.
- All disk writes for student data must target the LUKS/fscrypt-encrypted path defined in the shared architecture.
- Spec: `docs/checklist/RAG_POC_Checklist_1.pdf`
