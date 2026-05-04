import { apiFetch } from "@/api/client";
import type { FeatureFlags } from "@/types/api";

export const systemApi = {
  health: () => apiFetch<{ status: string; service: string }>("/health"),
  config: () => apiFetch<FeatureFlags>("/api/config"),
};
