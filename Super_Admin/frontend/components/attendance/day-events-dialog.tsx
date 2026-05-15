"use client";

import { format, parseISO } from "date-fns";
import {
  Camera as CameraIcon,
  Image as ImageIcon,
  Loader2,
} from "lucide-react";
import { useState } from "react";

import { EventTypeBadge } from "@/components/attendance/event-type-badge";
import { SnapshotViewer } from "@/components/snapshots/snapshot-viewer";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useEventList,
  useSnapshotUrl,
} from "@/lib/hooks/use-attendance";
import type { AttendanceEventDetail } from "@/lib/types/attendance";
import { cn } from "@/lib/utils";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  employeeId: number | null;
  /** YYYY-MM-DD (the day's `work_date`). */
  workDate: string | null;
  /** Display name for the dialog header. */
  employeeName: string;
}

export function DayEventsDialog({
  open,
  onOpenChange,
  employeeId,
  workDate,
  employeeName,
}: Props) {
  // Build the inclusive ISO datetime range for one local day.
  const range = workDate
    ? {
        start: `${workDate}T00:00:00`,
        end: `${workDate}T23:59:59.999`,
      }
    : null;

  const query = useEventList({
    employee_id: employeeId ?? undefined,
    start: range?.start,
    end: range?.end,
    limit: 500,
    offset: 0,
  });

  // Sort oldest → newest so timeline feels chronological.
  const events = (query.data?.items ?? [])
    .slice()
    .sort((a, b) => (a.event_time < b.event_time ? -1 : 1));

  const [viewerIndex, setViewerIndex] = useState<number | null>(null);

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-h-[90vh] max-w-3xl overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {employeeName}
              {workDate && (
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  {format(parseISO(workDate), "EEEE, MMMM d, yyyy")}
                </span>
              )}
            </DialogTitle>
            <DialogDescription>
              Every IN, OUT, and break event captured for this person on this
              day, in chronological order. Click a snapshot to view it
              full-size.
            </DialogDescription>
          </DialogHeader>

          {query.isLoading ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-44 w-full" />
              ))}
            </div>
          ) : events.length === 0 ? (
            <div className="rounded-md border border-dashed bg-muted/20 px-6 py-12 text-center">
              <ImageIcon className="mx-auto h-6 w-6 text-muted-foreground" />
              <p className="mt-2 text-sm font-medium">
                No events on this day
              </p>
              <p className="text-xs text-muted-foreground">
                The cameras didn't record any activity for this person.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
              {events.map((e, idx) => (
                <EventCard
                  key={e.id}
                  event={e}
                  onClick={() => {
                    if (e.snapshot_available) setViewerIndex(idx);
                  }}
                />
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Existing full-screen snapshot viewer, scoped to this day's events. */}
      <SnapshotViewer
        events={events}
        index={viewerIndex ?? 0}
        open={viewerIndex !== null}
        onOpenChange={(v) => !v && setViewerIndex(null)}
        onIndexChange={setViewerIndex}
      />
    </>
  );
}

// ----------------------------------------------------------------------
// Per-event card with snapshot thumbnail
// ----------------------------------------------------------------------

function EventCard({
  event,
  onClick,
}: {
  event: AttendanceEventDetail;
  onClick: () => void;
}) {
  const { url, loading } = useSnapshotUrl(
    event.snapshot_available ? event.id : null,
  );
  const dt = parseISO(event.event_time);

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!event.snapshot_available}
      className={cn(
        "group flex flex-col overflow-hidden rounded-md border bg-card text-left transition-shadow",
        event.snapshot_available
          ? "hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          : "cursor-default opacity-80",
      )}
      title={
        event.snapshot_available
          ? "Click to view full snapshot"
          : "No snapshot for this event"
      }
    >
      <div className="relative aspect-square w-full bg-black">
        {!event.snapshot_available ? (
          <div className="flex h-full w-full flex-col items-center justify-center gap-1 text-white/50">
            <ImageIcon className="h-5 w-5" />
            <span className="text-[10px] uppercase tracking-wide">
              No snapshot
            </span>
          </div>
        ) : loading || !url ? (
          <div className="flex h-full w-full items-center justify-center text-white/40">
            <Loader2 className="h-4 w-4 animate-spin" />
          </div>
        ) : (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={url}
            alt={`${event.event_type} at ${format(dt, "h:mm:ss a").toLowerCase()}`}
            className="h-full w-full object-cover transition-transform group-hover:scale-[1.02]"
          />
        )}
        {/* Time pill (top-right) */}
        <span className="absolute right-1.5 top-1.5 rounded bg-black/70 px-1.5 py-0.5 font-mono text-[10px] tabular-nums text-white">
          {format(dt, "h:mm:ss a").toLowerCase()}
        </span>
      </div>
      <div className="space-y-1 p-2">
        <div className="flex items-center gap-1.5">
          <EventTypeBadge type={event.event_type} />
          {event.is_manual && (
            <Badge variant="secondary" className="text-[10px]">
              manual
            </Badge>
          )}
        </div>
        <p className="flex items-center gap-1 text-[11px] text-muted-foreground">
          <CameraIcon className="h-3 w-3" />
          <span className="truncate">{event.camera_name ?? "—"}</span>
          {event.confidence !== null && (
            <span className="ml-auto tabular-nums">
              {(event.confidence * 100).toFixed(0)}%
            </span>
          )}
        </p>
      </div>
    </button>
  );
}
