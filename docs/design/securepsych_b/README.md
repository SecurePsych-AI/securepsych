# Handoff: SecurePsych Frontend (Variation B — Unified Composer)

## Overview

SecurePsych is an on-prem, FERPA-compliant AI assistant for school psychologists. It provides three core tools — RAG Q&A across uploaded evaluations, structured document summarization, and a clinical-jargon simplifier — all scoped to per-student "projects". The backend already exists; this handoff covers the frontend that talks to it.

The chosen direction is **Variation B — "Unified Composer"**: a project-rail layout where the three tools are exposed as a single composer on the project landing surface and as a tool-switcher segmented control in the workspace top bar. Citations live in a right-hand side panel (rather than inline footnotes), and the PII-redaction review is a side-by-side "original vs. stored" comparison.

## About the Design Files

The files in `reference/` are **design references created in HTML/JSX** — interactive prototypes showing intended look, layout, and behavior. **They are not production code to ship.** Inline styles, ad-hoc utility classes, and a single hand-rolled `styles.css` were used for speed of iteration; none of that should be lifted directly.

The implementation task is to **recreate these designs in the SecurePsych frontend codebase using its established patterns** — Vite + React + TypeScript + Tailwind + shadcn/ui per the project plan. The HTML mocks are the source of truth for layout, copy, color, spacing, and behavior; the implementation should rebuild them using shadcn primitives (Dialog, Tabs, Card, Button, Input, Textarea, ScrollArea, etc.) and Tailwind utility classes mapped against the design tokens listed below.

If you want to inspect the prototypes interactively, open `reference/SecurePsych Explorations.html` in a browser — pan/zoom around the canvas. Variation B is the middle column.

## Fidelity

**High-fidelity.** Final colors, typography, spacing, copy, and most interaction states are settled. Pixel-perfect recreation is the goal, with one caveat: any place the mock uses inline-style hex values, prefer the corresponding Tailwind/token class. Where the mock and a clean shadcn primitive disagree on minor chrome (focus rings, disabled states, etc.), prefer shadcn's defaults — they're already accessibility-tuned.

## Screens / Views

Each screen below maps 1:1 to an artboard in the prototype canvas. File references point into `reference/`.

### 1. Sign-In (`B_Login` — `variation-b.jsx`)
- **Purpose:** Username + password against the local auth endpoint. Returns a session token (8h TTL, session-only).
- **Layout:** Centered single column, ~340px wide, vertically centered on `--bg-primary` (white). Brand mark + "SecurePsych" wordmark above title; "Sign in" h2; subtitle "Local server · session-only token"; username input; password input; primary button (full-width); trust pills row (FERPA / On-prem / Air-gapped) at the bottom.
- **Notes:** Deliberately minimal — **no post-sign-in stats or marketing content on this page**. Only the trust pills are shown.
- **Behavior:** Submit → POST credentials → on success route to last-visited project or workspace landing. Error banner above the form on failure (401 → "Incorrect username or password"; 429 → "Too many attempts, try again in N minutes").

### 2. Workspace Landing (`B_Dashboard` — `variation-b.jsx`)
- **Purpose:** First screen after sign-in when no project is selected. Centerpiece is the unified composer.
- **Layout:** Full project rail on left (264px), workspace on right.
  - **Headline:** "What should we do today, Dr. Lee?" (centered, 28px/600/-0.02em letter-spacing).
  - **Composer card** below headline: textarea + a control row containing:
    - "Select project" button (chevron-down, opens project picker)
    - Tool segmented control with three options: **Ask** (default), **Summarize**, **Simplify** (accent-filled when active)
    - Right side: "Attach PDF" ghost button, primary send button.
  - **Suggestion chips** (3, equal-width grid below composer): "Ask: 'What were the FSIQ composite scores?'" / "Summarize: latest evaluation" / "Simplify: this paragraph at parent level". Click hydrates the composer.
  - **"Continue where you left off"** card-list below: ~3 recent activity rows (kind tag, title, project, timestamp). Each row navigates to the corresponding thread/summary/jargon run.
- **Behavior:** Send button is disabled until a project is selected. Choosing a tool from the segmented control changes the placeholder text in the textarea ("Ask anything about…", "Pick a document to summarize…", "Paste clinical text to simplify…").

