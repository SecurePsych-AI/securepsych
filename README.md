# securepsych

**SecurePsych AI — Main Development Repository**

Locally-hosted, FERPA-compliant AI assistant for school psychologists and special education teams. All code lives here: backend microservices, frontend, infrastructure configuration, and documentation.

Student data never leaves the building. This repository never contains student data.

---

## Project Status

| Phase | Name                                  | Dates           | Status       |
| ----- | ------------------------------------- | --------------- | ------------ |
| 0     | Research Sprint                       | Feb 24 – Mar 5  | **Complete** |
| 1     | Infrastructure & Scaffold             | Mar 6 – Mar 10  | **Complete** |
| 2     | Core RAG + Summarization              | Mar 11 – Mar 28 | **Complete** |
| 3     | Jargon Simplifier                     | Mar 29 – Apr 11 | **Complete** |
| 4     | API Gateway & Auth                    | Apr 12 – Apr 25 | **Complete** |
| 5     | Security Audit, Documentation Update  | Apr 26 – May 2  | **Complete** |
| 6     | Frontend (Variation B) + Demo Prep    | May 1 – May 4   | **MVP done** |

**Active workstream:** Stakeholder demo (May 4). Frontend MVP runs against MSW mocks by default; live-backend mode is verified for auth + project CRUD.

---

## Repository Structure

```
securepsych/
├── backend/
│   ├── gateway/          ← API gateway — single entry point, port 8000
│   ├── rag/              ← RAG Q&A service (ChromaDB + LLM)
│   ├── summarizer/       ← Document summarization service
│   └── jargon/           ← Jargon simplification service (Phase 3)
├── frontend/             ← React + Vite + TailwindCSS (includes Data Visualization + Task Manager components)
├── infra/
│   ├── docker-compose.yml
│   ├── .woodpecker.yml   ← CI/CD pipeline (Woodpecker CI)
│   └── systemd/          ← Service unit files for FastAPI + Ollama
├── docs/
│   ├── api/              ← API endpoint reference
│   ├── checklist/        ← Service/feature POC checklist before demo
│   ├── troubleshooting/  ← Common issues and fixes
│   └── jumpstart/        ← Onboarding guide for new contributors
├── .env.example          ← Copy to .env — never commit your .env
├── .gitignore
├── CONTRIBUTING.md
└── README.md             ← You are here
```

---

## Architecture Overview

Three independent Python/FastAPI AI services run on separate ports behind a single API gateway. The frontend only ever talks to the gateway — never to individual services directly. Data Visualization and Task Manager are React components in the frontend (no backend service required).

```
Browser / Frontend (React + Vite)
  │  [Data Visualization + Task Manager live here as React components]
  │
  ▼
API Gateway :8000
  │
  ├── RAG Q&A :8001 ──── ChromaDB (shared vector store)
  ├── Summarizer :8002
  └── Jargon Simplifier :8003

All services run on a single physical machine on the school LAN.
No service communicates with the internet during normal operation.
LangSmith tracing: metadata only (token counts, latency). No document content transmitted.
```

---

## Technology Stack

| Layer              | Tool                                                  | Status                              |
| ------------------ | ----------------------------------------------------- | ----------------------------------- |
| LLM Runtime        | Ollama (on-prem)                                      | Confirmed                           |
| Base Model         | Operator-selected (mistral:7b / llama3 benchmarked)   | Confirmed                           |
| AI Framework       | LangChain (LangGraph for RAG pipeline)                | Confirmed                           |
| Vector Store       | ChromaDB (local, embedded)                            | Confirmed                           |
| Indexing Strategy  | Hierarchical chunk + MMR retrieval (ChromaDB)         | Confirmed                           |
| PDF Processing     | PyMuPDF (`fitz`)                                      | Confirmed                           |
| Backend API        | FastAPI (Python) — 3 microservices + API gateway      | Confirmed — feature-complete        |
| Frontend           | React + Vite + TailwindCSS                            | Confirmed — integration in progress |
| Auth               | Local JWT (`python-jose`) — no external auth provider | Confirmed                           |
| Monitoring         | LangSmith (metadata-only tracing, dev only)           | Confirmed                           |
| CI/CD              | Gitea + Woodpecker CI (self-hosted)                   | Confirmed                           |
| OS                 | Ubuntu Server 24.04 LTS                               | Confirmed                           |
| Storage Encryption | LUKS/fscrypt at OS level                              | Confirmed                           |

