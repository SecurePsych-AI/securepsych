import { useMutation, useQueryClient } from "@tanstack/react-query";

import { ragApi } from "@/api/rag";
import type {
  RagPreviewResponse,
  RagQueryRequest,
  RagQueryResponse,
  RagUploadResponse,
  UUID,
} from "@/types/api";

export function useRagPreview() {
  return useMutation<RagPreviewResponse, unknown, File>({
    mutationFn: (file) => ragApi.preview(file),
  });
}

interface CommitArgs {
  previewToken: string;
  projectId: UUID;
  strategy?: "standard" | "deep";
}

export function useRagCommit() {
  const qc = useQueryClient();
  return useMutation<RagUploadResponse, unknown, CommitArgs>({
    mutationFn: (a) =>
      ragApi.upload({
        previewToken: a.previewToken,
        projectId: a.projectId,
        strategy: a.strategy,
      }),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ["projects", vars.projectId, "files"] });
      qc.invalidateQueries({ queryKey: ["rag", "documents", vars.projectId] });
    },
  });
}

export function useRagQuery() {
  const qc = useQueryClient();
  return useMutation<RagQueryResponse, unknown, RagQueryRequest>({
    mutationFn: (req) => ragApi.query(req),
    onSuccess: (_res, req) => {
      qc.invalidateQueries({ queryKey: ["projects", req.project_id, "threads"] });
      if (_res.thread_id) {
        qc.invalidateQueries({
          queryKey: ["projects", req.project_id, "threads", _res.thread_id],
        });
      }
    },
  });
}

interface DeleteArgs {
  documentId: UUID;
  projectId: UUID;
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (a: DeleteArgs) =>
      ragApi.deleteDocument(a.documentId, a.projectId),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ["projects", vars.projectId, "files"] });
      qc.invalidateQueries({ queryKey: ["rag", "documents", vars.projectId] });
    },
  });
}
