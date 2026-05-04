# SecurePsych Frontend — Complete Context Pack

> **For:** Claude Design / any new design or implementation session.
> **Purpose:** Single source of truth describing what we're building, the constraints that shape it, the API surface it must speak to, and the visual language it must wear. Self-contained — does not depend on external files.
> **Audience:** A new collaborator who has zero prior context on the project.
> **Last updated:** 2026-05-01 — frontend kickoff.

---

## 1. The Project in One Paragraph

SecurePsych AI is a locally hosted, FERPA-compliant AI assistant for school psychologists and special-education teams. It runs on a single on-prem server inside the school LAN; no student data ever leaves the building. The backend (a FastAPI gateway fronting three local AI microservices — RAG Q&A, Document Summarizer, and Jargon Simplifier — all powered by on-prem Ollama) is feature-complete. The frontend folder is empty. We are building it from scratch in the next four days for a Monday stakeholder demo.

---

## 2. What We Are Building

A web application for a single user (a school psychologist) to:

1. **Manage student cases** as projects — never by name, always by case code. Each project owns its uploaded documents, conversation threads, and run history.
2. **Q&A documents (RAG)** — upload an evaluation PDF, ask questions, receive grounded answers with page-level citations.
3. **Summarize documents** — upload a long psychoeducational evaluation and receive a structured summary covering diagnoses, scores, accommodations, and dates.
4. **Simplify clinical jargon** — paste a paragraph (or upload a PDF) and receive a rewrite at one of five reading levels, from psychologist-to-psychologist down to elementary-age child.
5. **Review past activity** — every project carries a history of threads, summaries, and jargon runs.

Two additional surfaces — a Data Visualization view and a Task Manager — are mentioned in the project README as React-only components. **They are out of scope for the Monday demo.** Render them as "Coming soon" tiles or hide them behind feature flags.

### 2.1 The User

A school psychologist working on student case files. Reasonably tech-comfortable but not technical. Cares about saving time on report-reading, getting parent-friendly explanations of clinical findings, and absolutely cannot mishandle student data. Will not use this if the FERPA story is shaky.

### 2.2 The Demo Story (What the User Will See on Monday)

> "Dr. Lee opens SecurePsych on her laptop, signs in, and creates a new project — `Case 2026-014`. She uploads `eval_2024.pdf`. The system shows her a redaction-confirmation screen — a list of detected names and dates of birth that will be replaced with placeholders before storage. She confirms. The document is ingested. She switches to the Q&A tab and asks *'What cognitive assessments were administered and what were the composite scores?'* — the system answers with page-level citations she can click. She switches to the Summarizer tab on the same project and gets a structured summary. She copies a clinical paragraph into the Jargon Simplifier, picks Level 3 (parent-friendly), and gets a plain-language rewrite she can paste into a parent letter. The whole thing runs on the school's local server with no internet."

---

## 3. Tech Stack (Locked)

| Layer | Choice | Notes |
|------|--------|-------|
| Framework | **React 18 + Vite** | No SSR. Local LAN deployment. CORS default in gateway already targets `localhost:5173`. |
| Language | **TypeScript (strict)** | All API responses typed against the contract in §10. |
| Styling | **TailwindCSS** | Utility-first. No CSS-in-JS. |
| Components | **shadcn/ui** | Copy-paste primitives. Ownership lives in our repo. |
| Routing | **React Router v6** | File-based not needed; static route table is fine. |
| Server state | **TanStack Query (`@tanstack/react-query`)** | Fetching, caching, mutations, optimistic updates. |
| Client state | **Zustand** | Tiny store: auth token + selected project ID. |
| Forms | **react-hook-form + zod** | Client-side validation mirrors server-side PII checks. |
| Mocks | **MSW (Mock Service Worker)** | Toggle via `VITE_USE_MOCKS=true`. |
| Tests | **Vitest + React Testing Library** | Smoke test per tool. Run full suite before PR. |
| Icons | **lucide-react** | Already a shadcn dependency. |
| HTTP | Native `fetch` wrapped in a typed client | No axios. |

**Do not introduce additional dependencies without approval from Natoli (Engineering Lead).**

---

## 4. Architecture Overview

