import { http, HttpResponse, delay } from "msw";

import { detectPiiInLabel } from "@/lib/ferpa";
import type {
  AuthLoginResponse,
  FeatureFlags,
  JargonLevel,
  JargonResponse,
  Project,
  RagPreviewResponse,
  RagQueryRequest,
  RagQueryResponse,
  RagUploadResponse,
  SummarizeResponse,
} from "@/types/api";

import {
  JARGON_BY_LEVEL,
  SAMPLE_CITATIONS,
  SAMPLE_PREVIEW,
  SAMPLE_RAG_ANSWER,
  SAMPLE_SUMMARY,
  SAMPLE_UPLOAD,
} from "@/mocks/data/seed";
import {
  addFile,
  addJargonRun,
  addSummary,
  appendUserAndAssistantMessages,
  createProject,
  deleteFile,
  getJargonRuns,
  getProjectFiles,
  getSummaries,
  getThread,
  getThreads,
  listAllDocuments,
  makeJargonRun,
  makeSummary,
  mockState,
} from "@/mocks/store";

const BASE = "http://localhost:8000";
const url = (p: string) => `${BASE}${p}`;

const FEATURE_FLAGS: FeatureFlags = {
  rag_enabled: true,
  summarizer_enabled: true,
  jargon_enabled: true,
};

