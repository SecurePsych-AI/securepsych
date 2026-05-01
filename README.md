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

**Active workstream:** Frontend integration and stakeholder demo prep.

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

## Getting Started (Phase 1+)

> Full setup guide will be in `/docs/jumpstart/` once Phase 1 infrastructure is live.

**Prerequisites:**

- Access to the team's on-prem server (LAN only — get the static IP from Kai or Arpita)
- Python 3.11+, Node.js 20+, Docker
- Ollama installed and model pulled (see `/docs/jumpstart/`)

**Environment setup:**

```bash
# Clone the repo
git clone https://github.com/securepsych-ai/securepsych.git
cd securepsych

# Copy environment template
cp .env.example .env
# Fill in values — ask Natoli or Arpita for local server config

# Backend (from /backend/rag, or any service)
poetry install
uvicorn main:app --reload --port 8001

# Frontend
cd frontend
npm install
npm run dev
```

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