```
Browser (React + Vite, dev port 5173)
   │
   │  Authorization: Bearer <JWT>
   ▼
API Gateway :8000 ───────────────────────────────┐
   │  enforces JWT auth, RBAC, project ownership  │
   │  redacts PII before responses leave the box   │
   ▼                                              │
   ├── RAG Q&A          :8001  ─── ChromaDB       │
   ├── Summarizer       :8002                     │
   └── Jargon Simplifier:8003                     │
                                                  │
   No outbound network. LangSmith metadata-only.  │
   All persistence on a LUKS-encrypted volume.    │
                                                  ┘
```

The frontend speaks **only** to the gateway. Never call services on :8001 / :8002 / :8003 directly. The gateway is the single source of truth for auth, ownership, and PII redaction.

---

## 5. Information Architecture & Layout

We are following a **hybrid of two reference mockups**: the polished mockup's feature-card landing dashboard combined with the rough mockup's persistent left **project rail**.

```
┌───────────────────────────────────────────────────────────────────┐
│ TopBar:  [Logo SecurePsych AI]    [System Status: Operational]  ⚙ │
├──────────────┬────────────────────────────────────────────────────┤
│ ProjectRail  │ Workspace                                          │
│              │                                                    │
│ + New Project│  When no project selected:                         │
│              │    Welcome dashboard with three feature cards      │
│ ▼ Recent     │    (Q&A Assistant, Document Summarizer,            │
│   Case 2026- │     Jargon Simplifier) + Recent Activity           │
│   014        │                                                    │
│   Case 2026- │  When project selected:                            │
│   011        │    Project workspace with tabs:                    │
│   …          │      ▸ Overview (files, recent runs)               │
│  [Load more] │      ▸ Q&A (chat surface)                          │
│              │      ▸ Summarize                                   │
│ ▼ Threads    │      ▸ Jargon                                      │
│   in Case…   │      ▸ History                                     │
│              │                                                    │
│ — — —        │                                                    │
│ ⓘ FERPA-     │                                                    │
│   compliant  │                                                    │
│ ⓘ On-prem    │                                                    │
│ Logout       │                                                    │
└──────────────┴────────────────────────────────────────────────────┘
```

### 5.1 Routes

| Path | Page | Notes |
|------|------|-------|
| `/login` | Login form | Username/password → JWT. Redirect to `/` on success. |
| `/` | Dashboard | Welcome cards + recent activity. Visible after login if no project selected. |
| `/p/:projectId` | Project Overview | Files, recent threads, recent summaries, recent jargon runs. |
| `/p/:projectId/qa` | RAG Chat | Threaded conversation surface. |
| `/p/:projectId/qa/:threadId` | RAG Chat (existing thread) | Loads thread history. |
| `/p/:projectId/summarize` | Summarizer | Mode A (upload) or Mode B (existing doc). |
| `/p/:projectId/jargon` | Jargon Simplifier | Text input + level selector. |
| `/p/:projectId/history` | Full Activity Log | All threads, summaries, jargon runs. |
| `*` | NotFound | Bounce to `/`. |

### 5.2 Project Selection Is Mandatory

Almost every backend endpoint requires a `project_id`. The UI must not let a user enter the Q&A / Summarizer / Jargon surfaces without a selected project. The composer and upload buttons are disabled until a project is in context.

---

## 6. Visual Design Language — Light, ChatGPT-style

Calm, neutral, and document-friendly. The room a school psychologist works in: clean, focused, no chrome competing with the content.

### 6.1 Color Tokens

| Token | Value | Usage |
|------|-------|-------|
| `--bg-primary` | `#FFFFFF` | Main canvas, message bubbles. |
| `--bg-secondary` | `#F7F7F8` | Project rail, sidebars, subtle surfaces. |
| `--bg-tertiary` | `#ECECEC` | Hover states, code blocks, citation cards. |
| `--border` | `#E5E5E5` | Card and input borders. |
| `--border-strong` | `#D1D5DB` | Active focus, dividers between sections. |
| `--text-primary` | `#1F1F1F` | Body text. |
| `--text-secondary` | `#6E6E80` | Metadata, timestamps, captions. |
| `--text-muted` | `#9CA3AF` | Placeholder, disabled. |
| `--accent` | `#0F766E` | Teal — buttons, focus rings, key links. |
| `--accent-hover` | `#0D5F58` | Hover state for primary buttons. |
| `--accent-soft` | `#E6F4F1` | Tinted backgrounds for selected/active states. |
| `--danger` | `#B91C1C` | Destructive actions, errors. |
| `--success` | `#15803D` | Status pills (System Operational, FERPA OK). |
| `--warning` | `#B45309` | PII detected callouts. |

