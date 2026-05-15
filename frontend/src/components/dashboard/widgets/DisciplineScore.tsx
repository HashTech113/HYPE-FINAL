import { useEffect, useMemo, useRef, useState } from "react";
import { Award, Radio, Trophy } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboardData } from "@/contexts/DashboardDataContext";
import {
  buildDisciplineByTeam,
  buildTopEmployeesByScore,
  type DisciplineStatus,
} from "@/lib/dashboardData";
import { getCurrentCompany, getCurrentRole } from "@/lib/auth";
import { getSnapshotLogs, type SnapshotLogItem } from "@/api/dashboardApi";
import { formatDateDash, formatTime12, parseTimestamp } from "@/lib/dateFormat";
import { cn } from "@/lib/utils";

const STATUS_STYLES: Record<DisciplineStatus, { badge: string; bar: string; label: string }> = {
  Outstanding: { badge: "bg-green-50 text-green-700", bar: "bg-green-500", label: "Outstanding" },
  Excellent: { badge: "bg-blue-50 text-blue-700", bar: "bg-blue-500", label: "Excellent" },
  "Very Good": { badge: "bg-orange-50 text-orange-700", bar: "bg-orange-500", label: "Very Good" },
  Good: { badge: "bg-yellow-50 text-yellow-700", bar: "bg-yellow-500", label: "Good" },
  Average: { badge: "bg-slate-100 text-slate-600", bar: "bg-slate-400", label: "Average" },
};

type DisciplineScoreProps = {
  flipped?: boolean;
};

