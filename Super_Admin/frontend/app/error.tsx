"use client";

// Next.js App-Router segment-level error boundary. Caught here:
//  * any render exception thrown inside `(dashboard)/*` or
//    `(auth)/*` routes (i.e. anything below the root layout),
//  * uncaught errors from event handlers / hooks that re-render.
//
// The previous behaviour was a Next.js default white screen — the
// user saw nothing, the dashboard appeared dead, and there was no
// way to recover without a hard refresh. With this in place, the
// user sees a useful message + a "Try again" button that re-mounts
// the segment, and we can wire telemetry to `error.digest` if we
// add error reporting later.

import { useEffect } from "react";

import { Button } from "@/components/ui/button";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Always surface to the browser console so it shows up in
    // DevTools even after the user clicks "Try again". Ready for
    // a future replacement with Sentry/Datadog without changing
    // the call site.
    // eslint-disable-next-line no-console
    console.error("Dashboard render crash:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <div className="max-w-lg space-y-4 rounded-lg border border-destructive/40 bg-destructive/5 p-6">
        <div>
          <h1 className="text-lg font-semibold text-destructive">
            Something went wrong
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            The dashboard hit an unexpected error and couldn&apos;t finish
            rendering this page. Your data is safe — this only affects
            what you see in the browser.
          </p>
        </div>
        <details className="rounded-md border bg-background p-3 text-xs">
          <summary className="cursor-pointer font-medium">
            Technical detail
          </summary>
          <p className="mt-2 break-words font-mono">
            {error.message || "Unknown error"}
          </p>
          {error.digest && (
            <p className="mt-1 text-muted-foreground">
              Reference:{" "}
              <span className="font-mono">{error.digest}</span>
            </p>
          )}
        </details>
        <div className="flex gap-2">
          <Button onClick={() => reset()}>Try again</Button>
          <Button variant="outline" asChild>
            <a href="/dashboard">Go to dashboard</a>
          </Button>
        </div>
      </div>
    </div>
  );
}