Tailwind config note: extend the default theme rather than overwriting it. Map `--accent` to a `teal` scale and use shadcn's `cn()` helper everywhere.

### 6.2 Typography

- **Font stack:** `ui-sans-serif, system-ui, -apple-system, "Segoe UI", "Helvetica Neue", Arial, sans-serif` — system fonts, no webfont download (this is on-prem LAN, no CDN).
- **Sizes:** Tailwind defaults. Body `text-sm` (14px), headings escalate; chat messages `text-base` (16px) for readability.
- **Line height:** `leading-relaxed` for any block of clinical text or AI output.
- **Monospace:** `ui-monospace, "SF Mono", Menlo, Consolas, monospace` for citations and inline code.

### 6.3 Component Style Principles

- **Borders over shadows.** A 1px `border-border` is the default elevation cue. Reserve subtle `shadow-sm` for floating elements (dialogs, popovers).
- **Generous whitespace.** Padding scales: `p-4` for tight cards, `p-6` for content panels, `p-8` for page-level wrappers.
- **Rounded corners.** `rounded-xl` (12px) for cards and message bubbles, `rounded-lg` for buttons and inputs, `rounded-full` for pills.
- **Focus rings.** Visible, accent-colored, 2px offset. Accessibility is non-negotiable.
- **Loading states are skeletons, not spinners.** Spinners only for sub-second waits or dialog confirmations.
- **Empty states are friendly.** Each empty list has an illustration-free, sentence-or-two prompt: "No projects yet. Create one to get started."

### 6.4 Iconography

`lucide-react`. Suggested mapping:

- `MessageSquare` — Q&A
- `FileText` — Summarizer
- `Languages` — Jargon Simplifier
- `Folder` — Projects
- `Upload` — File upload
- `Shield` — FERPA badge
- `Server` — On-prem badge
- `Wifi-off` — Air-gapped indicator
- `Clock` — History
- `LogOut` — Sign out
- `Plus` — New project / new thread

### 6.5 Trust Signals

The chrome should reassure the user this is safe. In the project rail footer, render three small pill-style indicators:

- ✓ FERPA-compliant
- ✓ On-prem only
- ✓ No internet

These appear on every page. They are part of the demo narrative.

---

## 7. FERPA UX Rules — Hard Requirements

These are not stylistic preferences. Each one ties to a specific item in the FERPA / RAG / Summarizer POC checklists.

1. **Never display or accept raw student names or IDs.**
   - Project labels are validated server-side against SSN, DOB, and 6+ digit district ID patterns. Mirror the validation client-side with helper text: *"Use a case code such as `Case 2024-031`. Do not include names, birthdates, or ID numbers."*
   - The `display_label` field is capped at 80 characters.

2. **`student_id` and `redaction_key` are stripped by the gateway.**
   - These fields must never appear in TypeScript types, React state, console logs, or error reports.
   - Our `Project` type has `id`, `display_label`, `created_at` — nothing else.

3. **The two-step PII redaction confirmation is its own screen.**
   - On document upload: call `POST /api/rag/upload/preview` first. The response includes an `entity_map` like `{"STUDENT_NAME_1": "Marcus Johnson", "DATE_OF_BIRTH_1": "01/15/2012"}`.
   - Render a confirmation panel showing each detected entity and what placeholder will replace it. The user clicks **Confirm and ingest** before we call `POST /api/rag/upload` with the `preview_token`.
   - This is a real screen, not a loading spinner.

4. **All filenames shown to the user are the redacted version (`*_REDACTED.pdf`).**
   - The original filename is never echoed back from the backend; never reconstruct it client-side.

5. **Citations are mandatory on every RAG answer.**
   - `sources: [{source, page, parent_id, document_id}]` accompanies every assistant message. Render each as a clickable footnote that scrolls/links to the source position. At minimum show "📄 `eval_2024_REDACTED.pdf` · page 12".

6. **A non-developer hard-delete flow is required by the FERPA checklist.**
   - For MVP: a Delete button on each document card, with a confirmation dialog that explains what will be removed. Wire it to `DELETE /api/rag/documents/{id}?project_id=...`.

7. **Trust badges visible on every page.** See §6.5.

