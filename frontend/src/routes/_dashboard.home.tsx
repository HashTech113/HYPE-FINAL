import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { SectionShell } from "@/components/dashboard/SectionShell";
import { Button } from "@/components/ui/button";
import { useDashboardData } from "@/contexts/DashboardDataContext";
import { PresenceTrend } from "@/components/dashboard/widgets/PresenceTrend";
import { DisciplineScore } from "@/components/dashboard/widgets/DisciplineScore";
import { TopAlerts } from "@/components/dashboard/widgets/TopAlerts";
import { RepeatPatterns } from "@/components/dashboard/widgets/RepeatPatterns";
import { WhereToAct } from "@/components/dashboard/widgets/WhereToAct";
import { getCurrentRole } from "@/lib/auth";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_dashboard/home")({
  component: DashboardPage,
});

function DashboardPage() {
  const { loading, error, lastUpdated, refresh } = useDashboardData();
  const isAdmin = getCurrentRole() === "admin";
  const [liveSnapshots, setLiveSnapshots] = useState(false);

  const stampLabel =
    lastUpdated !== null
      ? `Updated ${lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: true })}`
      : loading
        ? "Loading…"
        : "";

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <SectionShell
        title="Dashboard"
        className="animate-fade-in-up"
        actions={
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <button
              type="button"
              onClick={() => setLiveSnapshots((prev) => !prev)}
              aria-pressed={liveSnapshots}
              className={cn(
                "flex h-9 items-center gap-1.5 rounded-md border px-4 text-xs font-semibold transition-colors",
                liveSnapshots
                  ? "border-emerald-500 bg-emerald-50 text-emerald-800"
                  : "border-slate-200 text-emerald-700 hover:bg-emerald-50",
              )}
              title={
                liveSnapshots
                  ? "Live snapshots on — click to return to discipline scores"
                  : "Show live recognized snapshots"
              }
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              Live
            </button>
            {stampLabel && <span>{stampLabel}</span>}
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="neu-pill h-9 gap-1.5 border-0 px-4 text-foreground"
              onClick={() => void refresh()}
              disabled={loading}
              title="Refresh dashboard data"
            >
              <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
              Refresh
            </Button>
          </div>
        }
      >
        {error && (
          <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Scrollable widget list — negative margins + padding keep the card's
            internal padding consistent while giving the scrollbar room. */}
        <div className="scrollbar-hidden -mx-4 flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-4">
          {/* Row 1 — fixed height on lg+ so PresenceTrend's chart card and the
              DisciplineScore card share the same baseline. ``[&>*]:min-h-0``
              overrides CSS Grid's automatic min-content sizing on the
              direct children — without it, a long team list inside
              DisciplineScore would push the row past 440 px instead of
              triggering the inner scroll. (Clipping is handled by the
              Card's own ``overflow-hidden`` so the flip-card's 3D
              animation isn't clipped at the row level.) */}
          <div className="grid grid-cols-1 gap-4 lg:h-[440px] lg:grid-cols-2 lg:[&>*]:min-h-0">
            <PresenceTrend />
            <DisciplineScore flipped={liveSnapshots} />
          </div>
          {/* Row 2 */}
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <TopAlerts />
            <RepeatPatterns />
          </div>
          {/* Row 3 — admin-only; HR sees company-scoped data and doesn't get
              the cross-team triage panel. */}
          {isAdmin && (
            <div className="grid grid-cols-1 gap-4">
              <WhereToAct />
            </div>
          )}
        </div>
      </SectionShell>
    </div>
  );
}