### 3. Create Project (`B_CreateProject` — `variation-b-extra.jsx`)
- **Purpose:** Modal opened from "Select project → New project" or from the workspace landing.
- **Layout:** Centered modal (480px) over a blurred dashboard. Header "Start a new project"; subtitle. Two fields: **Case label** (with live PII validation — green check + "Looks good. Format `Case 20XX-NNN` is recommended" when valid; red error + "Looks like a name and date of birth. Use a case code such as `Case 2026-014`. Names, birthdates, and 6+ digit IDs are blocked at the gateway." when not). **Internal student ID** (optional, hashed) with helper "Sent once, never returned. Hashed with a keyed BLAKE2b function." Bottom callout in `--bg-secondary`: "**Don't include** names, dates of birth, SSNs, or 6+ digit IDs in the label. The gateway will reject them."
- **Behavior:** Validate on blur and on submit. Block create when label fails the gateway regex (names, DOBs, 6+ digit IDs). Internal ID is optional; hash client-side stub before posting. On success → switch active project to the new one and route to its workspace.

### 4. PII Redaction Review (`B_PIIReview` — `variation-b.jsx`)
- **Purpose:** Shown after a PDF is uploaded but before it's ingested. Lets the user verify the gateway-detected PII before originals are discarded.
- **Layout:**
  - Page header: "Confirm what gets stored" + subtitle. Right side: Cancel / "Confirm and ingest" primary buttons.
  - **Two equal-width text panels (side-by-side):**
    - Left: "Original — discarded" (warning-tinted highlights for detected entities)
    - Right: "Stored — what we keep" (accent-tinted highlights showing `{TOKEN_NAME_N}` placeholders)
    - Each panel scrolls independently; max-height 240px.
  - **Replacement map** below: 5-column grid, one column per detected entity. Each shows occurrence count, original value (mono), arrow, accent-pill placeholder.
  - Header strip on map: "5 entities · 46 occurrences across 24 pages" + chunking strategy tag.
- **Behavior:** Confirm → POST `/documents/ingest` with confirmed map → close → show document in Documents list. Cancel → discard upload session. Originals are never persisted regardless of choice.

### 5. RAG Q&A (`B_Chat` — `variation-b.jsx`)
- **Purpose:** Threaded conversation grounded in the project's documents. **Every claim cites at least one source.**
- **Layout:** Project rail (with Threads sub-section visible) | Workspace.
  - **Top bar:** breadcrumbs "Case 2026-014 / Cognitive scores · WISC-V" + tool segmented control on the right (Folder / Message[active] / FileText / Languages / History) + status pill.
  - **Two-column body:** main chat (left, scrolls) + 320px Sources side panel (right).
  - **Chat:** Standard user/assistant bubbles. Assistant body has an action row at the bottom: "Cited 3 sources →" muted text + Copy button. Citation numbers in prose are NOT inline — they live in the side panel.
  - **Sources panel:** Header "Sources · 3 citations" + list of citation cards. Each card has a numbered chip (e.g. "1 page 12"), filename, italicized snippet quote, and "Open page" / "Copy quote" actions. The card matching the most recently hovered claim is highlighted with an accent border + soft shadow.
  - **Composer (footer):** scope dropdown ("All docs" / specific doc), Fast/Deep mode toggle, Send button.
- **Behavior:** Hovering a numbered claim in the assistant message highlights its citation card. Clicking "Open page" opens a PDF viewer at that page (or downloads if no inline viewer). Streaming: tokens stream in; citations appear after the response completes.

### 6. Document Summarizer (`B_Summarizer` — `variation-b.jsx`)
- **Purpose:** Generates a structured psychoeducational summary (Student / Referral / Cognitive / Achievement / Diagnoses / Recommendations) from a project document.
- **Layout:**
  - Page header "Summarize" + subtitle.
  - **Document picker composer:** Single horizontal row card showing the chosen doc (file icon, name, "24 pages · ~187 chunks", chunking tag). Action row: "Switch document" / "Or upload new" / right side hint + primary "Generate summary".
  - **Result card:** Header (title + tag + Copy/Export). Two-column body: 200px left nav (section anchor list, current section highlighted accent-soft) + main content area with the rendered section (typography mix of bold section title, mono score blocks, and paragraph commentary).