---

## 8. Auth Model

**MVP scope: single user.** One `GATEWAY_USERNAME` / `GATEWAY_PASSWORD` is provisioned in the gateway's `.env`. The user logs in once per session.

- `POST /api/auth/login` returns `{access_token, token_type}`. Token type is `bearer`.
- Token lifetime is 8 hours (server config). After expiry, redirect to `/login` on the next 401.
- Token storage: **in-memory Zustand store + sessionStorage rehydration.** No `localStorage` (XSS risk). On hard refresh, rehydrate from sessionStorage; if expired, bounce to login.
- Logout: `POST /api/auth/logout` with the current token, clear the store, redirect.
- Every authed request injects `Authorization: Bearer ${token}` via the API client.
- Multi-user / role-aware UX (admin vs. psychologist) is **post-MVP**. The token does carry a `role` field — store it but don't switch UI on it yet.

### 8.1 Auth UX

- Login is a single centered card. Fields: Username, Password. Submit button. Error banner above for "Invalid credentials" (HTTP 401).
- No "remember me", no SSO, no password reset link in MVP.
- 401 anywhere in the app → toast "Your session has expired" → redirect to `/login`.

---

## 9. Pagination Convention

Backend will adopt a **Standard Pagination Schema** for all list endpoints, with a "Load more" pattern in the UI. Today the endpoints return bare arrays; tomorrow they will return `{items, total, page_size, has_more}` or similar.

**Build for tomorrow.** Wrap every list query in a `useInfinitePagination` hook that:
- Today: takes the array response, treats it as a single page.
- Tomorrow: paginates with `page` + `page_size` query params.

The "Load more" button at the bottom of any list is hidden when there's nothing more to load. Initial page size: 20.

---

## 10. Complete API Reference

> Base URL: `http://localhost:8000`. All authed endpoints require `Authorization: Bearer <token>`.

### 10.1 Auth

#### `POST /api/auth/login`
Body: `{ "username": "string", "password": "string" }`
Response 200: `{ "access_token": "eyJhbGci...", "token_type": "bearer" }`

#### `POST /api/auth/logout`
Body: `{ "token": "eyJhbGci..." }`
Response 200: `{ "status": "ok", "detail": "Token added to denylist" }`

### 10.2 Projects & History

#### `POST /api/projects`
Body: `{ "student_id": "district-id-98765", "display_label": "Case 2024-031" }`
Response 201: `{ "id": "uuid", "display_label": "Case 2024-031", "created_at": "ISO-8601" }`
Errors: 422 if `display_label` matches PII patterns; 401 if missing/invalid token.

> `student_id` is hashed server-side with a keyed BLAKE2b function. The raw value is never persisted and is never returned in responses. The frontend sends it once, never reads it back.

#### `GET /api/projects`
Response 200: array of project objects, newest first.

#### `GET /api/projects/{project_id}`
Response 200: project object. 404 if not found / not owned.

#### `GET /api/projects/{project_id}/files`
Response 200:
```json
[
  {
    "id": "uuid",
    "document_id": "uuid",
    "filename_redacted": "eval_2024_REDACTED.pdf",
    "strategy": "standard",
    "chunks_added": 187,
    "uploaded_at": "ISO-8601"
  }
]
```

#### `GET /api/projects/{project_id}/threads`
Response 200:
```json
[
  { "id": "uuid", "title": null, "created_at": "ISO-8601" }
]
```

#### `GET /api/projects/{project_id}/threads/{thread_id}`
Response 200:
```json
{
  "id": "uuid",
  "title": null,
  "created_at": "ISO-8601",
  "messages": [
    {
      "id": "uuid",
      "role": "user" | "assistant",
      "content": "string",
      "sources": [
        { "source": "filename", "page": 12, "parent_id": "12_2", "document_id": "uuid" }
      ],
      "created_at": "ISO-8601"
    }
  ]
}
```

#### `GET /api/projects/{project_id}/summaries`
Response 200:
```json
[
  {
    "id": "uuid",
    "document_id": "uuid",
    "filename_redacted": "eval_2024_REDACTED.pdf",
    "summary": "Psychoeducational Evaluation Summary...",
    "page_count": 24,
    "created_at": "ISO-8601"
  }
]
```

