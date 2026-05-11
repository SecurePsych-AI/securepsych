import { useQuery } from "@tanstack/react-query";
import { systemApi } from "@/api/system";
import type { FeatureFlags } from "@/types/api";

export function useFeatureFlags() {
  return useQuery<FeatureFlags>({
    queryKey: ["system", "config"],
    queryFn: () => systemApi.config(),
    staleTime: Infinity,
  });
}
