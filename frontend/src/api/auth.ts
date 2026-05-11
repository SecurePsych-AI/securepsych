import { apiFetch } from "@/api/client";
import type { AuthLoginRequest, AuthLoginResponse } from "@/types/api";

export const authApi = {
  login: (req: AuthLoginRequest) =>
    apiFetch<AuthLoginResponse>("/api/auth/login", {
      method: "POST",
      json: req,
    }),

  logout: (token: string) =>
    apiFetch<{ status: string; detail: string }>("/api/auth/logout", {
      method: "POST",
      json: { token },
    }),
};
