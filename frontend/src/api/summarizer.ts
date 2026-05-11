import { apiFetch } from "@/api/client";
import type {
  SummarizeJsonRequest,
  SummarizeResponse,
  UUID,
} from "@/types/api";

export const summarizerApi = {
  fromDocument: (req: SummarizeJsonRequest) =>
    apiFetch<SummarizeResponse>("/api/summarize", {
      method: "POST",
      json: req,
    }),

  fromFile: (file: File, projectId?: UUID) => {
    const fd = new FormData();
    fd.append("file", file);
    if (projectId) fd.append("project_id", projectId);
    return apiFetch<SummarizeResponse>("/api/summarize", {
      method: "POST",
      body: fd,
    });
  },
};
