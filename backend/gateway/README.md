# API Gateway

Single entry point for all frontend requests; authenticates users via local JWT and proxies to backend microservices on ports 8001–8003; runs on port 8000.

## What it does
Issues and validates JWTs (`python-jose`) with role-based access control — only `psychologist` and `admin` roles are permitted. Proxies authenticated requests to RAG (8001), Summarizer (8002), and Jargon (8003). Enforces at startup that every configured upstream URL resolves to `localhost` — any non-local URL raises a `RuntimeError` and prevents the process from starting, which is the primary FERPA network boundary control.

## How to run
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Copy `.env.example` → `.env` and fill in your credentials; never commit `.env`.


## What to know as a developer
- **All upstream service URLs must point to `localhost`** — enforced in `config.py` at startup. This is non-negotiable; it is the FERPA network boundary.
- **Never bypass JWT auth** — `/health`, `/api/config`, and `/api/auth/login` are the only unauthenticated endpoints.
- **No OAuth or external identity providers** — authentication must remain local JWT only (`python-jose`).
- **Orchestration here, never service-to-service** — the gateway may fetch content from RAG and forward it to Summarizer; microservices must never call each other directly.
- Routing config: `backend/gateway/config.yaml`; jargon proxy: `backend/gateway/proxy/jargon.py`