- **Behavior:** Generate is synchronous (~90s for a 24-page doc) — show in-progress state (see #7). Result is auto-saved to project history. Copy and Export TXT both target the **rendered** summary text, not the underlying JSON.

### 7. Summarizer In-Progress (`B_SummarizerInProgress` — `variation-b-extra.jsx`)
- **Purpose:** Shown while a summary is generating.
- **Layout:** Same shell as the result, but:
  - Top status pill in composer card: pulsing accent dot + "elapsed 0:38 · ~0:50 remaining".
  - Summary card header tag reads "streaming…".
  - Left section nav uses three states per item: completed (green check), in-progress (pulsing accent dot, accent-soft background), pending (muted bullet).
  - Content area shows already-completed sections in full + an in-progress section with skeleton lines.
- **Behavior:** Server streams JSON sections. On each completed section, advance the nav state. On error, swap the in-progress dot for a red exclamation and show a retry button.

### 8. Jargon Simplifier (`B_Jargon` — `variation-b.jsx`)
- **Purpose:** Rewrite clinical text at one of five reading levels.
- **Layout:** Single full-width card, two stacked sections.
  - **Top strip:** "Reading level" label + 5 equal-width buttons (L1 Psychologist · L2 Educator · L3 Parent[default] · L4 High school · L5 Elementary). Active level uses solid accent fill + white text.
  - **Body:** 50/50 split.
    - Left (clinical input): label "Clinical input" + textarea + footer with character counter and "or upload PDF" link. Primary "Simplify at Level N" button below (full-width).
    - Right (output, secondary background): label + accent tag for level + plain "FK 7.1" tag for Flesch-Kincaid score. Body text below at 14px/1.7 line-height. Footer with Copy / "Try another level" actions.
- **Behavior:** Selecting a level **after** a result has been generated replaces the right-side output (don't append). Input is never stored beyond a 200-character preview (display this in the privacy footer of the result, e.g. as a tooltip or muted line).

### 9. History (`B_History` — `variation-b-extra.jsx`)
- **Purpose:** Per-project activity log.
- **Layout:** Page header + filter segmented control (All / Q&A / Summaries / Jargon) + Export button. Body: 2-column grid of activity cards. Each card: kind tag + title (bold), excerpt paragraph (muted, 1.55 line-height), footer row "23 min ago · meta · Open button".
- **Behavior:** Open routes to the originating thread/summary/jargon run. Export downloads a JSON of the filtered set.

### 10. Delete Document Confirm (`B_DeleteConfirm` — `variation-b-extra.jsx`)
- **Purpose:** Hard-delete confirmation modal (FERPA-required).
- **Layout:** Modal (440px) over blurred Documents view. Title "Delete eval_2024_REDACTED.pdf?". Lead paragraph explaining what happens to chunks and citations. Inline danger callout with shield icon: "Hard-delete · cannot be undone · required by FERPA." Cancel / Delete-permanently (red) actions.
- **Behavior:** Delete button is enabled by default in this variation (no type-to-confirm). On confirm → DELETE request → toast "Document deleted" + return to Documents list.

## Interactions & Behavior

### Navigation Model
- **Global:** Sign-in → Workspace landing (no project) OR last-active project.
- **Project rail (264px, persistent on left):**
  - Brand header.
  - "+ New project" button.
  - Recent projects list (max 5 + "Load more").
  - When a project is active and the workspace is in Q&A mode, a "Threads in {project}" sub-section appears with the project's threads + "+ New thread".
  - Footer: trust pills + user row with sign-out.
- **Workspace top bar (48px):** Breadcrumbs on the left, tool switcher segmented control on the right (in B, the tool switcher lives in the top bar — there is no separate tabs row).

### Citation UX (B-specific)
- Numbered references **do not** appear inline in assistant prose. Instead, the assistant message footer says "Cited N sources →" and the right-hand Sources panel lists them in order with snippet quotes.
- Hover-sync: hovering a numbered span (rendered as a subtle underline on the cited claim) highlights the matching citation card in the side panel. Clicking jumps to it.

### Tool Switching
- The segmented control in the top bar (Folder/Overview, Message/Q&A, FileText/Summarize, Languages/Simplify, History) is the canonical way to switch tools within a project.
- Active state: white background pill on the secondary-tinted control. The accent-filled variant of the control is used **only** in the welcome composer (the "Ask / Summarize / Simplify" picker).

### Loading States
- **Chat:** assistant bubble shows a typing indicator (3-dot pulse) until the first token streams in; subsequent content streams character-by-character.
- **Summarizer:** dedicated in-progress screen (#7).
- **Jargon:** primary button shows inline spinner + "Simplifying…" text; result panel shows skeleton lines.
- **PDF upload:** progress bar in upload chip; gateway-side PII detection swap to the Review screen on completion.

### Error/Empty States
- **Empty project:** When a project has no documents, the workspace shows an upload-CTA card centered in the content area: "Upload your first document to start asking questions."
- **No threads:** "Start a thread from the composer" message in place of the threads list.
- **Network error:** Toast top-right with retry action.
- **Session expired:** Modal blocking interaction with the workspace (already designed in Variation A — `A_SessionExpired` is a good reference; reuse the toast pattern in B as well).

### Form Validation (Create Project)
- Reject any case label containing:
  - Two consecutive capitalized words (heuristic for first/last name)
  - Date patterns (`MM/DD/YYYY`, `M/D/YY`, `YYYY-MM-DD`)
  - Numeric runs of 6+ digits
- Show error inline below the input with the same icon + text from the design.

### Responsive Behavior
- The mocks are sized at 1280×820. Real implementation should:
  - Collapse the project rail to icon-only at <1100px (with a hamburger reveal).
  - Stack the PII Review side-by-side panels vertically at <900px.
  - Collapse the chat Sources side panel into a bottom sheet at <900px.

## State Management

Per the project plan, use **Zustand** for client UI state and **TanStack Query** for server state.

### Zustand slices
- `useAuthStore` — `{ token, user, expiresAt, signIn(), signOut() }`
- `useProjectStore` — `{ activeProjectId, recentProjects, setActiveProject() }`
- `useComposerStore` — `{ tool: 'ask' | 'summarize' | 'simplify', draft: string, attachedDoc?: DocId, setTool(), setDraft() }`
- `useSidePanelStore` — `{ openCitationId, hoveredClaimId, setHoveredClaim() }` (drives the chat sources hover-sync)

### TanStack Query keys
- `['projects']` — list
- `['project', id]` — single project + its docs/threads
- `['thread', threadId, 'messages']` — paginated, with optimistic append on send
- `['document', docId, 'pii']` — PII detection result for the review screen
- `['summary', docId]` — cached generated summary
- `['history', projectId, filter]` — activity log

## Design Tokens

All values live in `reference/styles.css` under `:root`. Map them into your `tailwind.config.ts` extensions.

### Colors
| Token | Hex | Tailwind suggestion |
|---|---|---|
| `--bg-primary` | `#FFFFFF` | `background` |
| `--bg-secondary` | `#F7F7F8` | `muted` |
| `--bg-tertiary` | `#ECECEC` | `muted-foreground/10` |
| `--border` | `#E5E5E5` | `border` |
| `--border-strong` | `#D1D5DB` | `border-strong` (custom) |
| `--text-primary` | `#1F1F1F` | `foreground` |
| `--text-secondary` | `#6E6E80` | `muted-foreground` |
| `--text-muted` | `#9CA3AF` | `muted-foreground/70` |
| `--accent` | `#0F766E` | `primary` (teal) |
| `--accent-hover` | `#0D5F58` | `primary` hover |
| `--accent-soft` | `#E6F4F1` | `primary/10` |
| `--danger` | `#B91C1C` | `destructive` |
| `--danger-soft` | `#FEF2F2` | `destructive/10` |
| `--success` | `#15803D` | `success` (custom) |
| `--success-soft` | `#ECFDF5` | `success/10` |
| `--warning` | `#B45309` | `warning` (custom) |
| `--warning-soft` | `#FFFBEB` | `warning/10` |

### Border accents (one-offs in the mocks — formalize)
| Use | Hex |
|---|---|
| Accent pill border | `#B5E3DA` |
| Success pill border | `#D1FADF` |
| Warning pill border | `#FDE68A` |
| Danger pill border | `#FECACA` |

### Typography
- **Sans:** `ui-sans-serif, system-ui, -apple-system, "Segoe UI", "Helvetica Neue", Arial, sans-serif`
- **Mono:** `ui-monospace, "SF Mono", Menlo, Consolas, monospace`
- **Base:** 14px / 1.5
- **Scale used:** 10.5 (tiny pill), 11 (eyebrow), 11.5–12 (helper/meta), 12.5 (small), 13–13.5 (body small), 14 (body), 14.5 (button), 15 (chat body), 16 (modal heading), 19–22 (page heading), 26–28 (welcome headline)
- **Headings:** 600 weight, `letter-spacing: -0.015em` (smaller) → `-0.02em` (welcome).
- **Numbers in score blocks:** mono, 12px.

### Radii
| Token | Value |
|---|---|
| `--radius-sm` | 6px |
| `--radius-md` | 8px (buttons, inputs) |
| `--radius-lg` | 10px (icon tiles) |
| `--radius-xl` | 12px (cards) |
| `--radius-2xl` | 16px (composer, login card) |

### Spacing (commonly used px values from the mocks)
- Inline gaps: 4, 6, 8, 10, 12
- Card padding: 14, 16, 18, 22
- Page padding: 24×28
- Topbar height: 48
- Project rail width: 264

### Shadows
The mocks lean on borders rather than shadows. The few in use:
- Composer + login card: `0 1px 2px rgba(0,0,0,0.03)`
- Active segmented button: `0 1px 2px rgba(0,0,0,0.06)`
- Modal: `0 20px 40px rgba(15,23,42,0.18)`
- Toast: `0 12px 24px rgba(15,23,42,0.18)`

## Components (translation guide → shadcn/ui)

| Mock element | shadcn primitive | Notes |
|---|---|---|
| `.composer` | Custom (Card + Textarea + Button row) | Wrap shadcn `Textarea` (auto-resize) + custom toolbar |
| `.seg` / `.seg.accent` | `ToggleGroup` (single) | Accent variant uses `data-state=on` background = primary |
| `.tab` | `Tabs` | Underline variant (not the pill default) |
| `.rail-item` | Custom button | Use `Button variant="ghost"` + state styling |
| `.modal` | `Dialog` | All modals (CreateProject, DeleteConfirm) |
| `.tag` / `.trust-pill` | `Badge` | Variants: `default`, `accent`, `warn`, `success` |
| `.cite-chip` | Custom | Inline numbered chip with mono filename |
| `.input` / `.textarea` | `Input` / `Textarea` | Match focus ring: 3px accent-soft |
| `.btn.primary` | `Button` (default) | Primary = teal |
| `.btn.danger` | `Button variant="destructive"` | |
| `.icon-btn` | `Button variant="ghost" size="icon"` | |
| `.kbd` | `<kbd>` styled | Match border + bg-secondary |
| Page header | Custom | h1 + subtitle pattern |
| Citation side panel | `ScrollArea` + custom card list | |
| PII review side-by-side | Two `Card`s with internal `ScrollArea` | |
| Activity timeline / history | Custom card grid | |

### Icons
The mocks use a hand-rolled inline SVG icon set defined in `reference/icons.jsx`. **Use `lucide-react` instead** — every icon used has a direct lucide equivalent (`Plus`, `Folder`, `MessageSquare` for `Message`, `FileText`, `Languages`, `Clock`, `ShieldCheck`, `Server`, `WifiOff`, `LogOut`, `Upload`, `Search`, `Send`, `Settings`, `Check`, `X`, `ChevronDown`, `ChevronRight`, `Trash2` for `Trash`, `Copy`, `AlertTriangle`, `EyeOff`, `ArrowRight`, `Sparkles` for `Sparkle`, `History`, `Hash`, `Lock`).

## API Integration

Refer to the existing backend OpenAPI spec. Key endpoints the frontend calls (per the context pack):

- `POST /auth/login` → `{ token, expiresAt, user }`
- `GET /projects` → list
- `POST /projects` → create (body validated client-side first)
- `POST /documents/upload` → returns upload session ID
- `GET /documents/upload/:sessionId/pii` → PII detection result for the Review screen
- `POST /documents/ingest` → confirm + ingest
- `DELETE /documents/:docId` → hard delete
- `POST /threads/:threadId/messages` (SSE) → streams assistant response with `[citation]` events
- `POST /summaries` (SSE) → streams structured summary sections
- `POST /jargon` → synchronous, returns rewrite + Flesch-Kincaid score
- `GET /projects/:id/history?type=…` → paginated activity log

All requests include `Authorization: Bearer <token>` and respect the 8h session TTL — on 401, surface the session-expired pattern.

## Demo Script (acceptance flow)

The implementation is correct if a stakeholder can click through this end-to-end without intervention:

1. **Sign in** as `dr.lee`.
2. Land on the workspace welcome composer.
3. **Create a new project** "Case 2026-014" (verify the live PII validation green-check).
4. **Try to type** "John Doe DOB 01/15/2012" first — verify the validation blocks it.
5. **Upload** `eval_2024_REDACTED.pdf` (or sample) → land on the **PII Review** side-by-side screen → confirm.
6. From the project workspace, switch tool to **Q&A** → ask "What were the WISC-V composite scores?" → verify streaming response + side-panel citations with snippet quotes → hover a claim → verify citation card highlights.
7. Switch tool to **Summarize** → click Generate → verify in-progress screen with section-nav state transitions → land on the result.
8. Switch tool to **Simplify** → paste clinical text → choose Level 3 → verify rewrite + FK score appears in the right pane.
9. Open **History** → verify all four runs above are listed → click one → verify it routes back to the originating screen.
10. From Documents → **Delete** the uploaded doc → confirm in modal → verify it's removed.

## Files in `reference/`

- `SecurePsych Explorations.html` — the canvas containing all variations (B is the middle column)
- `styles.css` — tokens + utility classes used across all mocks
- `icons.jsx` — inline SVG icon set (use lucide-react instead in implementation)
- `shared.jsx` — `ProjectRail`, `TopBar`, `Tabs`, `TrustPills` shared primitives
- `variation-b.jsx` — Login, Dashboard, PII Review, Chat, Summarizer, Jargon
- `variation-b-extra.jsx` — Create Project modal, History, Delete Confirm modal, Summarizer in-progress

## Notes for the Implementer

- **Read the existing project plan and context pack first** (the user has these as `SECUREPSYCH_FE_CONTEXT.md` and `SECUREPSYCH_FE_PLAN.md`). The plan defines the stack (Vite + React + TS + Tailwind + shadcn/ui + Zustand + TanStack Query), the security model, the demo script, and the API contract. The mocks are the visual spec; the plan is the architectural spec.
- **Don't ship the inline styles** from the JSX. They were used for prototyping speed; map every value to a Tailwind utility or a token variable.
- **Pay special attention to the PII gateway language** — the validation copy and the privacy callouts on Create Project, PII Review, and Jargon are not decorative; they're part of the FERPA story. Preserve copy verbatim unless legal explicitly approves a change.
- **Streaming UX matters** — the chat and summarizer both stream from the backend. Build the components to render incrementally rather than wait for completion.

---

## Implementation status (May 3, 2026)

This handoff is **implemented in `frontend/`** as of the May 3 demo prep. For a full screen-to-file map, run/test instructions, and the design decisions made along the way, see [`docs/jumpstart/FRONTEND_DEV.md`](../../jumpstart/FRONTEND_DEV.md).

Quick map:

| Screen | File |
|---|---|
| Sign-in | [`frontend/src/components/auth/LoginForm.tsx`](../../../frontend/src/components/auth/LoginForm.tsx) |
| Workspace landing | [`frontend/src/pages/DashboardPage.tsx`](../../../frontend/src/pages/DashboardPage.tsx) |
| Create Project | [`frontend/src/components/projects/CreateProjectDialog.tsx`](../../../frontend/src/components/projects/CreateProjectDialog.tsx) |
| PII Redaction Review | [`frontend/src/components/upload/PIIReviewPanel.tsx`](../../../frontend/src/components/upload/PIIReviewPanel.tsx) |
| RAG Q&A | [`frontend/src/pages/ProjectChatPage.tsx`](../../../frontend/src/pages/ProjectChatPage.tsx) |
| Document Summarizer | [`frontend/src/pages/ProjectSummarizerPage.tsx`](../../../frontend/src/pages/ProjectSummarizerPage.tsx) |
| Jargon Simplifier | [`frontend/src/pages/ProjectJargonPage.tsx`](../../../frontend/src/pages/ProjectJargonPage.tsx) |
| History | [`frontend/src/pages/ProjectHistoryPage.tsx`](../../../frontend/src/pages/ProjectHistoryPage.tsx) |
| Delete Document confirm | inline `Dialog` in `ProjectChatPage.tsx` |

**Deliberate scope reductions (signed off for the May 4 demo):**
- Citations render as numbered footnotes under the assistant message, not the right-hand side panel with hover-sync. Hover-sync is post-demo polish.
- The PII Review panel does **not** show the "5 entities · 46 occurrences across 24 pages" copy — the gateway's `entity_map` doesn't return per-entity counts.
- Streaming (SSE) is **not** implemented; sync only, per `SECUREPSYCH_FE_CONTEXT.md` §14.

**Backend patches that landed alongside the frontend:** see [`docs/troubleshooting/dev-env-fixes.md`](../../troubleshooting/dev-env-fixes.md). Three fixes, all surgical, none change production behavior.
