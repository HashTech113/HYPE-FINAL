import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";

import { getRouter } from "./router";
import "./styles.css";

const router = getRouter();
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      // 30 s stale window dedupes the refetch storm that used to fire on
      // every route change (staleTime: 0 made each remount refetch).
      // Queries with their own ``refetchInterval`` (cameras health,
      // detections) still poll on schedule — they just don't trigger an
      // extra fetch on remount when data is fresh.
      staleTime: 30_000,
      retry: 1,
    },
  },
});

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof getRouter>;
  }
}

const rootEl = document.getElementById("app");
if (!rootEl) throw new Error("#app element not found");

createRoot(rootEl).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <Toaster position="bottom-right" richColors closeButton />
    </QueryClientProvider>
  </StrictMode>,
);
