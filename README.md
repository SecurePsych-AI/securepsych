# securepsych

**SecurePsych AI — Main Development Repository**

Locally-hosted, FERPA-compliant AI assistant for school psychologists and special education teams. All code lives here: backend microservices, frontend, infrastructure configuration, and documentation.

Student data never leaves the building. This repository never contains student data.

---

## Project Status

| Phase | Name                                   | Dates           | Status          |
| ----- | -------------------------------------- | --------------- | --------------- |
| 0     | Research Sprint                        | Feb 24 – Mar 5  | **Complete**    |
| 1     | Infrastructure & Scaffold              | Mar 6 – Mar 10  | **ON-HOLD**     |
| 2     | Core RAG + Summarization               | Mar 11 – Mar 28 | **IN PROGRESS** |
| 3     | Jargon Simplifier + Data Visualization | Mar 29 – Apr 11 | Not started     |
| 4     | Evaluation Task Manager                | Apr 12 – May    | Future scope    |

**First external milestone:** April 2026 stakeholder demo.

---

## Repository Structure

```
securepsych/
├── backend/
│   ├── gateway/          ← API gateway — single entry point, port 8000
│   ├── rag/              ← RAG Q&A service (ChromaDB + LLM)
│   ├── summarizer/       ← Document summarization service
│   ├── jargon/           ← Jargon simplification service (Phase 3)
│   ├── visualizer/       ← Assessment data visualization service (Phase 3)
│   └── task_manager/     ← Evaluation task manager (Phase 4)
├── frontend/             ← React + Vite + TailwindCSS
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

Five independent Python/FastAPI services run on separate ports behind a single API gateway. The frontend only ever talks to the gateway — never to individual services directly.

```
Browser / Frontend (React + Vite)
        │
        ▼
   API Gateway :8000 / Task Manager
        │
   ┌────┴────────────────────────────────┐
   │                                     │
RAG Q&A     Summarizer    Jargon    Visualizer
   │              │
   └──── ChromaDB (shared vector store) ────┘

All services run on a single physical machine on the school LAN.
No service communicates with the internet during normal operation.
LangSmith tracing: metadata only (token counts, latency). No document content transmitted.
```

---

## Technology Stack

| Layer              | Tool                                                  | Status                   |
| ------------------ | ----------------------------------------------------- | ------------------------ |
| LLM Runtime        | Ollama (on-prem)                                      | Confirmed                |
| Base Model         | TBD — benchmark in Phase 1                            | Pending                  |
| AI Framework       | LangChain or LlamaIndex                               | Pending (Research 7)     |
| Vector Store       | ChromaDB (local, embedded)                            | Confirmed                |
| Indexing Strategy  | TBD                                                   | Pending (Research 1 & 2) |
| PDF Processing     | PyMuPDF (`fitz`)                                      | Confirmed                |
| Backend API        | FastAPI (Python)                                      | Confirmed                |
| Frontend           | React + Vite + TailwindCSS                            | Confirmed                |
| Auth               | Local JWT (`python-jose`) — no external auth provider | Confirmed                |
| Monitoring         | LangSmith (metadata-only tracing)                     | Confirmed                |
| CI/CD              | Gitea + Woodpecker CI (self-hosted)                   | Confirmed                |
| OS                 | Ubuntu Server 24.04 LTS                               | Confirmed                |
| Storage Encryption | LUKS/fscrypt at OS level                              | Confirmed                |

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
| Product Design (UI/UX)      | Frontend usability, interface design, and experience flow | Alysze, Zach           |
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
