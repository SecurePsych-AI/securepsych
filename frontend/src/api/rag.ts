import { apiFetch } from "@/api/client";
import type {
  RagDeleteResponse,
  RagDocumentsListResponse,
  RagPreviewResponse,
  RagQueryRequest,
  RagQueryResponse,
  RagUploadResponse,
  UUID,
} from "@/types/api";

export const ragApi = {
  preview: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return apiFetch<RagPreviewResponse>("/api/rag/upload/preview", {
      method: "POST",
      body: fd,
    });
  },

  upload: (args: {
    previewToken?: string;
    file?: File;
    projectId: UUID;
    strategy?: "standard" | "deep";
  }) => {
    const fd = new FormData();
    if (args.previewToken) fd.append("preview_token", args.previewToken);
    if (args.file) fd.append("file", args.file);
    fd.append("project_id", args.projectId);
    if (args.strategy) fd.append("strategy", args.strategy);
    return apiFetch<RagUploadResponse>("/api/rag/upload", {
      method: "POST",
      body: fd,
    });
  },

  query: (req: RagQueryRequest) =>
    apiFetch<RagQueryResponse>("/api/rag/query", {
      method: "POST",
      json: req,
    }),

  documents: (projectId: UUID) =>
    apiFetch<RagDocumentsListResponse>("/api/rag/documents", {
      query: { project_id: projectId },
    }),

  deleteDocument: (documentId: UUID, projectId: UUID) =>
    apiFetch<RagDeleteResponse>(`/api/rag/documents/${documentId}`, {
      method: "DELETE",
      query: { project_id: projectId },
    }),
};
