"use client";

import { format, formatDistanceToNow, parseISO } from "date-fns";
import {
  AlertCircle,
  Camera as CameraIcon,
  ChevronLeft,
  ChevronRight,
  Clock,
  Download,
  ImageIcon,
  Loader2,
  PencilLine,
  Target,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef } from "react";

import { EventTypeBadge } from "@/components/attendance/event-type-badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { useSnapshotUrl } from "@/lib/hooks/use-attendance";
import type { AttendanceEventDetail } from "@/lib/types/attendance";
import { cn } from "@/lib/utils";

interface Props {
  events: AttendanceEventDetail[];
  index: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onIndexChange: (index: number) => void;
}

export function SnapshotViewer({
  events,
  index,
  open,
  onOpenChange,
  onIndexChange,
}: Props) {
  const current = events[index] ?? null;
  const { url, loading, error } = useSnapshotUrl(
    current?.snapshot_available ? current.id : null,
  );

  const hasPrev = index > 0;
  const hasNext = index < events.length - 1;

  const go = useCallback(
    (delta: number) => {
      const next = index + delta;
      if (next >= 0 && next < events.length) onIndexChange(next);
    },
    [index, events.length, onIndexChange],
  );

  // Keyboard navigation: arrows + Esc + Home/End for first/last.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        go(-1);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        go(1);
      } else if (e.key === "Home") {
        e.preventDefault();
        onIndexChange(0);
      } else if (e.key === "End") {
        e.preventDefault();
        onIndexChange(events.length - 1);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, go, events.length, onIndexChange]);

  async function download() {
    if (!url || !current) return;
    const a = document.createElement("a");
    a.href = url;
    const ts = format(parseISO(current.event_time), "yyyyMMdd-HHmmss");
    a.download = `snap_${current.employee_code}_${ts}_${current.event_type}.jpg`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className={cn(
          // Big stage. p-0 so the image area can stretch edge to edge.
          "max-w-[min(96vw,1400px)] gap-0 overflow-hidden p-0",
          "h-[min(92vh,900px)]",
          // Hide the default ShadCN close (the last <button> child of
          // DialogContent renders the X). We render our own with a dark
          // backdrop so it stays readable over the image.
          "[&>button:last-child]:hidden",
        )}
      >
        {/* Accessibility: Radix Dialog requires a title; we hide it
            visually because the sidebar already shows the same info. */}
        <DialogTitle className="sr-only">
          {current
            ? `${current.employee_name} — ${current.event_type} snapshot`
            : "Snapshot viewer"}
        </DialogTitle>
        <DialogDescription className="sr-only">
          {current
            ? `Recorded ${format(parseISO(current.event_time), "PPpp")} on ${current.camera_name ?? "an unknown camera"}.`
            : "No event selected."}
        </DialogDescription>

        {!current ? (
          <Empty message="No event selected." />
        ) : (
          <div className="grid h-full min-h-0 grid-rows-[1fr_auto] lg:grid-cols-[1fr_360px] lg:grid-rows-[1fr_auto]">
            {/* IMAGE PANE — top-left on desktop, top on mobile */}
            <div className="relative min-h-0 bg-black lg:row-span-1">
              <ImagePane
                url={url}
                loading={loading}
                error={error}
                hasSnapshot={current.snapshot_available}
                eventLabel={`${current.employee_name} · ${current.event_type}`}
              />

              {events.length > 1 && (
                <>
                  <NavButton
                    side="left"
                    onClick={() => go(-1)}
                    disabled={!hasPrev}
                    aria="Previous (←)"
                  />
                  <NavButton
                    side="right"
                    onClick={() => go(1)}
                    disabled={!hasNext}
                    aria="Next (→)"
                  />
                </>
              )}

              {/* Counter pill, top-left */}
              {events.length > 1 && (
                <div className="pointer-events-none absolute left-3 top-3 rounded-full bg-black/70 px-2.5 py-1 text-[11px] font-medium tabular-nums text-white shadow backdrop-blur">
                  {index + 1} / {events.length}
                </div>
              )}

              {/* Close button, top-right inside image area for thumb-reach */}
              <button
                type="button"
                aria-label="Close"
                onClick={() => onOpenChange(false)}
                className="absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-full bg-black/70 text-white shadow backdrop-blur transition-colors hover:bg-black/90"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* SIDEBAR — right side on desktop, hidden on small screens (info shown above the strip instead) */}
            <aside className="hidden min-h-0 flex-col overflow-y-auto border-l bg-card lg:flex">
              <DetailPanel current={current} />
              <div className="mt-auto flex items-center justify-between gap-2 border-t p-4">
                <ShortcutHint />
                <Button
                  variant="default"
                  size="sm"
                  onClick={download}
                  disabled={!url}
                >
                  <Download className="h-4 w-4" />
                  Download
                </Button>
              </div>
            </aside>

            {/* THUMBNAIL STRIP — full width, bottom row */}
            <div className="lg:col-span-2 lg:row-start-2">
              <ThumbStrip
                events={events}
                index={index}
                onPick={onIndexChange}
              />
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ----------------------------------------------------------------------
// Image pane
// ----------------------------------------------------------------------

function ImagePane({
  url,
  loading,
  error,
  hasSnapshot,
  eventLabel,
}: {
  url: string | null;
  loading: boolean;
  error: string | null;
  hasSnapshot: boolean;
  eventLabel: string;
}) {
  if (!hasSnapshot) {
    return <Empty message="This event has no snapshot." />;
  }
  if (loading) {
    return (
      <div className="flex h-full w-full items-center justify-center gap-2 text-sm text-white/70">
        <Loader2 className="h-5 w-5 animate-spin" /> Loading snapshot…
      </div>
    );
  }
  if (error || !url) {
    return <Empty message={error ?? "Snapshot unavailable."} isError />;
  }
  return (
    /* eslint-disable-next-line @next/next/no-img-element */
    <img
      src={url}
      alt={eventLabel}
      // h-full + w-full + object-contain → image fills the pane while
      // preserving its native aspect ratio (the black around it is the
      // natural letterbox of a tall portrait crop in a wider stage,
      // which is now intentional + properly centered).
      className="block h-full w-full object-contain"
    />
  );
}

// ----------------------------------------------------------------------
// Sidebar detail panel
// ----------------------------------------------------------------------

function DetailPanel({ current }: { current: AttendanceEventDetail }) {
  const dt = parseISO(current.event_time);
  return (
    <div className="space-y-5 p-5">
      {/* Identity */}
      <div className="flex items-center gap-3">
        <Avatar className="h-12 w-12">
          <AvatarFallback className="text-base">
            {initials(current.employee_name, current.employee_code)}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0">
          <p className="truncate text-base font-semibold leading-tight">
            {current.employee_name}
          </p>
          <p className="truncate text-xs text-muted-foreground">
            {current.employee_code}
          </p>
        </div>
      </div>

      {/* Event chip + flags */}
      <div className="flex flex-wrap items-center gap-2">
        <EventTypeBadge type={current.event_type} />
        {current.is_manual && (
          <Badge variant="secondary" className="gap-1">
            <PencilLine className="h-3 w-3" /> manual entry
          </Badge>
        )}
      </div>

      {/* Stat rows */}
      <div className="space-y-3 rounded-md border bg-muted/30 p-3 text-sm">
        <Row icon={<Clock className="h-3.5 w-3.5" />} label="Time">
          <div className="flex flex-col text-right leading-tight">
            <span className="font-medium tabular-nums">
              {format(dt, "PPpp")}
            </span>
            <span className="text-[11px] text-muted-foreground">
              {formatDistanceToNow(dt, { addSuffix: true })}
            </span>
          </div>
        </Row>
        <Row icon={<CameraIcon className="h-3.5 w-3.5" />} label="Camera">
          <span className="font-medium">{current.camera_name ?? "—"}</span>
        </Row>
        <Row icon={<Target className="h-3.5 w-3.5" />} label="Confidence">
          <ConfidenceBar value={current.confidence} />
        </Row>
      </div>

      {current.note && (
        <div className="rounded-md border-l-2 border-primary/40 bg-muted/20 px-3 py-2 text-xs">
          <p className="font-medium uppercase tracking-wide text-muted-foreground">
            Note
          </p>
          <p className="mt-1 leading-relaxed">{current.note}</p>
        </div>
      )}
    </div>
  );
}

function Row({
  icon,
  label,
  children,
}: {
  icon: React.ReactNode;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-3">
      <span className="inline-flex items-center gap-1.5 text-xs uppercase tracking-wide text-muted-foreground">
        {icon}
        {label}
      </span>
      <div className="min-w-0 flex-1 text-right text-sm">{children}</div>
    </div>
  );
}

function ConfidenceBar({ value }: { value: number | null }) {
  if (value === null) return <span className="text-muted-foreground">—</span>;
  const pct = Math.max(0, Math.min(100, value * 100));
  // Color graded: red < 50, amber < 70, green ≥ 70
  const color =
    pct >= 70
      ? "bg-success"
      : pct >= 50
        ? "bg-warning"
        : "bg-destructive";
  return (
    <div className="ml-auto flex w-full max-w-[180px] flex-col items-end gap-1">
      <span className="font-medium tabular-nums">{pct.toFixed(1)}%</span>
      <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <span
          className={cn("absolute inset-y-0 left-0 rounded-full", color)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------
// Thumbnail strip
// ----------------------------------------------------------------------

function ThumbStrip({
  events,
  index,
  onPick,
}: {
  events: AttendanceEventDetail[];
  index: number;
  onPick: (i: number) => void;
}) {
  // Render a windowed slice around the current index so we don't
  // hammer the API with 41 image fetches at once. ±10 around the
  // selected item is plenty for visual context, and arrow-key nav is
  // the primary way to step through anyway.
  const window = 12;
  const start = Math.max(0, index - window);
  const end = Math.min(events.length, index + window + 1);
  const visible = useMemo(
    () => events.slice(start, end).map((e, i) => ({ event: e, idx: start + i })),
    [events, start, end],
  );

  // Auto-scroll the active thumb into view on every index change.
  const scrollerRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const el = scrollerRef.current?.querySelector<HTMLElement>(
      `[data-thumb-idx="${index}"]`,
    );
    el?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
  }, [index]);

  if (events.length <= 1) return null;

  return (
    <div className="border-t bg-muted/20">
      <div
        ref={scrollerRef}
        className="flex gap-2 overflow-x-auto px-3 py-3 [scrollbar-width:thin]"
      >
        {start > 0 && (
          <div className="self-center px-1 text-xs text-muted-foreground">
            …{start} earlier
          </div>
        )}
        {visible.map(({ event, idx }) => (
          <Thumb
            key={event.id}
            event={event}
            active={idx === index}
            onClick={() => onPick(idx)}
            indexLabel={idx + 1}
          />
        ))}
        {end < events.length && (
          <div className="self-center px-1 text-xs text-muted-foreground">
            +{events.length - end} more…
          </div>
        )}
      </div>
    </div>
  );
}

function Thumb({
  event,
  active,
  onClick,
  indexLabel,
}: {
  event: AttendanceEventDetail;
  active: boolean;
  onClick: () => void;
  indexLabel: number;
}) {
  const { url, loading } = useSnapshotUrl(
    event.snapshot_available ? event.id : null,
  );
  return (
    <button
      type="button"
      onClick={onClick}
      data-thumb-idx={indexLabel - 1}
      className={cn(
        "group relative h-16 w-16 shrink-0 overflow-hidden rounded-md border bg-black transition",
        active
          ? "ring-2 ring-primary ring-offset-2 ring-offset-background"
          : "opacity-70 hover:opacity-100",
      )}
      title={`${format(parseISO(event.event_time), "PPpp")} · ${event.event_type}`}
      aria-label={`Snapshot ${indexLabel}`}
    >
      {!event.snapshot_available ? (
        <div className="flex h-full w-full items-center justify-center text-white/40">
          <ImageIcon className="h-4 w-4" />
        </div>
      ) : loading || !url ? (
        <div className="flex h-full w-full items-center justify-center text-white/40">
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        </div>
      ) : (
        /* eslint-disable-next-line @next/next/no-img-element */
        <img src={url} alt="" className="h-full w-full object-cover" />
      )}
      {/* Index pill, bottom-left of thumb */}
      <span className="absolute bottom-0.5 left-0.5 rounded bg-black/70 px-1 text-[9px] font-medium tabular-nums text-white">
        {indexLabel}
      </span>
    </button>
  );
}

// ----------------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------------

function Empty({ message, isError }: { message: string; isError?: boolean }) {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-2 p-8 text-sm text-white/70">
      <AlertCircle
        className={cn("h-6 w-6", isError ? "text-destructive" : "text-white/50")}
      />
      <p className="text-center">{message}</p>
    </div>
  );
}

function NavButton({
  side,
  onClick,
  disabled,
  aria,
}: {
  side: "left" | "right";
  onClick: () => void;
  disabled: boolean;
  aria: string;
}) {
  return (
    <button
      type="button"
      aria-label={aria}
      title={aria}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "absolute top-1/2 z-10 -translate-y-1/2 rounded-full bg-black/60 p-2.5 text-white shadow backdrop-blur transition-all",
        "hover:scale-110 hover:bg-black/85 disabled:opacity-25 disabled:hover:scale-100",
        side === "left" ? "left-3" : "right-3",
      )}
    >
      {side === "left" ? (
        <ChevronLeft className="h-5 w-5" />
      ) : (
        <ChevronRight className="h-5 w-5" />
      )}
    </button>
  );
}

function ShortcutHint() {
  return (
    <p className="hidden text-[10px] uppercase tracking-wider text-muted-foreground sm:block">
      <Kbd>←</Kbd> <Kbd>→</Kbd> navigate · <Kbd>Esc</Kbd> close
    </p>
  );
}

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="mx-0.5 rounded border bg-muted px-1 py-px font-mono text-[10px] text-foreground">
      {children}
    </kbd>
  );
}

function initials(name: string, code: string): string {
  const src = (name || code || "").trim();
  const parts = src.split(/\s+/).slice(0, 2);
  return parts.map((p) => p[0]?.toUpperCase() ?? "").join("") || "?";
}
