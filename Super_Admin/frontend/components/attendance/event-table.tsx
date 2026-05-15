"use client";

import { format, formatDistanceToNow, parseISO } from "date-fns";
import {
  Camera as CameraIcon,
  ChevronRight,
  Image as ImageIcon,
  MoreHorizontal,
  Pencil,
  Trash2,
} from "lucide-react";
import { Fragment, useMemo, useState } from "react";

import { EventTypeBadge } from "@/components/attendance/event-type-badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { AttendanceEventDetail } from "@/lib/types/attendance";
import { cn } from "@/lib/utils";

function initials(name: string, code: string): string {
  const src = (name || code || "").trim();
  const parts = src.split(/\s+/).slice(0, 2);
  return parts.map((p) => p[0]?.toUpperCase() ?? "").join("") || "?";
}

function fmt(iso: string): { absolute: string; relative: string } {
  try {
    const dt = parseISO(iso);
    return {
      absolute: `${format(dt, "MMM d")} · ${format(dt, "h:mm:ss a").toLowerCase()}`,
      relative: formatDistanceToNow(dt, { addSuffix: true }),
    };
  } catch {
    return { absolute: iso, relative: "" };
  }
}

interface EmployeeGroup {
  employeeId: number;
  employeeName: string;
  employeeCode: string;
  latest: AttendanceEventDetail;
  all: AttendanceEventDetail[];
}

function groupByEmployee(rows: AttendanceEventDetail[]): EmployeeGroup[] {
  // Events come back from the API ordered by event_time DESC, so the first
  // occurrence of each employee is automatically their latest event.
  const byId = new Map<number, EmployeeGroup>();
  for (const ev of rows) {
    const g = byId.get(ev.employee_id);
    if (g) {
      g.all.push(ev);
    } else {
      byId.set(ev.employee_id, {
        employeeId: ev.employee_id,
        employeeName: ev.employee_name,
        employeeCode: ev.employee_code,
        latest: ev,
        all: [ev],
      });
    }
  }
  // Preserve API ordering (most recent activity first) by sorting groups
  // on their latest event's timestamp.
  return Array.from(byId.values()).sort((a, b) =>
    a.latest.event_time < b.latest.event_time ? 1 : -1,
  );
}

interface Props {
  rows: AttendanceEventDetail[] | undefined;
  loading: boolean;
  onOpenSnapshot: (event: AttendanceEventDetail) => void;
  onEdit: (event: AttendanceEventDetail) => void;
  onDelete: (event: AttendanceEventDetail) => void;
}

export function EventTable({
  rows,
  loading,
  onOpenSnapshot,
  onEdit,
  onDelete,
}: Props) {
  const groups = useMemo(() => groupByEmployee(rows ?? []), [rows]);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  function toggle(employeeId: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(employeeId)) next.delete(employeeId);
      else next.add(employeeId);
      return next;
    });
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[28%]">Employee</TableHead>
          <TableHead>Latest event</TableHead>
          <TableHead>Timestamp</TableHead>
          <TableHead>Camera</TableHead>
          <TableHead>Confidence</TableHead>
          <TableHead className="w-24 text-right">Snapshot</TableHead>
          <TableHead className="w-12" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {loading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <TableRow key={`s-${i}`}>
              <TableCell>
                <div className="flex items-center gap-3">
                  <Skeleton className="h-9 w-9 rounded-full" />
                  <div className="flex flex-col gap-1.5">
                    <Skeleton className="h-3 w-40" />
                    <Skeleton className="h-3 w-24" />
                  </div>
                </div>
              </TableCell>
              <TableCell>
                <Skeleton className="h-5 w-24 rounded-full" />
              </TableCell>
              <TableCell>
                <Skeleton className="h-3 w-32" />
              </TableCell>
              <TableCell>
                <Skeleton className="h-3 w-24" />
              </TableCell>
              <TableCell>
                <Skeleton className="h-3 w-12" />
              </TableCell>
              <TableCell className="text-right">
                <Skeleton className="ml-auto h-8 w-20 rounded-md" />
              </TableCell>
              <TableCell />
            </TableRow>
          ))
        ) : groups.length === 0 ? (
          <TableRow>
            <TableCell colSpan={7} className="py-12 text-center">
              <p className="text-sm text-muted-foreground">
                No events match these filters.
              </p>
            </TableCell>
          </TableRow>
        ) : (
          groups.map((g) => {
            const isOpen = expanded.has(g.employeeId);
            return (
              <Fragment key={g.employeeId}>
                <SummaryRow
                  group={g}
                  open={isOpen}
                  onToggle={() => toggle(g.employeeId)}
                  onOpenSnapshot={onOpenSnapshot}
                  onEdit={onEdit}
                  onDelete={onDelete}
                />
                {isOpen && (
                  <TableRow className="bg-muted/30 hover:bg-muted/30">
                    <TableCell colSpan={7} className="p-0">
                      <ChildEvents
                        events={g.all}
                        onOpenSnapshot={onOpenSnapshot}
                        onEdit={onEdit}
                        onDelete={onDelete}
                      />
                    </TableCell>
                  </TableRow>
                )}
              </Fragment>
            );
          })
        )}
      </TableBody>
    </Table>
  );
}

