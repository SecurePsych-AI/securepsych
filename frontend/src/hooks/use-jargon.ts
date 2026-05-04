import { useMutation, useQueryClient } from "@tanstack/react-query";

import { jargonApi } from "@/api/jargon";
import type { JargonRequest, JargonResponse, UUID } from "@/types/api";

export function useJargon() {
  const qc = useQueryClient();
  return useMutation<JargonResponse, unknown, JargonRequest>({
    mutationFn: (req) => jargonApi.simplify(req),
    onSuccess: (_data, vars) => {
      if (vars.project_id) {
        qc.invalidateQueries({
          queryKey: ["projects", vars.project_id, "jargon-runs"],
        });
      }
    },
  });
}

interface FromFileArgs {
  file: File;
  level: number;
  projectId?: UUID;
}

export function useJargonFromFile() {
  const qc = useQueryClient();
  return useMutation<JargonResponse, unknown, FromFileArgs>({
    mutationFn: (a) => jargonApi.fromFile(a.file, a.level, a.projectId),
    onSuccess: (_data, vars) => {
      if (vars.projectId) {
        qc.invalidateQueries({
          queryKey: ["projects", vars.projectId, "jargon-runs"],
        });
      }
    },
  });
}