> **Backend status (May 2026):** All three microservices (RAG, Summarizer, Jargon) are feature-complete. The API gateway ships JWT auth, RBAC, per-user ownership, access logging, and student data isolation. The FERPA compliance checklist is current — 34 of 39 items complete, 5 remaining TODOs are infrastructure-level (TLS cert deployment, log rotation cron). Frontend integration is the active workstream.

---

## Getting Started (local dev)

**Prerequisites:**

- Python 3.11+ (Python 3.13 verified), Node.js 20+
- Ollama (optional — only needed for live LLM responses; the demo path uses MSW mocks)

**One-time setup:**

```bash
# 1. Backend venv + install all 4 service requirements
py -3.13 -m venv backend\.venv
backend\.venv\Scripts\python -m pip install --upgrade pip
backend\.venv\Scripts\python -m pip install -r backend\gateway\requirements.txt -r backend\rag\requirements.txt -r backend\summarizer\requirements.txt -r backend\jargon\requirements.txt -r backend\requirements-dev.txt

# 2. Generate dev .env files for the 4 backend services (random secrets, SECUREPSYCH_ENV=test)
py -3.13 scripts\setup_backend_dev_env.py

# 3. Frontend deps + auto-install of the MSW service worker
cd frontend
npm install
```

**Run the stack:** see [`.claude/launch.json`](.claude/launch.json) for the canonical dev-server configs (gateway 8000, rag 8001, summarizer 8002, jargon 8003, frontend 5173). Detailed walkthrough — including the MSW mock toggle and the demo script — lives in [`docs/jumpstart/FRONTEND_DEV.md`](docs/jumpstart/FRONTEND_DEV.md).

**Demo creds (dev only):** `dr.lee` / `demo-pass-2026` (overridable in `backend/gateway/.env`).

**Live-backend troubleshooting:** if you re-clone or change Python paths, see [`docs/troubleshooting/dev-env-fixes.md`](docs/troubleshooting/dev-env-fixes.md) for the three patches that make the services run from a fresh venv on Windows.

---

## Teams

| Team                        | Focus                                                     | Members                |
| --------------------------- | --------------------------------------------------------- | ---------------------- |
| Retrieval Engineering (RAG) | Document retrieval and context pipeline                   | Arham, Noble, Mohammed |
| Summarization               | Document and report summarization workflows               | Arpita                 |
| Product Design (UI/UX)      | Frontend usability, interface design, and experience flow | Alyse, Zach           |
| Compliance & FERPA          | Policy alignment and compliance safeguards                | Jon                    |

---

## FERPA Notice — Mandatory Read

This system is designed for FERPA-regulated student data. Every contributor must understand and follow these rules:

- **Never commit student data.** No PDFs, no test scores, no IEPs, no names. Not even as a test file.
- **Never commit `.env` or any file containing credentials.**
- **Never add a network call to an external service** without Natoli's explicit approval. Every external call is a potential FERPA violation.
- The ChromaDB `chroma/` directory is in `.gitignore` because it contains document embeddings derived from student files. Do not remove that entry.
- The LangSmith integration is configured for **metadata only**. It must never be reconfigured to log prompt content. If you're unsure whether a change affects this, ask before merging.

FERPA compliance research and the full compliance memo are in the `research-tracker` repo under `/research/`.

---

## Contributing

Read [`COLLABORATION.md`](./COLLABORATION.md) before opening your first PR.

All PRs require Natoli's review and approval. No direct commits to `main` or `dev`.

---

## Key Contacts

| Question                            | Contact                   |
| ----------------------------------- | ------------------------- |
| Architecture, scope, tech decisions | Natoli (EL)               |
| Deadlines, meetings, process        | Kai (PM)                  |
| School psych domain questions       | Dr. Josh Johnson          |
| FERPA / compliance questions        | Jon T. → Dr. Josh Johnson |

---