#### `GET /api/projects/{project_id}/jargon-runs`
Response 200:
```json
[
  {
    "id": "uuid",
    "level": 3,
    "input_preview": "First 200 chars only — full input never stored.",
    "simplified_text": "...",
    "fk_grade": 7.1,
    "created_at": "ISO-8601"
  }
]
```

### 10.3 RAG

#### `POST /api/rag/upload/preview`
multipart/form-data — `file` (PDF). Returns:
```json
{
  "preview_token": "uuid",
  "sample_text": "first ~500 chars",
  "entity_map": { "STUDENT_NAME_1": "Marcus Johnson", "DATE_OF_BIRTH_1": "01/15/2012" },
  "page_count": 24,
  "filename": "eval_2024.pdf"
}
```

#### `POST /api/rag/upload`
multipart/form-data — `file` OR `preview_token`, plus `project_id` (required), optional `strategy: "standard" | "deep"`.
Response 200:
```json
{
  "status": "ok",
  "document_id": "uuid",
  "source": "eval_2024_REDACTED.pdf",
  "strategy": "standard",
  "chunks_added": 187,
  "avg_chunk_tokens": 512
}
```

#### `POST /api/rag/query`
JSON:
```json
{
  "question": "What cognitive assessments were administered?",
  "project_id": "uuid",
  "document_id": "uuid",         // optional — scope to one doc
  "thread_id": "uuid",            // omit to start a new thread
  "mode": "fast",                 // "fast" (default) or "deep"
  "top_k": 3                      // default 3
}
```
Response 200:
```json
{
  "answer": "...",
  "mode": "fast",
  "top_k": 3,
  "thread_id": "uuid",
  "sources": [
    { "source": "eval_2024_REDACTED.pdf", "page": 12, "parent_id": "12_2", "document_id": "uuid" }
  ]
}
```

#### `GET /api/rag/documents?project_id=...`
```json
{
  "total_documents": 1,
  "documents": [{ "document_id": "uuid", "filename": "eval_2024_REDACTED.pdf" }]
}
```

#### `DELETE /api/rag/documents/{document_id}?project_id=...`
```json
{ "deleted": true, "document_id": "uuid", "filename": "eval_2024_REDACTED.pdf", "chunks_removed": 187 }
```

### 10.4 Summarizer

#### `POST /api/summarize`

**Mode A** — multipart/form-data: `file` (PDF ≤ 50 MB), optional `project_id`.

**Mode B** — application/json: `{ "document_id": "uuid", "project_id": "uuid" }`.

Response 200 (both modes):
```json
{
  "summary": "Psychoeducational Evaluation Summary\n\nDiagnoses: ...\nWISC-V FSIQ: 88 ...",
  "page_count": 24
}
```

> Synchronous only for MVP. Latency target is 90s for a 48-page doc. Show a skeleton or a friendly "Working on it…" panel — never a blocking modal.

### 10.5 Jargon Simplifier

#### `POST /api/jargon/simplify`

**JSON mode:**
```json
{ "text": "...", "level": 3, "project_id": "uuid" }
```

**Multipart mode:** `file` (PDF), optional `level` and `project_id`.

Response 200:
```json
{
  "simplified_text": "...",
  "flesch_kincaid_grade": 7.1,
  "level": 3
}
```

Levels:
| Level | Audience |
|-------|----------|
| 1 | Psychologist (clinical preserved) |
| 2 | Educator / coordinator |
| 3 | Parent / guardian (default) |
| 4 | High-school student |
| 5 | Elementary-age child |

### 10.6 System

#### `GET /health`
`{ "status": "ok", "service": "gateway" }`

#### `GET /api/config`
`{ "rag_enabled": true, "summarizer_enabled": true, "jargon_enabled": true }`

> **Use this on app load.** Hide tabs / cards for any disabled service.

---

## 11. Mock Payloads (verbatim, drop into `src/mocks/data/`)

