import { apiFetch } from "@/api/client";
import type {
  CreateProjectRequest,
  JargonRun,
  Project,
  SummaryRun,
  Thread,
  UploadedFile,
  UUID,
} from "@/types/api";

export const projectsApi = {
  list: () => apiFetch<Project[]>("/api/projects"),
  get: (id: UUID) => apiFetch<Project>(`/api/projects/${id}`),
  create: (req: CreateProjectRequest) =>
    apiFetch<Project>("/api/projects", { method: "POST", json: req }),
  files: (id: UUID) => apiFetch<UploadedFile[]>(`/api/projects/${id}/files`),
  threads: (id: UUID) => apiFetch<Thread[]>(`/api/projects/${id}/threads`),
  thread: (id: UUID, threadId: UUID) =>
    apiFetch<Thread>(`/api/projects/${id}/threads/${threadId}`),
  summaries: (id: UUID) =>
    apiFetch<SummaryRun[]>(`/api/projects/${id}/summaries`),
  jargonRuns: (id: UUID) =>
    apiFetch<JargonRun[]>(`/api/projects/${id}/jargon-runs`),
};
