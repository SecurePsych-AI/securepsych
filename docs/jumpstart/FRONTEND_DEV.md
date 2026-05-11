# Frontend — Local Development & Demo Walkthrough

This is the orientation doc for anyone reviewing or running the SecurePsych frontend (Variation B). It assumes you've already read the design handoff at [`docs/design/securepsych_b/README.md`](../design/securepsych_b/README.md) and want to know what was built and how to run it.

---

## At a glance

- **Stack:** Vite + React 18 + TypeScript (strict) + TailwindCSS + shadcn-style primitives + Zustand + TanStack Query + React Router v6 + MSW.
- **Demo path:** runs entirely against MSW (Mock Service Worker) — no backend needed for the rehearsed demo flow.
- **Live path:** flip `VITE_USE_MOCKS=false` and the same UI hits the real gateway on `:8000`.
- **No new dependencies were added beyond the ones in [`SECUREPSYCH_FE_PLAN.md` §2](../design/securepsych_b/SECUREPSYCH_FE_PLAN.md). Per Natoli's rule, dep additions need approval.**

---

## Run it

```bash
# from the project root
cd frontend
npm install      # auto-installs the MSW service worker into public/
npm run dev      # serves on http://localhost:5173
```

Login: `dr.lee` / `demo-pass-2026`.

For full-stack (gateway + 3 services), use the configs in [`.claude/launch.json`](../../.claude/launch.json) — each service runs via `python -m uvicorn ... --app-dir backend/<service>`.

---

## Mock vs. live backend

| File | Knob | Effect |
|---|---|---|
| `frontend/.env.local` | `VITE_USE_MOCKS=true` | MSW intercepts every API call. No backend needed. **Default.** |
| `frontend/.env.local` | `VITE_USE_MOCKS=false` | Frontend hits the real gateway on `localhost:8000`. Restart Vite after changing. |

The MSW setup lives in [`src/mocks/`](../../frontend/src/mocks/):
- [`handlers.ts`](../../frontend/src/mocks/handlers.ts) — every endpoint from [CONTEXT §10](../design/securepsych_b/SECUREPSYCH_FE_CONTEXT.md), wrapped in MSW v2 handlers.
- [`store.ts`](../../frontend/src/mocks/store.ts) — small in-memory store so create-project / upload / send-message persist across the demo.
- [`data/seed.ts`](../../frontend/src/mocks/data/seed.ts) — canned content (sample summary, jargon outputs by level, sample citations).
- [`browser.ts`](../../frontend/src/mocks/browser.ts) — worker registration, started conditionally from [`src/main.tsx`](../../frontend/src/main.tsx).

If you want to **bypass MSW for one fetch** (e.g., to verify a live endpoint), unregister the worker from DevTools console: `navigator.serviceWorker.getRegistration().then(r => r.unregister())`.

---

## How the design spec maps to the code

| Design screen (Variation B) | Page component | Notes |
|---|---|---|
| `B_Login` | [`src/pages/LoginPage.tsx`](../../frontend/src/pages/LoginPage.tsx) → [`LoginForm`](../../frontend/src/components/auth/LoginForm.tsx) | Trust pills below the card. 401 → inline banner. `?expired=1` shows the session-expired pattern. |
| `B_Dashboard` | [`src/pages/DashboardPage.tsx`](../../frontend/src/pages/DashboardPage.tsx) | Welcome headline, [`FeatureCardGrid`](../../frontend/src/components/dashboard/FeatureCardGrid.tsx) (Q&A / Summarize / Jargon + 2 "Coming soon"), [`RecentActivityList`](../../frontend/src/components/dashboard/RecentActivityList.tsx). |
| `B_CreateProject` | [`src/components/projects/CreateProjectDialog.tsx`](../../frontend/src/components/projects/CreateProjectDialog.tsx) | Live PII validation via [`src/lib/ferpa.ts`](../../frontend/src/lib/ferpa.ts). Verbatim FERPA copy. |
| `B_PIIReview` | [`src/components/upload/PIIReviewPanel.tsx`](../../frontend/src/components/upload/PIIReviewPanel.tsx) | Side-by-side panels with entity highlighting. **Count copy intentionally dropped** per stakeholder decision. |
| `B_Chat` | [`src/pages/ProjectChatPage.tsx`](../../frontend/src/pages/ProjectChatPage.tsx) | [`MessageList`](../../frontend/src/components/chat/MessageList.tsx), [`Composer`](../../frontend/src/components/chat/Composer.tsx), [`CitationFootnotes`](../../frontend/src/components/chat/CitationFootnotes.tsx). **Footnote-style citations**, not the hover-sync side panel — that's a post-demo polish item. |
| `B_Summarizer` | [`src/pages/ProjectSummarizerPage.tsx`](../../frontend/src/pages/ProjectSummarizerPage.tsx) → [`SummaryDisplay`](../../frontend/src/components/summarizer/SummaryDisplay.tsx) | Auto-renders the seeded summary; Generate button re-runs against the picked document. |
| `B_SummarizerInProgress` | Same page, in-flight state | Skeleton lines + "Working on it…" banner. Sync only — no SSE per [CONTEXT §14](../design/securepsych_b/SECUREPSYCH_FE_CONTEXT.md). |
| `B_Jargon` | [`src/pages/ProjectJargonPage.tsx`](../../frontend/src/pages/ProjectJargonPage.tsx) → [`LevelSelector`](../../frontend/src/components/jargon/LevelSelector.tsx) | Five level buttons; level switch after a result is generated re-simplifies (per spec). |
| `B_History` | [`src/pages/ProjectHistoryPage.tsx`](../../frontend/src/pages/ProjectHistoryPage.tsx) | All / Q&A / Summaries / Jargon filter; JSON export. |
| `B_DeleteConfirm` | Inline `Dialog` in [`ProjectChatPage.tsx`](../../frontend/src/pages/ProjectChatPage.tsx) | Hard-delete copy: "cannot be undone · required by FERPA." |

