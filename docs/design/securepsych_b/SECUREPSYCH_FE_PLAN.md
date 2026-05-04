# SecurePsych Frontend — Implementation Plan

> **Companion to:** `SECUREPSYCH_FE_CONTEXT.md` (read that first).
> **Sprint length:** 4 days — Friday May 1 → Monday May 4, 2026 (demo).
> **Definition of done:** A school psychologist can log in, create a project, upload a redacted PDF, ask grounded questions with citations, generate a structured summary, simplify clinical text, and review past activity — all on a light-themed, ChatGPT-style UI running on `localhost:5173` against the gateway on `localhost:8000`. Mocks toggleable via `VITE_USE_MOCKS=true`.

---

## 1. Day-by-Day Milestones

### Day 1 — Friday May 1: Foundations
- Vite + React + TypeScript scaffold in `frontend/`.
- Tailwind installed and configured with the §6 color tokens from the context pack.
- shadcn/ui initialized. Pull primitives: `button`, `input`, `card`, `dialog`, `dropdown-menu`, `tabs`, `toast`, `tooltip`, `skeleton`, `badge`, `slider`, `separator`, `sheet`.
- Folder structure (see §3) committed.
- API client (`src/api/client.ts`) — typed `fetch` wrapper, JWT injection, 401 redirect.
- Zustand auth store (`src/store/auth.ts`).
- TanStack Query provider in `main.tsx`.
- React Router with skeleton routes (everything renders a placeholder).
- MSW set up with the four mock JSONs from the context pack. `VITE_USE_MOCKS` flag.
- Login page wired to `POST /api/auth/login`. Auth flow round-trips end-to-end.
- App shell: TopBar, ProjectRail (empty state), main content area.
- Trust badges in rail footer.
- **End of Day 1 demo:** Log in with mock creds, see the dashboard skeleton.

### Day 2 — Saturday May 2: Projects + RAG
- Create-project dialog with PII validation (`src/lib/ferpa.ts`).
- Project list query, render in rail, "Load more" stub.
- Selected project state in Zustand. URL syncs to `/p/:projectId`.
- Project Overview page: lists files, recent threads, recent summaries, recent jargon runs.
- Document upload flow:
  - Step 1: file picker → `POST /api/rag/upload/preview` → display `entity_map` confirmation panel.
  - Step 2: user clicks **Confirm and ingest** → `POST /api/rag/upload` with `preview_token` and `project_id`.
- RAG chat panel:
  - Message list with user / assistant bubbles.
  - Composer with Enter-to-send (Shift+Enter newline).
  - `mode` toggle in composer header (Fast / Deep).
  - Citation footnotes under each assistant message.
  - Optional `document_id` filter dropdown (scope to single doc).
- Threads sidebar in chat view, click loads thread.
- Document Delete with confirmation dialog.
- **End of Day 2 demo:** Full RAG happy path on mocks.

