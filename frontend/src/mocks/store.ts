import type {
  ChatMessage,
  JargonLevel,
  JargonRun,
  Project,
  SummaryRun,
  Thread,
  UploadedFile,
  UUID,
} from "@/types/api";
import {
  DOCUMENT_ID,
  FILE_A,
  PROJECT_A,
  PROJECT_B,
  SAMPLE_CITATIONS,
  SAMPLE_JARGON_INPUT_PREVIEW,
  SAMPLE_RAG_ANSWER,
  SAMPLE_SUMMARY,
  THREAD_A,
} from "@/mocks/data/seed";

interface MockState {
  projects: Project[];
  files: Map<UUID, UploadedFile[]>;
  threads: Map<UUID, Thread[]>;
  threadMessages: Map<UUID, ChatMessage[]>;
  summaries: Map<UUID, SummaryRun[]>;
  jargonRuns: Map<UUID, JargonRun[]>;
}

function nowIso(): string {
  return new Date().toISOString();
}

function uuid(): string {
  return crypto.randomUUID();
}

const initialThreadMessages: ChatMessage[] = [
  {
    id: uuid(),
    role: "user",
    content: "What were the WISC-V composite scores?",
    sources: [],
    created_at: THREAD_A.created_at,
  },
  {
    id: uuid(),
    role: "assistant",
    content: SAMPLE_RAG_ANSWER,
    sources: SAMPLE_CITATIONS.slice(0, 2),
    created_at: THREAD_A.created_at,
  },
];

const initialJargonRun: JargonRun = {
  id: uuid(),
  level: 3,
  input_preview: SAMPLE_JARGON_INPUT_PREVIEW,
  simplified_text:
    "The testing showed that your child has difficulty with the sound-based building blocks of reading — things like remembering the sounds in words and recognizing how words break into smaller sound parts.",
  fk_grade: 7.1,
  created_at: "2026-04-30T15:10:45.000000+00:00",
};

export const mockState: MockState = {
  projects: [PROJECT_A, PROJECT_B],
  files: new Map([[PROJECT_A.id, [FILE_A]]]),
  threads: new Map([[PROJECT_A.id, [THREAD_A]]]),
  threadMessages: new Map([[THREAD_A.id, initialThreadMessages]]),
  summaries: new Map([[PROJECT_A.id, [SAMPLE_SUMMARY]]]),
  jargonRuns: new Map([[PROJECT_A.id, [initialJargonRun]]]),
};

export function createProject(label: string): Project {
  const project: Project = {
    id: uuid(),
    display_label: label,
    created_at: nowIso(),
  };
  mockState.projects = [project, ...mockState.projects];
  return project;
}

export function getProjectFiles(projectId: UUID): UploadedFile[] {
  return mockState.files.get(projectId) ?? [];
}

export function addFile(projectId: UUID, file: UploadedFile): void {
  const existing = mockState.files.get(projectId) ?? [];
  mockState.files.set(projectId, [file, ...existing]);
}

export function deleteFile(projectId: UUID, documentId: UUID): UploadedFile | null {
  const existing = mockState.files.get(projectId) ?? [];
  const idx = existing.findIndex((f) => f.document_id === documentId);
  if (idx === -1) return null;
  const [removed] = existing.splice(idx, 1);
  mockState.files.set(projectId, [...existing]);
  return removed ?? null;
}

export function getThreads(projectId: UUID): Thread[] {
  return mockState.threads.get(projectId) ?? [];
}

export function getThread(threadId: UUID): Thread | null {
  for (const list of mockState.threads.values()) {
    const found = list.find((t) => t.id === threadId);
    if (found) {
      return { ...found, messages: mockState.threadMessages.get(threadId) ?? [] };
    }
  }
  return null;
}

export function appendUserAndAssistantMessages(args: {
  projectId: UUID;
  threadId?: UUID;
  question: string;
  answer: string;
  sources: ChatMessage["sources"];
}): { threadId: UUID } {
  let threadId = args.threadId;
  if (!threadId) {
    const newThread: Thread = {
      id: uuid(),
      title: args.question.slice(0, 60),
      created_at: nowIso(),
    };
    threadId = newThread.id;
    const list = mockState.threads.get(args.projectId) ?? [];
    mockState.threads.set(args.projectId, [newThread, ...list]);
    mockState.threadMessages.set(threadId, []);
  }
  const list = mockState.threadMessages.get(threadId) ?? [];
  const ts = nowIso();
  list.push({
    id: uuid(),
    role: "user",
    content: args.question,
    sources: [],
    created_at: ts,
  });
  list.push({
    id: uuid(),
    role: "assistant",
    content: args.answer,
    sources: args.sources,
    created_at: ts,
  });
  mockState.threadMessages.set(threadId, list);
  return { threadId };
}

export function getSummaries(projectId: UUID): SummaryRun[] {
  return mockState.summaries.get(projectId) ?? [];
}

export function addSummary(projectId: UUID, summary: SummaryRun): void {
  const existing = mockState.summaries.get(projectId) ?? [];
  mockState.summaries.set(projectId, [summary, ...existing]);
}

export function getJargonRuns(projectId: UUID): JargonRun[] {
  return mockState.jargonRuns.get(projectId) ?? [];
}

export function addJargonRun(projectId: UUID, run: JargonRun): void {
  const existing = mockState.jargonRuns.get(projectId) ?? [];
  mockState.jargonRuns.set(projectId, [run, ...existing]);
}

export function listAllDocuments(projectId: UUID) {
  const files = getProjectFiles(projectId);
  return {
    total_documents: files.length,
    documents: files.map((f) => ({
      document_id: f.document_id,
      filename: f.filename_redacted,
    })),
  };
}

export { DOCUMENT_ID };

export function makeJargonRun(
  level: JargonLevel,
  text: string,
  simplified: string,
  fk: number,
): JargonRun {
  return {
    id: uuid(),
    level,
    input_preview: text.slice(0, 200),
    simplified_text: simplified,
    fk_grade: fk,
    created_at: nowIso(),
  };
}

export function makeSummary(documentId: UUID, summary: string, pageCount: number): SummaryRun {
  return {
    id: uuid(),
    document_id: documentId,
    filename_redacted:
      mockState.files.get(PROJECT_A.id)?.find((f) => f.document_id === documentId)
        ?.filename_redacted ?? "eval_2024_REDACTED.pdf",
    summary,
    page_count: pageCount,
    created_at: nowIso(),
  };
}