export const handlers = [
  // ── System ────────────────────────────────────────────────────────────────
  http.get(url("/health"), () =>
    HttpResponse.json({ status: "ok", service: "gateway" }),
  ),

  http.get(url("/api/config"), () => HttpResponse.json(FEATURE_FLAGS)),

  // ── Auth ──────────────────────────────────────────────────────────────────
  http.post(url("/api/auth/login"), async ({ request }) => {
    const body = (await request.json()) as { username?: string; password?: string };
    if (!body?.username || !body?.password) {
      return HttpResponse.json({ detail: "Invalid credentials" }, { status: 401 });
    }
    await delay(180);
    const res: AuthLoginResponse = {
      access_token: `mock.${btoa(body.username)}.token`,
      token_type: "bearer",
    };
    return HttpResponse.json(res);
  }),

  http.post(url("/api/auth/logout"), async () =>
    HttpResponse.json({ status: "ok", detail: "Token added to denylist" }),
  ),

  // ── Projects ──────────────────────────────────────────────────────────────
  http.get(url("/api/projects"), async () => {
    await delay(80);
    return HttpResponse.json(mockState.projects);
  }),

  http.post(url("/api/projects"), async ({ request }) => {
    const body = (await request.json()) as {
      display_label?: string;
      student_id?: string;
    };
    const label = body?.display_label ?? "";
    const check = detectPiiInLabel(label);
    if (!check.ok) {
      return HttpResponse.json(
        { detail: check.reason },
        { status: 422 },
      );
    }
    await delay(120);
    const created: Project = createProject(label.trim());
    return HttpResponse.json(created, { status: 201 });
  }),

  http.get(url("/api/projects/:projectId"), ({ params }) => {
    const project = mockState.projects.find((p) => p.id === params.projectId);
    if (!project) {
      return HttpResponse.json({ detail: "Not found" }, { status: 404 });
    }
    return HttpResponse.json(project);
  }),

  http.get(url("/api/projects/:projectId/files"), ({ params }) =>
    HttpResponse.json(getProjectFiles(params.projectId as string)),
  ),

  http.get(url("/api/projects/:projectId/threads"), ({ params }) =>
    HttpResponse.json(getThreads(params.projectId as string)),
  ),

  http.get(url("/api/projects/:projectId/threads/:threadId"), ({ params }) => {
    const thread = getThread(params.threadId as string);
    if (!thread) return HttpResponse.json({ detail: "Not found" }, { status: 404 });
    return HttpResponse.json(thread);
  }),

  http.get(url("/api/projects/:projectId/summaries"), ({ params }) =>
    HttpResponse.json(getSummaries(params.projectId as string)),
  ),

  http.get(url("/api/projects/:projectId/jargon-runs"), ({ params }) =>
    HttpResponse.json(getJargonRuns(params.projectId as string)),
  ),

  // ── RAG ───────────────────────────────────────────────────────────────────
  http.post(url("/api/rag/upload/preview"), async () => {
    await delay(420);
    const res: RagPreviewResponse = SAMPLE_PREVIEW;
    return HttpResponse.json(res);
  }),

  http.post(url("/api/rag/upload"), async ({ request }) => {
    const fd = await request.formData().catch(() => null);
    const projectId = (fd?.get("project_id") as string | null) ?? null;
    if (!projectId) {
      return HttpResponse.json({ detail: "project_id is required" }, { status: 422 });
    }
    await delay(900);
    const res: RagUploadResponse = SAMPLE_UPLOAD;
    addFile(projectId, {
      id: crypto.randomUUID(),
      document_id: res.document_id,
      filename_redacted: res.source,
      strategy: res.strategy,
      chunks_added: res.chunks_added,
      uploaded_at: new Date().toISOString(),
    });
    return HttpResponse.json(res);
  }),

  http.post(url("/api/rag/query"), async ({ request }) => {
    const body = (await request.json()) as RagQueryRequest;
    await delay(700);
    const { threadId } = appendUserAndAssistantMessages({
      projectId: body.project_id,
      threadId: body.thread_id,
      question: body.question,
      answer: SAMPLE_RAG_ANSWER,
      sources: SAMPLE_CITATIONS.slice(0, body.mode === "deep" ? 3 : 2),
    });
    const res: RagQueryResponse = {
      answer: SAMPLE_RAG_ANSWER,
      mode: body.mode ?? "fast",
      top_k: body.top_k ?? 3,
      thread_id: threadId,
      sources: SAMPLE_CITATIONS.slice(0, body.mode === "deep" ? 3 : 2),
    };
    return HttpResponse.json(res);
  }),

  http.get(url("/api/rag/documents"), ({ request }) => {
    const u = new URL(request.url);
    const projectId = u.searchParams.get("project_id");
    if (!projectId) return HttpResponse.json({ detail: "project_id is required" }, { status: 422 });
    return HttpResponse.json(listAllDocuments(projectId));
  }),

  http.delete(url("/api/rag/documents/:documentId"), async ({ params, request }) => {
    const u = new URL(request.url);
    const projectId = u.searchParams.get("project_id");
    if (!projectId) return HttpResponse.json({ detail: "project_id is required" }, { status: 422 });
    await delay(220);
    const removed = deleteFile(projectId, params.documentId as string);
    if (!removed) return HttpResponse.json({ detail: "Not found" }, { status: 404 });
    return HttpResponse.json({
      deleted: true,
      document_id: removed.document_id,
      filename: removed.filename_redacted,
      chunks_removed: removed.chunks_added,
    });
  }),

  // ── Summarizer ────────────────────────────────────────────────────────────
  http.post(url("/api/summarize"), async ({ request }) => {
    const ct = request.headers.get("content-type") ?? "";
    let projectId: string | null = null;
    let documentId: string | null = null;
    if (ct.includes("application/json")) {
      const body = (await request.json()) as { document_id?: string; project_id?: string };
      documentId = body.document_id ?? null;
      projectId = body.project_id ?? null;
    } else {
      const fd = await request.formData();
      projectId = (fd.get("project_id") as string | null) ?? null;
    }
    await delay(1500);
    const res: SummarizeResponse = {
      summary: SAMPLE_SUMMARY.summary,
      page_count: SAMPLE_SUMMARY.page_count,
    };
    if (projectId) {
      addSummary(
        projectId,
        makeSummary(documentId ?? SAMPLE_SUMMARY.document_id, res.summary, res.page_count),
      );
    }
    return HttpResponse.json(res);
  }),

  // ── Jargon ────────────────────────────────────────────────────────────────
  http.post(url("/api/jargon/simplify"), async ({ request }) => {
    const ct = request.headers.get("content-type") ?? "";
    let level: JargonLevel = 3;
    let text = "";
    let projectId: string | null = null;
    if (ct.includes("application/json")) {
      const body = (await request.json()) as {
        text?: string;
        level?: JargonLevel;
        project_id?: string;
      };
      level = (body.level ?? 3) as JargonLevel;
      text = body.text ?? "";
      projectId = body.project_id ?? null;
    } else {
      const fd = await request.formData();
      level = (Number(fd.get("level") ?? 3) as JargonLevel) ?? 3;
      text = (fd.get("text") as string | null) ?? "";
      projectId = (fd.get("project_id") as string | null) ?? null;
    }
    await delay(650);
    const sample = JARGON_BY_LEVEL[level] ?? JARGON_BY_LEVEL[3];
    const res: JargonResponse = {
      simplified_text: sample.simplified_text,
      flesch_kincaid_grade: sample.flesch_kincaid_grade,
      level,
    };
    if (projectId) {
      addJargonRun(
        projectId,
        makeJargonRun(level, text, sample.simplified_text, sample.flesch_kincaid_grade),
      );
    }
    return HttpResponse.json(res);
  }),
];