### Day 3 — Sunday May 3: Summarizer + Jargon + Polish
- Summarizer page:
  - Mode toggle: Upload PDF (Mode A) vs. Existing Document (Mode B, dropdown of project's docs).
  - Submit → friendly "Working on it…" panel with skeleton (target 90s tolerance).
  - Display structured summary with monospace blocks for scores.
  - "Save to history" is automatic on the backend when `project_id` is sent — show a toast "Summary saved to project history".
- Jargon page:
  - Textarea (or "Upload PDF" toggle).
  - Level slider (1–5) with labels under each tick.
  - Result panel with the simplified text + Flesch–Kincaid grade pill.
  - Copy button.
- History page: combined timeline of threads, summaries, jargon runs.
- Empty states everywhere.
- Toast system wired (success / error).
- 401 → toast → redirect.
- Smoke tests (Vitest) — 1 per tool, happy path.
- Run full test suite — must pass before any PR.
- **End of Day 3 demo:** All three tools live on mocks. Polish pass.

### Day 4 — Monday May 4 morning: Demo prep
- Smoke test against the **live** gateway: login, create project, upload a fixture PDF (ask Arpita for one), query, summarize, simplify.
- Fix any contract drift (the gateway code is truth, the docs are aspirational).
- Rehearse the demo script (§9 below).
- Confirm `VITE_USE_MOCKS=true` works as a fallback if the live backend has issues.
- Tag the commit, open PR (assign Natoli per `COLLABORATION.md`).
- **Demo at the agreed time.**

---

## 2. Project Scaffolding (Day 1, first hour)

```bash
# from securepsych-dev/
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install react-router-dom @tanstack/react-query zustand react-hook-form @hookform/resolvers zod
npm install lucide-react clsx tailwind-merge class-variance-authority
npm install -D msw vitest @testing-library/react @testing-library/jest-dom @vitest/ui jsdom
npx shadcn@latest init        # accept defaults; choose "neutral" base color
npx shadcn@latest add button input label card dialog dropdown-menu tabs toast tooltip skeleton badge slider separator sheet textarea form
npx msw init public/ --save
```

**`frontend/.env.example`:**

```
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCKS=false
```

**`frontend/.env.local`** (gitignored, dev only):

```
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCKS=true
```

---

## 3. File / Folder Structure

```
frontend/
├── public/
│   └── mockServiceWorker.js          # generated by msw init
├── src/
│   ├── api/
│   │   ├── client.ts                 # typed fetch wrapper, JWT, 401 handling
│   │   ├── auth.ts                   # login, logout
│   │   ├── projects.ts               # CRUD + history sub-resources
│   │   ├── rag.ts                    # preview, upload, query, list, delete
│   │   ├── summarizer.ts
│   │   ├── jargon.ts
│   │   └── system.ts                 # /health, /api/config
│   ├── components/
│   │   ├── ui/                       # shadcn primitives (auto-generated)
│   │   ├── layout/
│   │   │   ├── AppShell.tsx
│   │   │   ├── ProjectRail.tsx
│   │   │   ├── TopBar.tsx
│   │   │   ├── TrustBadges.tsx
│   │   │   └── Footer.tsx
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── RequireAuth.tsx       # route guard
│   │   ├── projects/
│   │   │   ├── ProjectListItem.tsx
│   │   │   ├── CreateProjectDialog.tsx
│   │   │   └── ProjectSwitcher.tsx
│   │   ├── dashboard/
│   │   │   ├── FeatureCardGrid.tsx
│   │   │   ├── FeatureCard.tsx       # one of: Q&A, Summarizer, Jargon (+ disabled stretch tiles)
│   │   │   ├── RecentActivityList.tsx
│   │   │   └── WelcomeHeader.tsx
│   │   ├── chat/
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── UserMessage.tsx
│   │   │   ├── AssistantMessage.tsx
│   │   │   ├── CitationFootnotes.tsx
│   │   │   ├── Composer.tsx
│   │   │   ├── ModeToggle.tsx        # fast | deep
│   │   │   ├── DocumentScopeFilter.tsx
│   │   │   └── ThreadList.tsx
│   │   ├── upload/
│   │   │   ├── UploadDialog.tsx
│   │   │   ├── PIIReviewPanel.tsx    # the redaction confirmation screen
│   │   │   └── EntityMapTable.tsx
│   │   ├── summarizer/
│   │   │   ├── SummarizerPanel.tsx
│   │   │   ├── SummarizeModeToggle.tsx   # Mode A | Mode B
│   │   │   └── SummaryDisplay.tsx
│   │   ├── jargon/
│   │   │   ├── JargonPanel.tsx
│   │   │   ├── LevelSlider.tsx
│   │   │   └── SimplifiedOutput.tsx
│   │   ├── history/
│   │   │   ├── HistoryTimeline.tsx
│   │   │   ├── ThreadCard.tsx
│   │   │   ├── SummaryCard.tsx
│   │   │   └── JargonRunCard.tsx
│   │   └── shared/
│   │       ├── EmptyState.tsx
│   │       ├── LoadingSkeleton.tsx
│   │       ├── ErrorBoundary.tsx
│   │       ├── LoadMoreButton.tsx
│   │       ├── DangerConfirmDialog.tsx
│   │       └── CopyButton.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useProjects.ts            # list, get, create
│   │   ├── useProjectFiles.ts
│   │   ├── useThread.ts
│   │   ├── useRagQuery.ts
│   │   ├── useSummarize.ts
│   │   ├── useJargon.ts
│   │   ├── useFeatureFlags.ts        # /api/config
│   │   ├── useInfinitePagination.ts  # forward-compat with standard schema
│   │   └── useToast.ts               # shadcn toast wrapper
│   ├── lib/
│   │   ├── cn.ts                     # clsx + twMerge
│   │   ├── ferpa.ts                  # PII regexes
│   │   ├── format.ts                 # date / score formatting
│   │   └── jwt.ts                    # decode (no validation — server's job)
│   ├── mocks/
│   │   ├── browser.ts                # MSW worker setup
│   │   ├── handlers.ts               # all HTTP handlers
│   │   └── data/
│   │       ├── history.json
│   │       ├── rag.json
│   │       ├── summarizer.json
│   │       └── jargon.json
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx         # the welcome cards
│   │   ├── ProjectOverviewPage.tsx
│   │   ├── ProjectChatPage.tsx       # + :threadId variant
│   │   ├── ProjectSummarizerPage.tsx
│   │   ├── ProjectJargonPage.tsx
│   │   ├── ProjectHistoryPage.tsx
│   │   └── NotFoundPage.tsx
│   ├── store/
│   │   ├── auth.ts                   # token + user role
│   │   └── selection.ts              # selected project id
│   ├── types/
│   │   ├── api.ts                    # see context pack §12
│   │   └── ui.ts
│   ├── App.tsx                       # router root
│   ├── main.tsx                      # providers: QueryClient, ToastProvider, ErrorBoundary
│   ├── router.tsx                    # route table
│   └── index.css                     # tailwind directives + CSS variables
├── .env.example
├── .env.local                        # gitignored
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.ts
├── tsconfig.json
└── vite.config.ts
```

---

## 4. State Management

| Concern | Tool | Why |
|---------|------|-----|
| Server data (projects, threads, messages, summaries, jargon runs, files) | TanStack Query | Caching, refetch-on-window-focus disabled (LAN, low traffic), retry once on 5xx, never on 4xx. |
| Auth token, user role | Zustand | Tiny global slice. Persisted to sessionStorage. |
| Selected project ID | Zustand + URL | URL is truth (`/p/:projectId`); store mirrors for non-routed components. |
| Form state (login, create project, composer, jargon textarea) | react-hook-form + zod | Schema-validated, type-safe. |
| Ephemeral UI (open/closed dialogs, dropdowns) | React state | No global store needed. |

### 4.1 Query Keys Convention

```ts
['projects']
['projects', projectId]
['projects', projectId, 'files']
['projects', projectId, 'threads']
['projects', projectId, 'threads', threadId]
['projects', projectId, 'summaries']
['projects', projectId, 'jargon-runs']
['rag', 'documents', projectId]
['system', 'config']
```

Mutations invalidate the relevant subtree (`['projects', projectId]`) on success.

---

## 5. API Client Design

```ts
// src/api/client.ts (sketch)

const BASE = import.meta.env.VITE_API_BASE_URL;

export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) { super(`HTTP ${status}`); }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit & { json?: unknown } = {}
): Promise<T> {
  const token = useAuthStore.getState().token;
  const headers = new Headers(init.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);

  let body: BodyInit | undefined;
  if (init.json !== undefined) {
    headers.set('Content-Type', 'application/json');
    body = JSON.stringify(init.json);
  } else if (init.body) {
    body = init.body;
  }

  const res = await fetch(`${BASE}${path}`, { ...init, headers, body });

  if (res.status === 401) {
    useAuthStore.getState().clear();
    window.location.assign('/login');
    throw new ApiError(401, { detail: 'Session expired' });
  }
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}
```

Per-resource modules wrap `apiFetch` with typed signatures matching `src/types/api.ts`. Example:

```ts
// src/api/rag.ts
export const ragApi = {
  preview: (file: File) => {
    const fd = new FormData(); fd.append('file', file);
    return apiFetch<RagPreviewResponse>('/api/rag/upload/preview', { method: 'POST', body: fd });
  },
  upload: (args: { previewToken: string; projectId: UUID; strategy?: 'standard' | 'deep' }) => {
    const fd = new FormData();
    fd.append('preview_token', args.previewToken);
    fd.append('project_id', args.projectId);
    if (args.strategy) fd.append('strategy', args.strategy);
    return apiFetch<RagUploadResponse>('/api/rag/upload', { method: 'POST', body: fd });
  },
  query: (req: RagQueryRequest) =>
    apiFetch<RagQueryResponse>('/api/rag/query', { method: 'POST', json: req }),
  listDocuments: (projectId: UUID) =>
    apiFetch<{ total_documents: number; documents: { document_id: UUID; filename: string }[] }>(
      `/api/rag/documents?project_id=${projectId}`
    ),
  deleteDocument: (documentId: UUID, projectId: UUID) =>
    apiFetch<{ deleted: boolean; chunks_removed: number }>(
      `/api/rag/documents/${documentId}?project_id=${projectId}`,
      { method: 'DELETE' }
    ),
};
```

---

## 6. Mock Layer (MSW)

`src/mocks/handlers.ts` returns the JSON fixtures from §11 of the context pack. The handler set covers every endpoint — login, projects, files, threads, RAG, summarize, jargon, system. Toggle:

```ts
// src/main.tsx
if (import.meta.env.VITE_USE_MOCKS === 'true') {
  const { worker } = await import('./mocks/browser');
  await worker.start({ onUnhandledRequest: 'bypass' });
}
```

The `bypass` setting means any handler we forget to write falls through to the real network — useful when partially mocked.

---

## 7. Component Inventory (Key Signatures)

```tsx
// Layout
<AppShell>{children}</AppShell>
<ProjectRail selectedProjectId?: UUID />
<TopBar systemStatus: 'ok' | 'unknown' />
<TrustBadges />

// Auth
<LoginForm onSuccess: () => void />
<RequireAuth>{children}</RequireAuth>  // route guard, redirects to /login if no token

// Projects
<ProjectListItem project: Project active: boolean onSelect: () => void />
<CreateProjectDialog open: boolean onOpenChange: (b: boolean) => void onCreated: (p: Project) => void />

// Dashboard
<FeatureCardGrid flags: FeatureFlags />
<FeatureCard
  icon: LucideIcon
  title: string
  description: string
  href: string
  disabled?: boolean
  comingSoon?: boolean
/>
<RecentActivityList projectId?: UUID limit?: number />

// Chat (RAG)
<ChatPanel projectId: UUID threadId?: UUID />
<MessageList messages: ChatMessage[] />
<UserMessage message: ChatMessage />
<AssistantMessage message: ChatMessage onCitationClick: (c: Citation) => void />
<CitationFootnotes citations: Citation[] />
<Composer
  onSubmit: (q: { question: string; mode: 'fast' | 'deep'; documentId?: UUID }) => void
  busy: boolean
  scopedDocumentId?: UUID
/>
<ModeToggle value: 'fast' | 'deep' onChange: (m) => void />
<DocumentScopeFilter projectId: UUID value?: UUID onChange: (id?: UUID) => void />
<ThreadList projectId: UUID activeThreadId?: UUID />

// Upload
<UploadDialog projectId: UUID open onOpenChange />
<PIIReviewPanel
  preview: RagPreviewResponse
  onConfirm: () => void
  onCancel: () => void
  busy: boolean
/>

// Summarizer
<SummarizerPanel projectId: UUID />
<SummaryDisplay summary: string pageCount: number />

// Jargon
<JargonPanel projectId: UUID />
<LevelSlider value: 1|2|3|4|5 onChange: (l) => void />
<SimplifiedOutput text: string fkGrade: number level: 1|2|3|4|5 />

// Shared
<EmptyState icon: LucideIcon title: string description: string action?: ReactNode />
<LoadMoreButton hasMore: boolean loading: boolean onClick: () => void />
<DangerConfirmDialog
  title: string
  description: string
  confirmLabel: string
  onConfirm: () => void | Promise<void>
  trigger: ReactNode
/>
<CopyButton text: string />
```

---

## 8. Hooks (Day 1–3)

```ts
useAuth()                                   // { token, user, login, logout }
useFeatureFlags()                           // FeatureFlags from /api/config, cached forever
useProjects()                               // list of Project, infinite pagination
useProject(projectId)                       // single Project
useProjectFiles(projectId)                  // UploadedFile[]
useProjectThreads(projectId)                // Thread[] (summaries)
useThread(projectId, threadId)              // Thread with messages
useProjectSummaries(projectId)              // SummaryRun[]
useProjectJargonRuns(projectId)             // JargonRun[]
useRagPreview()                             // mutation
useRagCommit()                              // mutation; invalidates files + documents
useRagQuery(projectId)                      // mutation; invalidates threads + the active thread
useDeleteDocument(projectId)                // mutation; invalidates files + documents
useSummarize(projectId)                     // mutation; invalidates summaries
useJargon(projectId)                        // mutation; invalidates jargon-runs
```

---

## 9. Demo Script (the story we are rehearsing for Monday)

1. **Open** `http://localhost:5173`. Show the login screen.
2. **Log in** with the seeded credentials. Land on the dashboard. Point out the trust badges in the rail footer ("FERPA-compliant", "On-prem only", "No internet").
3. **Talking point:** "While I do this, I have a terminal open running `curl api.openai.com` — it fails. The system has no outbound network." (Per FERPA checklist item 12.)
4. **Create a project.** Type a name with a number that looks like a date — show the live PII validation. Correct to `Case 2026-014`. Submit.
5. **Upload a PDF** — the fixture eval. Pause on the PII review screen: explain that the system has detected names and DOBs and will replace them with placeholders before storage. Confirm.
6. **Switch to Q&A.** Ask: *"What cognitive assessments were administered and what were the composite scores?"* Wait for the answer. Click a citation footnote — show the page reference.
7. **Switch to Summarize** on the same project. Run Mode B (existing document). Show the structured output appearing in the result panel.
8. **Switch to Jargon.** Paste a clinical paragraph from the eval. Set the level slider to 3 (Parent). Show the rewrite. Show the Flesch–Kincaid grade pill. Move the slider to 5 (Elementary) — show the rewrite changes.
9. **History tab.** Show the full activity timeline.
10. **Delete the document** — show the confirmation dialog. Talk about the FERPA hard-delete requirement.
11. **Log out.** Done.

Fallback: if the live backend has any trouble, restart the frontend with `VITE_USE_MOCKS=true npm run dev` — the mock layer covers every step above.

---

## 10. Testing

- **Smoke tests (Vitest):**
  - `LoginPage` — submitting valid creds calls the API and stores token.
  - `CreateProjectDialog` — PII validation rejects "John Doe DOB 01/15/2012".
  - `ChatPanel` — submits a question, renders the assistant reply with citations.
  - `SummarizerPanel` — Mode B submits a document_id and renders the summary.
  - `JargonPanel` — slider change updates `level` and a re-submit returns a new fk grade.
- **Run `npm run test` before every PR.** Per Natoli's note: full suite passes or the PR doesn't open.
- **Manual checklist before demo:**
  - [ ] Login round-trips against live gateway.
  - [ ] Project create blocks PII labels.
  - [ ] Upload preview shows entity map.
  - [ ] RAG answer renders citations.
  - [ ] Summarizer Mode A and Mode B both work.
  - [ ] Jargon all 5 levels return content.
  - [ ] Document delete confirmation dialog appears.
  - [ ] Logout returns to /login.
  - [ ] `VITE_USE_MOCKS=true` works as a fallback.
  - [ ] No console errors on the happy path.

---

## 11. Risk Register

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Backend not reachable at demo time | Medium | MSW fallback toggle, rehearsed. |
| Summarizer >90s on demo PDF | Medium | Use a smaller fixture, 10–20 pages, for the demo. |
| RAG hallucinates / cites wrong page | Low (per checklist) | Use a fixture we have rehearsed against; have a backup question. |
| PII regex false positive blocks valid label | Low | Allow `Case 20XX-NNN` patterns; show the *exact* server rule in the helper text. |
| Token expires mid-demo | Very low (8h window) | Log in fresh right before. |
| `shadcn add` introduces an unexpected dep | Low | Use `--yes` and pin versions; review the diff. |
| CORS misconfigured on live backend | Low | Gateway `.env.example` already lists `localhost:5173`. Confirm deployed value matches. |

---

## 12. Open Questions (Resolve While Building)

These can be answered in parallel with the build — none of them block Day 1.

- [ ] Confirm the gateway's PII regex set matches our client-side mirror (read `backend/gateway/auth/store.py` or `db/crud.py` for the canonical patterns).
- [ ] Verify the actual response shape of `GET /api/projects/{id}/threads` against the docs (the docs say messages are excluded — confirm).
- [ ] Confirm what happens when the user uploads a non-PDF file — server returns 422; frontend should toast a friendly error.
- [ ] Confirm the `top_k` upper bound. We will hide the control in MVP and pass `top_k: 3` for fast, `top_k: 2` for deep (per the `RAG_Summary.md` benchmarking note).
- [ ] Ask Arpita for a non-real-student fixture PDF (≤ 24 pages) we can use in the demo.
- [ ] Confirm with Natoli that single-user demo is acceptable (one shared bootstrap account, no admin-creates-user UX).
- [ ] Confirm the deployed gateway's `CORS_ALLOWED_ORIGINS` includes the frontend's actual deploy URL.

---

## 13. Definition of Ready (Hand-Off to a New Coding Session)

If you (or another contributor) opens a new chat to start building, paste both `SECUREPSYCH_FE_CONTEXT.md` and this plan, then say:

> "Implement Day 1 of the SecurePsych frontend per the plan. Begin with the Vite scaffold and stop after the login page round-trips against MSW mocks. Show me the diff before installing dependencies beyond the listed ones."

That phrasing keeps the work scoped to a single milestone, gates on dep additions (per Natoli's rule), and gives Claude a hard stop so you can review.

---

End of plan.
