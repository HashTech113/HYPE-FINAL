"use client";

// Top-of-tree error boundary. ONLY catches errors that escape the
// root `layout.tsx` itself — e.g. a crash inside the `<Providers>`
// component, or in metadata generation. Must render its OWN
// <html>/<body> because the app's root layout is what threw.
//
// Without this, Next.js shows a hard-coded fallback that says
// "Application error: a client-side exception has occurred" with no
// actionable detail and no recovery button.

import { useEffect } from "react";

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("Root-level render crash:", error);
  }, [error]);

  return (
    <html>
      <body
        style={{
          margin: 0,
          padding: 24,
          fontFamily:
            "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
          background: "#0b0b0c",
          color: "#fff",
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div style={{ maxWidth: 480 }}>
          <h1 style={{ fontSize: 18, marginBottom: 8 }}>
            The application crashed
          </h1>
          <p style={{ color: "#aaa", fontSize: 14, marginBottom: 16 }}>
            A top-level error prevented the app from rendering. Your
            data on the server is unaffected.
          </p>
          <pre
            style={{
              background: "#1a1a1c",
              border: "1px solid #2a2a2e",
              padding: 12,
              fontSize: 12,
              borderRadius: 6,
              overflow: "auto",
              maxHeight: 200,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            {error.message || "Unknown error"}
            {error.digest ? `\n\nRef: ${error.digest}` : ""}
          </pre>
          <button
            type="button"
            onClick={reset}
            style={{
              marginTop: 12,
              padding: "8px 14px",
              background: "#2563eb",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              cursor: "pointer",
              fontSize: 14,
            }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