function SummaryRow({
  group,
  open,
  onToggle,
  onOpenSnapshot,
  onEdit,
  onDelete,
}: {
  group: EmployeeGroup;
  open: boolean;
  onToggle: () => void;
  onOpenSnapshot: (event: AttendanceEventDetail) => void;
  onEdit: (event: AttendanceEventDetail) => void;
  onDelete: (event: AttendanceEventDetail) => void;
}) {
  const e = group.latest;
  const { absolute, relative } = fmt(e.event_time);
  const moreCount = group.all.length - 1;

  return (
    <TableRow
      className="cursor-pointer hover:bg-muted/40"
      onClick={onToggle}
    >
      <TableCell>
        <div className="flex items-center gap-3">
          <ChevronRight
            className={cn(
              "h-4 w-4 shrink-0 text-muted-foreground transition-transform",
              open && "rotate-90",
            )}
            aria-hidden
          />
          <Avatar className="h-9 w-9">
            <AvatarFallback className="text-xs">
              {initials(group.employeeName, group.employeeCode)}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <p className="truncate font-medium">{group.employeeName}</p>
            <p className="truncate text-xs text-muted-foreground">
              {group.employeeCode}
              {moreCount > 0
                ? ` · ${moreCount} earlier event${moreCount === 1 ? "" : "s"}`
                : ""}
            </p>
          </div>
        </div>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1.5">
          <EventTypeBadge type={e.event_type} />
          {e.is_manual && (
            <Badge variant="secondary" className="gap-1">
              <Pencil className="h-3 w-3" /> manual
            </Badge>
          )}
        </div>
      </TableCell>
      <TableCell>
        <div className="flex flex-col leading-tight">
          <span className="text-sm tabular-nums">{absolute}</span>
          {relative && (
            <span className="text-[11px] text-muted-foreground">{relative}</span>
          )}
        </div>
      </TableCell>
      <TableCell className="text-sm text-muted-foreground">
        {e.camera_name ? (
          <span className="inline-flex items-center gap-1.5">
            <CameraIcon className="h-3.5 w-3.5" />
            {e.camera_name}
          </span>
        ) : (
          "—"
        )}
      </TableCell>
      <TableCell className="text-sm tabular-nums text-muted-foreground">
        {e.confidence !== null ? `${(e.confidence * 100).toFixed(1)}%` : "—"}
      </TableCell>
      <TableCell className="text-right">
        {e.snapshot_available ? (
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5"
            onClick={(ev) => {
              ev.stopPropagation();
              onOpenSnapshot(e);
            }}
          >
            <ImageIcon className="h-3.5 w-3.5" />
            View
          </Button>
        ) : (
          <span className="text-xs text-muted-foreground">—</span>
        )}
      </TableCell>
      <TableCell onClick={(ev) => ev.stopPropagation()}>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" aria-label="Row actions">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-44">
            <DropdownMenuItem onClick={() => onEdit(e)}>
              <Pencil className="mr-2 h-4 w-4" /> Edit latest event
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive"
              onClick={() => onDelete(e)}
            >
              <Trash2 className="mr-2 h-4 w-4" /> Delete latest event
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  );
}

function ChildEvents({
  events,
  onOpenSnapshot,
  onEdit,
  onDelete,
}: {
  events: AttendanceEventDetail[];
  onOpenSnapshot: (event: AttendanceEventDetail) => void;
  onEdit: (event: AttendanceEventDetail) => void;
  onDelete: (event: AttendanceEventDetail) => void;
}) {
  return (
    <div className="border-l-2 border-primary/30 bg-background/40 px-2 py-2">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[28%] pl-12 text-[11px] uppercase tracking-wide text-muted-foreground">
              Event #
            </TableHead>
            <TableHead className="text-[11px] uppercase tracking-wide text-muted-foreground">
              Type
            </TableHead>
            <TableHead className="text-[11px] uppercase tracking-wide text-muted-foreground">
              Timestamp
            </TableHead>
            <TableHead className="text-[11px] uppercase tracking-wide text-muted-foreground">
              Camera
            </TableHead>
            <TableHead className="text-[11px] uppercase tracking-wide text-muted-foreground">
              Confidence
            </TableHead>
            <TableHead className="w-24 text-right text-[11px] uppercase tracking-wide text-muted-foreground">
              Snapshot
            </TableHead>
            <TableHead className="w-12" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {events.map((e, idx) => {
            const { absolute, relative } = fmt(e.event_time);
            return (
              <TableRow key={e.id}>
                <TableCell className="pl-12 text-xs text-muted-foreground tabular-nums">
                  {idx === 0 ? "Latest" : `#${idx + 1}`}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1.5">
                    <EventTypeBadge type={e.event_type} />
                    {e.is_manual && (
                      <Badge variant="secondary" className="gap-1">
                        <Pencil className="h-3 w-3" /> manual
                      </Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex flex-col leading-tight">
                    <span className="text-sm tabular-nums">{absolute}</span>
                    {relative && (
                      <span className="text-[11px] text-muted-foreground">
                        {relative}
                      </span>
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {e.camera_name ? (
                    <span className="inline-flex items-center gap-1.5">
                      <CameraIcon className="h-3.5 w-3.5" />
                      {e.camera_name}
                    </span>
                  ) : (
                    "—"
                  )}
                </TableCell>
                <TableCell className="text-sm tabular-nums text-muted-foreground">
                  {e.confidence !== null
                    ? `${(e.confidence * 100).toFixed(1)}%`
                    : "—"}
                </TableCell>
                <TableCell className="text-right">
                  {e.snapshot_available ? (
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-1.5"
                      onClick={() => onOpenSnapshot(e)}
                    >
                      <ImageIcon className="h-3.5 w-3.5" />
                      View
                    </Button>
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label="Row actions"
                      >
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-44">
                      <DropdownMenuItem onClick={() => onEdit(e)}>
                        <Pencil className="mr-2 h-4 w-4" /> Edit event
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={() => onDelete(e)}
                      >
                        <Trash2 className="mr-2 h-4 w-4" /> Delete event
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
