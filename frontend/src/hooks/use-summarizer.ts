import { useMutation, useQueryClient } from "@tanstack/react-query";

import { summarizerApi } from "@/api/summarizer";
import type { SummarizeJsonRequest, SummarizeResponse, UUID } from "@/types/api";

export function useSummarizeFromDocument() {
  const qc = useQueryClient();
  return useMutation<SummarizeResponse, unknown, SummarizeJsonRequest>({
    mutationFn: (req) => summarizerApi.fromDocument(req),
    onSuccess: (_data, vars) => {
      if (vars.project_id) {
        qc.invalidateQueries({
          queryKey: ["projects", vars.project_id, "summaries"],
        });
      }
    },
  });
}

interface FromFileArgs {
  file: File;
  projectId?: UUID;
}

export function useSummarizeFromFile() {
  const qc = useQueryClient();
  return useMutation<SummarizeResponse, unknown, FromFileArgs>({
    mutationFn: (a) => summarizerApi.fromFile(a.file, a.projectId),
    onSuccess: (_data, vars) => {
      if (vars.projectId) {
        qc.invalidateQueries({
          queryKey: ["projects", vars.projectId, "summaries"],
        });
      }
    },
  });
}