### `history_mock.json`
```json
{
  "list_projects_response_200": [
    { "id": "a1b2c3d4-0001-0001-0001-000000000001", "display_label": "Case 2024-031", "created_at": "2024-09-03T14:22:07.123456+00:00" },
    { "id": "b2c3d4e5-0002-0002-0002-000000000002", "display_label": "Case 2024-018", "created_at": "2024-08-15T09:10:31.000000+00:00" }
  ],
  "list_files_response_200": [
    { "id": "c3d4e5f6-0003-0003-0003-000000000003", "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98", "filename_redacted": "eval_2024_REDACTED.pdf", "strategy": "standard", "chunks_added": 187, "uploaded_at": "2024-09-03T14:30:55.000000+00:00" }
  ],
  "list_threads_response_200": [
    { "id": "cc1d2e3f-4a5b-6c7d-8e9f-a0b1c2d3e4f5", "title": null, "created_at": "2024-09-03T14:45:00.000000+00:00" }
  ],
  "get_thread_response_200": {
    "id": "cc1d2e3f-4a5b-6c7d-8e9f-a0b1c2d3e4f5",
    "title": null,
    "created_at": "2024-09-03T14:45:00.000000+00:00",
    "messages": [
      { "id": "d1e2f3a4-b5c6-7d8e-9f0a-b1c2d3e4f5a6", "role": "user", "content": "What cognitive assessments were administered and what were the composite scores?", "sources": [], "created_at": "2024-09-03T14:45:00.000000+00:00" },
      { "id": "e2f3a4b5-c6d7-8e9f-0a1b-c2d3e4f5a6b7", "role": "assistant", "content": "The Wechsler Intelligence Scale for Children (WISC-V) was administered. The student obtained a Full Scale IQ (FSIQ) composite score of 88, placing performance in the Low Average range (25th percentile).", "sources": [{ "source": "eval_2024_REDACTED.pdf", "page": 12, "parent_id": "12_2", "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98" }], "created_at": "2024-09-03T14:45:03.000000+00:00" }
    ]
  },
  "list_summaries_response_200": [
    { "id": "f3a4b5c6-d7e8-9f0a-1b2c-d3e4f5a6b7c8", "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98", "filename_redacted": "eval_2024_REDACTED.pdf", "summary": "Psychoeducational Evaluation Summary\n\nStudent diagnosed with Specific Learning Disability in Reading (Dyslexia). WISC-V FSIQ: 88 (Low Average). WIAT-4 Word Reading: 74 (4th percentile). Recommendations include Orton-Gillingham instruction and extended time accommodations.", "page_count": 24, "created_at": "2024-09-03T15:02:11.000000+00:00" }
  ],
  "list_jargon_runs_response_200": [
    { "id": "a4b5c6d7-e8f9-0a1b-2c3d-e4f5a6b7c8d9", "level": 3, "input_preview": "The examinee demonstrated significant deficits in phonological processing as measured by the CTOPP-2, with a Phonological Memory Composite of 74 (4th percentil", "simplified_text": "The testing showed that your child has difficulty with the sound-based building blocks of reading...", "fk_grade": 7.1, "created_at": "2024-09-03T15:10:45.000000+00:00" }
  ]
}
```

### `rag_mock.json`
```json
{
  "upload_response_200": { "status": "ok", "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98", "source": "eval_2024_REDACTED.pdf", "strategy": "standard", "chunks_added": 187, "avg_chunk_tokens": 512 },
  "query_response_200": {
    "answer": "The Wechsler Intelligence Scale for Children (WISC-V) was administered. The student obtained a Full Scale IQ (FSIQ) composite score of 88, placing performance in the Low Average range (25th percentile). The Verbal Comprehension Index was 92 and the Processing Speed Index was 79.",
    "mode": "fast", "top_k": 3, "thread_id": "cc1d2e3f-4a5b-6c7d-8e9f-a0b1c2d3e4f5",
    "sources": [
      { "source": "eval_2024_REDACTED.pdf", "page": 12, "parent_id": "12_2", "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98" },
      { "source": "eval_2024_REDACTED.pdf", "page": 13, "parent_id": "13_0", "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98" }
    ]
  },
  "documents_list_response_200": {
    "total_documents": 2,
    "documents": [
      { "document_id": "f7e6d5c4-b3a2-9180-7654-3210fedcba98", "filename": "eval_2024_REDACTED.pdf" },
      { "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "filename": "iep_2024_REDACTED.pdf" }
    ]
  },
  "preview_response_200": {
    "preview_token": "9f8e7d6c-5b4a-3210-fedc-ba9876543210",
    "sample_text": "This psychoeducational evaluation was conducted for STUDENT_NAME_1...",
    "entity_map": { "STUDENT_NAME_1": "Marcus Johnson", "DATE_OF_BIRTH_1": "01/15/2012" },
    "page_count": 24,
    "filename": "eval_2024.pdf"
  }
}
```