export function DisciplineScore({ flipped = false }: DisciplineScoreProps) {
  const { attendance } = useDashboardData();
  const rows = useMemo(() => buildDisciplineByTeam(attendance), [attendance]);
  const isHr = getCurrentRole() === "hr";
  const hrCompany = isHr ? getCurrentCompany() : null;
  const topEmployees = useMemo(
    () => (isHr ? buildTopEmployeesByScore(attendance, 5) : []),
    [attendance, isHr],
  );
  const companyLabel = hrCompany ? hrCompany.toUpperCase() : null;

  return (
    <div className="flip-card">
      <div className={cn("flip-card-inner", flipped && "is-flipped")}>
        <div className="flip-card-face flip-card-front">
          {/* ``overflow-hidden`` so the inner scrollable list is visibly
              clipped at the card's rounded boundary instead of leaking
              past it when the worker grid above bounds this card to a
              fixed height. */}
          <Card className="flex h-full flex-col overflow-hidden">
            <CardHeader className="flex flex-row items-center gap-2 pb-5 pl-0">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Award className="h-5 w-5" />
              </div>
              <CardTitle className="text-base font-semibold">
                Discipline Score by Team
                {companyLabel && (
                  <span
                    className="ml-1.5 font-bold tracking-[0.18em] drop-shadow-[0_1px_0_rgba(80,55,0,0.35)]"
                    style={{ color: "#B8860B" }}
                  >
                    {companyLabel}
                  </span>
                )}
              </CardTitle>
              <p className="ml-auto text-xs text-muted-foreground">Last 30 days</p>
            </CardHeader>

            <CardContent className="flex min-h-0 flex-1 flex-col">
              {rows.length === 0 && topEmployees.length === 0 ? (
                <p className="py-10 text-center text-sm text-muted-foreground">No team data yet.</p>
              ) : (
                // Scroll is invisible (no scrollbar chrome) but still works
                // via mouse-wheel / trackpad / touch — keeps the card visually
                // clean while letting the list overflow gracefully.
                <div className="scrollbar-hidden flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto pr-1">
                  {/* Admin-only: per-team rollup. HR sees only their own company,
                      so the team-by-team list is redundant — the team name is
                      already in the card title. */}
                  {!isHr &&
                    rows.map((row) => {
                      const style = STATUS_STYLES[row.status];
                      return (
                        <div key={row.company} className="space-y-1.5">
                          <div className="flex items-center justify-between gap-3">
                            <div className="flex min-w-0 items-center gap-2">
                              <span className="truncate text-sm font-medium text-foreground">
                                {row.company}
                              </span>
                              <span
                                className={cn(
                                  "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide transition-colors",
                                  style.badge,
                                )}
                              >
                                {style.label}
                              </span>
                            </div>
                            <span className="text-sm font-semibold tabular-nums text-foreground">
                              {row.score}%
                            </span>
                          </div>
                          <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                            <div
                              className={cn("h-full rounded-full transition-all duration-1000", style.bar)}
                              style={{ width: `${Math.max(0, Math.min(100, row.score))}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}

                  {isHr && topEmployees.length > 0 && (
                    <div>
                      <div className="mb-2 flex items-center gap-1.5">
                        <Trophy className="h-3.5 w-3.5 text-amber-500" />
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                          Top 5 Employees
                        </p>
                      </div>
                      <ol className="space-y-4">
                        {topEmployees.map((emp, idx) => {
                          const style = STATUS_STYLES[emp.status];
                          return (
                            <li
                              key={`${emp.company}::${emp.name}`}
                              className="space-y-1.5"
                            >
                              <div className="flex items-center justify-between gap-3">
                                <div className="flex min-w-0 items-center gap-2">
                                  <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-slate-100 text-[11px] font-semibold text-slate-700">
                                    {idx + 1}
                                  </span>
                                  <span className="truncate text-sm font-medium text-foreground">
                                    {emp.name}
                                  </span>
                                  <span
                                    className={cn(
                                      "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide transition-colors",
                                      style.badge,
                                    )}
                                  >
                                    {style.label}
                                  </span>
                                </div>
                                <span className="text-sm font-semibold tabular-nums text-foreground">
                                  {emp.score}%
                                </span>
                              </div>
                              <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                                <div
                                  className={cn("h-full rounded-full transition-all duration-1000", style.bar)}
                                  style={{ width: `${Math.max(0, Math.min(100, emp.score))}%` }}
                                />
                              </div>
                            </li>
                          );
                        })}
                      </ol>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="flip-card-face flip-card-back">
          <LiveSnapshotsCard active={flipped} />
        </div>
      </div>
    </div>
  );
}

const SNAPSHOT_POLL_MS = 5_000;
const SNAPSHOT_LIMIT = 20;
const CAROUSEL_INTERVAL_MS = 2_500;

function LiveSnapshotsCard({ active }: { active: boolean }) {
  const [items, setItems] = useState<SnapshotLogItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [index, setIndex] = useState(0);
  const aliveRef = useRef(true);

  // HR users must only see captures of their own company's employees
  // (admins still see every team). The snapshot row already carries a
  // server-resolved `company`, so a client-side filter is enough — no
  // unrecognized faces leak through because their company resolves to null.
  const isHr = getCurrentRole() === "hr";
  const hrCompany = isHr ? getCurrentCompany() : null;

  // Poll the snapshot feed only while flipped — no background traffic
  // when the operator is looking at scores.
  useEffect(() => {
    aliveRef.current = true;
    if (!active) return () => undefined;

    let cancelled = false;
    const fetchOnce = async () => {
      try {
        const data = await getSnapshotLogs({ limit: SNAPSHOT_LIMIT });
        if (cancelled || !aliveRef.current) return;
        const next = hrCompany
          ? data.items.filter((it) => it.company === hrCompany)
          : data.items;
        setItems(next);
        setError(null);
      } catch (err) {
        if (cancelled || !aliveRef.current) return;
        setError(err instanceof Error ? err.message : "Failed to load snapshots");
      } finally {
        if (!cancelled && aliveRef.current) setLoading(false);
      }
    };

    setLoading(true);
    void fetchOnce();
    const handle = window.setInterval(() => void fetchOnce(), SNAPSHOT_POLL_MS);

    return () => {
      cancelled = true;
      aliveRef.current = false;
      window.clearInterval(handle);
    };
  }, [active, hrCompany]);

  // Auto-advance carousel while flipped
  useEffect(() => {
    if (!active || items.length <= 1) return;
    const handle = window.setInterval(() => {
      setIndex((i) => (i + 1) % items.length);
    }, CAROUSEL_INTERVAL_MS);
    return () => window.clearInterval(handle);
  }, [active, items.length]);

  // Keep index in range when the feed shrinks
  useEffect(() => {
    if (items.length === 0) {
      if (index !== 0) setIndex(0);
    } else if (index >= items.length) {
      setIndex(0);
    }
  }, [items.length, index]);

  const current = items[index] ?? null;
  const total = items.length;

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="flex flex-row items-center gap-2 pb-5 pl-0">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-600">
          <Radio className="h-5 w-5" />
        </div>
        <CardTitle className="text-base font-semibold">Recognized Snapshots</CardTitle>
        <span className="ml-auto inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          Live
        </span>
      </CardHeader>

      <CardContent className="flex min-h-0 flex-1 flex-col">
        {error ? (
          <p className="py-10 text-center text-sm text-rose-600">{error}</p>
        ) : !current ? (
          <p className="py-10 text-center text-sm text-muted-foreground">
            {loading ? "Loading snapshots…" : "No snapshots yet."}
          </p>
        ) : (
          <SnapshotCarousel items={items} index={index} current={current} total={total} />
        )}
      </CardContent>
    </Card>
  );
}

function SnapshotCarousel({
  items,
  index,
  current,
  total,
}: {
  items: SnapshotLogItem[];
  index: number;
  current: SnapshotLogItem;
  total: number;
}) {
  const { date, time } = useMemo(() => {
    const d = parseTimestamp(current.timestamp);
    return {
      date: d ? formatDateDash(d) : "",
      time: d ? formatTime12(d) : "",
    };
  }, [current.timestamp]);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3">
      {/* Featured image — crossfades on index change via key. Details
          overlay sits inside the image at the bottom; a subtle neutral
          gradient keeps the text legible without a colored tint. */}
      <div className="relative min-h-0 flex-1 overflow-hidden rounded-xl border border-emerald-200 bg-slate-900">
        <img
          key={current.id}
          src={current.image_url}
          alt={current.name}
          className="h-full w-full animate-fade-in object-cover"
        />
        <div className="absolute inset-x-0 bottom-0 flex items-end justify-between gap-3 bg-gradient-to-t from-black/70 via-black/30 to-transparent px-3 py-2">
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-white">{current.name}</div>
            {current.company && (
              <div className="truncate text-[11px] font-medium text-emerald-200">
                {current.company}
              </div>
            )}
          </div>
          {(date || time) && (
            <div className="flex shrink-0 flex-col items-end text-[11px] font-medium tabular-nums leading-tight text-emerald-100">
              {date && <span>{date}</span>}
              {time && <span>{time}</span>}
            </div>
          )}
        </div>
      </div>

      {/* Position indicator + thumbnail strip */}
      <div className="flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
        <span className="tabular-nums">
          {index + 1} / {total}
        </span>
        <div className="flex items-center gap-1">
          {items.slice(0, 8).map((item, i) => (
            <span
              key={item.id}
              className={cn(
                "h-1.5 w-1.5 rounded-full transition-colors",
                i === index % 8 ? "bg-emerald-500" : "bg-slate-300",
              )}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
