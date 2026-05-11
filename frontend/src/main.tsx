import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "@/App";
import "@/index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: (failureCount, error: unknown) => {
        const status = (error as { status?: number } | null)?.status;
        if (status && status >= 400 && status < 500) return false;
        return failureCount < 1;
      },
      staleTime: 30_000,
    },
    mutations: { retry: false },
  },
});

async function bootstrap() {
  if (import.meta.env.VITE_USE_MOCKS === "true") {
    const { worker } = await import("@/mocks/browser");
    const startWorker = () =>
      worker.start({ onUnhandledRequest: "bypass", quiet: true });
    await startWorker();
    // The browser can idle out the service worker, which silently drops MSW's
    // handler subscription. Re-bind whenever the tab becomes visible again so
    // mocked responses keep flowing without a manual page refresh.
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "visible") {
        void startWorker().catch(() => {
          /* idempotent — ignore re-bind errors */
        });
      }
    });
  } else if ("serviceWorker" in navigator) {
    // Live-backend mode: tear down any leftover MSW worker from a prior mock
    // session, otherwise it would silently intercept real-backend requests.
    const reg = await navigator.serviceWorker.getRegistration();
    if (reg) await reg.unregister();
  }

  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </React.StrictMode>,
  );
}

bootstrap();