### `summarizer_mock.json`
```json
{
  "response_200": {
    "summary": "Psychoeducational Evaluation Summary\n\nStudent Information: 10-year-old, 4th grade. Evaluation completed March 15, 2024 by a licensed school psychologist.\n\nReferral Concerns: Difficulties with reading fluency, comprehension, written expression; possible ADHD concerns.\n\nCognitive Assessment (WISC-V):\n- Full Scale IQ: 88 (Low Average, 25th percentile)\n- Verbal Comprehension Index: 92 (Average)\n- Fluid Reasoning Index: 85 (Low Average)\n- Processing Speed Index: 79 (Below Average, 8th percentile)\n\nAcademic Achievement (WIAT-4):\n- Word Reading: 74 (4th percentile) — significantly below grade level\n- Reading Comprehension: 78 (7th percentile)\n- Spelling: 76 (5th percentile)\n- Math Problem Solving: 91 (27th percentile)\n\nDiagnoses Indicated: Specific Learning Disability in Reading (Dyslexia). ADHD Inattentive Type noted as differential requiring further evaluation.\n\nRecommendations: Orton-Gillingham reading instruction, extended time on assessments, preferential seating, reading specialist pull-out 3x/week.",
    "page_count": 24
  }
}
```

### `jargon_mock.json`
```json
{
  "level_1_response_200": { "simplified_text": "The student presents with deficits in phonological processing (CTOPP-2: PMC SS=74, 4th %ile; PAC SS=71, 3rd %ile). Findings meet DSM-5 criteria for SLD with Impairment in Reading (315.00), consistent with developmental dyslexia.", "flesch_kincaid_grade": 14.2, "level": 1 },
  "level_3_response_200": { "simplified_text": "The testing showed that your child has difficulty with the sound-based building blocks of reading — things like remembering the sounds in words and recognizing how words break into smaller sound parts. These scores were in the low range compared to other children the same age, which is why the evaluation found that your child has a reading learning disability (sometimes called dyslexia). This is something we can directly support with the right teaching approach.", "flesch_kincaid_grade": 7.1, "level": 3 },
  "level_5_response_200": { "simplified_text": "Some people find it harder to hear all the little sounds in words. Like, the word 'cat' has three sounds: k-a-t. Your brain sometimes has a tough time with that, and that's okay! It just means you learn to read in a slightly different way, and teachers can help you with special reading games and activities.", "flesch_kincaid_grade": 3.8, "level": 5 }
}
```

---

## 12. TypeScript Types (Source of Truth)

```ts
// src/types/api.ts

export type UUID = string;
export type ISODateTime = string;

export interface AuthLoginRequest { username: string; password: string; }
export interface AuthLoginResponse { access_token: string; token_type: "bearer"; }

export interface FeatureFlags {
  rag_enabled: boolean;
  summarizer_enabled: boolean;
  jargon_enabled: boolean;
}

export interface Project {
  id: UUID;
  display_label: string;
  created_at: ISODateTime;
  // student_id and student_id_hash deliberately omitted — never cross the gateway boundary.
}

export interface UploadedFile {
  id: UUID;
  document_id: UUID;
  filename_redacted: string;
  strategy: "standard" | "deep";
  chunks_added: number;
  uploaded_at: ISODateTime;
}

export interface Citation {
  source: string;
  page: number;
  parent_id: string;
  document_id: UUID;
}

export interface ChatMessage {
  id: UUID;
  role: "user" | "assistant";
  content: string;
  sources: Citation[];
  created_at: ISODateTime;
}

export interface Thread {
  id: UUID;
  title: string | null;
  created_at: ISODateTime;
  messages?: ChatMessage[];
}

export interface SummaryRun {
  id: UUID;
  document_id: UUID;
  filename_redacted: string;
  summary: string;
  page_count: number;
  created_at: ISODateTime;
}

export interface JargonRun {
  id: UUID;
  level: 1 | 2 | 3 | 4 | 5;
  input_preview: string; // first 200 chars
  simplified_text: string;
  fk_grade: number;
  created_at: ISODateTime;
}

// RAG
export interface RagPreviewResponse {
  preview_token: UUID;
  sample_text: string;
  entity_map: Record<string, string>;
  page_count: number;
  filename: string;
}

export interface RagUploadResponse {
  status: "ok";
  document_id: UUID;
  source: string;
  strategy: "standard" | "deep";
  chunks_added: number;
  avg_chunk_tokens: number;
}

export interface RagQueryRequest {
  question: string;
  project_id: UUID;
  document_id?: UUID;
  thread_id?: UUID;
  mode?: "fast" | "deep";
  top_k?: number;
}

export interface RagQueryResponse {
  answer: string;
  mode: "fast" | "deep";
  top_k: number;
  thread_id: UUID;
  sources: Citation[];
}

// Summarizer
export interface SummarizeJsonRequest { document_id: UUID; project_id?: UUID; }
export interface SummarizeResponse { summary: string; page_count: number; }

// Jargon
export interface JargonRequest { text: string; level?: 1 | 2 | 3 | 4 | 5; project_id?: UUID; }
export interface JargonResponse { simplified_text: string; flesch_kincaid_grade: number; level: 1 | 2 | 3 | 4 | 5; }

// Errors
export interface ApiErrorDetail { detail: string | Array<{ loc: string[]; msg: string; type?: string }>; }
```

