import { useAuthStore } from "@/store/auth";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) {
    super(`HTTP ${status}`);
  }
}

export interface ApiFetchInit extends Omit<RequestInit, "body"> {
  json?: unknown;
  body?: BodyInit | null;
  query?: Record<string, string | number | undefined>;
}

function buildUrl(path: string, query?: ApiFetchInit["query"]): string {
  const url = new URL(path, BASE);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null && v !== "") {
        url.searchParams.set(k, String(v));
      }
    }
  }
  return url.toString();
}

export async function apiFetch<T = unknown>(
  path: string,
  init: ApiFetchInit = {},
): Promise<T> {
  const { json, query, headers: initHeaders, body: initBody, ...rest } = init;
  const token = useAuthStore.getState().token;
  const headers = new Headers(initHeaders);

  if (token) headers.set("Authorization", `Bearer ${token}`);

  let body: BodyInit | null | undefined = initBody;
  if (json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(json);
  }

  const url = buildUrl(path, query);
  const res = await fetch(url, { ...rest, headers, body });

  if (res.status === 401) {
    useAuthStore.getState().clear();
    if (!window.location.pathname.startsWith("/login")) {
      window.location.assign("/login?expired=1");
    }
    throw new ApiError(401, { detail: "Session expired" });
  }

  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) {
    return (await res.json()) as T;
  }
  return (await res.text()) as unknown as T;
}

export function apiErrorMessage(err: unknown, fallback = "Something went wrong."): string {
  if (err instanceof ApiError) {
    const d = (err.detail as { detail?: unknown } | undefined)?.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d) && d[0]?.msg) return String(d[0].msg);
  }
  if (err instanceof Error) return err.message;
  return fallback;
}
