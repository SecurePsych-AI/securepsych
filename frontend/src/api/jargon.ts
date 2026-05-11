import { apiFetch } from "@/api/client";
import type { JargonRequest, JargonResponse, UUID } from "@/types/api";

export const jargonApi = {
  simplify: (req: JargonRequest) =>
    apiFetch<JargonResponse>("/api/jargon/simplify", {
      method: "POST",
      json: req,
    }),

  fromFile: (file: File, level: number, projectId?: UUID) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("level", String(level));
    if (projectId) fd.append("project_id", projectId);
    return apiFetch<JargonResponse>("/api/jargon/simplify", {
      method: "POST",
      body: fd,
    });
  },
};