---

## 13. PII Validation (Client-Side, Mirroring Server)

```ts
// src/lib/ferpa.ts

const SSN_PATTERN = /\b\d{3}-?\d{2}-?\d{4}\b/;
const DOB_PATTERN = /\b(0?[1-9]|1[0-2])[\/\-\.](0?[1-9]|[12]\d|3[01])[\/\-\.](19|20)\d{2}\b/;
const DISTRICT_ID_PATTERN = /\b\d{6,}\b/;

export function detectPiiInLabel(label: string): { ok: boolean; reason?: string } {
  if (label.length > 80) return { ok: false, reason: "Label must be 80 characters or fewer." };
  if (SSN_PATTERN.test(label)) return { ok: false, reason: "Looks like a Social Security number. Use a case code." };
  if (DOB_PATTERN.test(label)) return { ok: false, reason: "Looks like a date of birth. Use a case code." };
  if (DISTRICT_ID_PATTERN.test(label)) return { ok: false, reason: "Looks like a 6+ digit ID number. Use a case code." };
  return { ok: true };
}
```

---

## 14. Out of Scope for Monday Demo

- Multi-user account management. Admin-creates-user flow.
- SSO, OAuth, password reset.
- Streaming (SSE / WebSocket) responses.
- Async / job-queue summarization.
- Real-time collaboration / presence.
- Data Visualization tab implementation.
- Task Manager tab implementation.
- Internationalization.
- Mobile responsive past 768px (works, but not optimized).
- Dark mode.
- Document preview / inline PDF rendering.

---

## 15. Reference Mockups

Two source mockups exist in the project root:

- `mock_ui.png` — Polished "Welcome back, Dr. Lee" dashboard with three feature cards, recent files, FERPA trust panel. Visual style reference.
- `mock_ui_rough.png` — Rough sketch with project rail on left, central "What should we do today?" prompt. Information architecture reference (project-first).

The MVP combines both: the rough mockup's project rail + the polished mockup's dashboard cards on the empty-state landing.

---

## 16. Glossary

- **Project** — One per student case, the top-level organizing unit. Identified by a case code, never a name.
- **Document** — A PDF ingested into a project. Has an opaque `document_id` and a redacted filename.
- **Thread** — A multi-turn Q&A conversation scoped to a project. Replies append to it.
- **Run** — A single execution of the summarizer or jargon simplifier, logged to a project's history.
- **Mode (RAG)** — `fast` (single semantic search) or `deep` (semantic + same-page expansion).
- **Level (Jargon)** — 1 (clinical) through 5 (elementary).
- **Strategy (RAG upload)** — `standard` or `deep` chunking. `standard` is the default.
- **PII** — Personally Identifiable Information. Hard-blocked at the gateway.
- **FERPA** — Family Educational Rights and Privacy Act. Drives every constraint in this app.

---

## 17. Contacts

| Role | Person |
|------|--------|
| Engineering Lead | Natoli — architecture/scope, reviews every PR |
| Product Manager | Kai — process, deadlines |
| Product Design | Alyse, Zach |
| RAG team | Arham, Noble, Mohammed |
| Summarization | Arpita |
| Compliance / FERPA | Jon T. |
| Domain (school psych) | Dr. Josh Johnson |

---

End of context pack.