---

## State management

- **Auth token** — [`src/store/auth.ts`](../../frontend/src/store/auth.ts) — Zustand + sessionStorage. No localStorage (XSS concern, per the plan).
- **Active project** — [`src/store/selection.ts`](../../frontend/src/store/selection.ts) — set by route + rail + create flow.
- **Server state** — TanStack Query everywhere. Cache keys follow the convention from [PLAN §4.1](../design/securepsych_b/SECUREPSYCH_FE_PLAN.md): `['projects']`, `['projects', id, 'files']`, etc. Mutations invalidate the relevant subtree on success.
- **Auth-failure handling** — [`src/api/client.ts`](../../frontend/src/api/client.ts) catches `401` globally, clears the auth store, and redirects to `/login?expired=1`.

---

## Design decisions worth flagging during review

| Decision | Why | File |
|---|---|---|
| shadcn primitives written by hand instead of `npx shadcn add` | Avoids requiring a separate CLI step during setup; no behavioral difference. | [`src/components/ui/`](../../frontend/src/components/ui/) |
| Numbered citations are footnote-style under the assistant message | Variation B handoff describes a hover-sync side panel; PLAN keeps footnotes for MVP. | [`CitationFootnotes.tsx`](../../frontend/src/components/chat/CitationFootnotes.tsx) |
| PII Review drops "5 entities · 46 occurrences" copy | Gateway's `entity_map` doesn't return per-entity counts. Out-of-scope to add. | [`PIIReviewPanel.tsx`](../../frontend/src/components/upload/PIIReviewPanel.tsx) |
| Sync responses, no SSE | Matches [CONTEXT §14](../design/securepsych_b/SECUREPSYCH_FE_CONTEXT.md). Streaming is a post-demo enhancement. | All mutation hooks |
| Dev creds + `dev_data/` | `scripts/setup_backend_dev_env.py` writes `.env` files under each service with `SECUREPSYCH_ENV=test`. The dev volume bypasses the LUKS-mount FERPA check by design — never deploy this to the school server. | [`scripts/setup_backend_dev_env.py`](../../scripts/setup_backend_dev_env.py) |

---

## Tests

```bash
cd frontend
npm run test
```

Smoke coverage:
- [`src/lib/ferpa.test.ts`](../../frontend/src/lib/ferpa.test.ts) — PII validation, including the demo-script block on `John Doe DOB 01/15/2012`.
- [`src/lib/format.test.ts`](../../frontend/src/lib/format.test.ts) — relative time formatting.
- [`src/components/chat/CitationFootnotes.test.tsx`](../../frontend/src/components/chat/CitationFootnotes.test.tsx) — citation rendering.

The full E2E demo flow was verified manually via the running preview server during build (`preview_eval`). Add component tests as the surface stabilizes — Vitest setup is already wired.

---

## The demo script

Same one as [`SECUREPSYCH_FE_PLAN.md` §9](../design/securepsych_b/SECUREPSYCH_FE_PLAN.md). On the mock path, every step works end-to-end. On the live path, steps 1–5 (login, project CRUD) are verified; steps 6–8 (RAG/Summarize/Jargon) need Ollama running with the configured model.

If anything is flaky during the live demo, set `VITE_USE_MOCKS=true` and restart Vite — instant fallback.
