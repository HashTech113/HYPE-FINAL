"use client";

import { format, parseISO } from "date-fns";
import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  Clock,
  Coffee,
  Image as ImageIcon,
  Loader2,
  LogIn,
  LogOut,
  Mail,
  Phone,
  TrendingDown,
  Users,
  X,
  XCircle,
} from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { DayEventsDialog } from "@/components/attendance/day-events-dialog";
import { EmployeePicker } from "@/components/training/employee-picker";
import { PageHeader } from "@/components/shared/page-header";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useEmployeeDailyRange } from "@/lib/hooks/use-attendance";
import { useEmployee } from "@/lib/hooks/use-employees";
import type { DailyAttendance, SessionStatus } from "@/lib/types/attendance";
import type { Employee } from "@/lib/types/employee";
import { cn } from "@/lib/utils";

// ----------------------------------------------------------------------
// Date helpers (local-time, ISO yyyy-MM-dd)
// ----------------------------------------------------------------------

function toIsoDate(d: Date): string {
  const y = d.getFullYear();
  const m = `${d.getMonth() + 1}`.padStart(2, "0");
  const day = `${d.getDate()}`.padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function startOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

function endOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0);
}

function addDays(d: Date, n: number): Date {
  const c = new Date(d);
  c.setDate(c.getDate() + n);
  return c;
}

type RangePreset = "this_month" | "last_30" | "last_7" | "today" | "custom";

function presetRange(p: RangePreset): { start: string; end: string } {
  const today = new Date();
  switch (p) {
    case "today":
      return { start: toIsoDate(today), end: toIsoDate(today) };
    case "last_7":
      return { start: toIsoDate(addDays(today, -6)), end: toIsoDate(today) };
    case "last_30":
      return { start: toIsoDate(addDays(today, -29)), end: toIsoDate(today) };
    case "this_month":
    default:
      return { start: toIsoDate(startOfMonth(today)), end: toIsoDate(endOfMonth(today)) };
  }
}

// ----------------------------------------------------------------------
// Page
// ----------------------------------------------------------------------

export default function EmployeeSummaryPage() {
  const searchParams = useSearchParams();
  const initialId = (() => {
    const raw = searchParams.get("employee");
    if (!raw) return null;
    const n = Number(raw);
    return Number.isFinite(n) && n > 0 ? n : null;
  })();

  const [employee, setEmployee] = useState<Employee | null>(null);
  // Default to TODAY so the page opens with the most useful info first.
  // Other ranges are one preset-chip click away.
  const [preset, setPreset] = useState<RangePreset>("today");
  const [{ start, end }, setRange] = useState(presetRange("today"));

  // Auto-select the employee if one was passed via ?employee=ID — the
  // Employees-table action menu uses this so clicking "View summary"
  // lands the user on a fully populated page.
  const initialEmployeeQuery = useEmployee(initialId);
  useEffect(() => {
    if (employee === null && initialEmployeeQuery.data) {
      setEmployee(initialEmployeeQuery.data);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialEmployeeQuery.data]);

  function applyPreset(p: RangePreset) {
    setPreset(p);
    if (p !== "custom") setRange(presetRange(p));
  }

  const query = useEmployeeDailyRange(employee?.id ?? null, start, end);
  const days = query.data ?? [];

  const totals = useMemo(() => computeTotals(days), [days]);

  // The day for which the events-with-snapshots dialog is open.
  // Snapshots are intentionally NOT inline in the summary table — they
  // live in this side dialog so the per-day rows stay scannable.
  const [openEventsDay, setOpenEventsDay] = useState<string | null>(null);

  return (
    <div className="mx-auto flex max-w-[1400px] flex-col gap-6">
      <PageHeader
        title="Employee summary"
        description="Pick an employee and a date range to see total hours worked, days present, lateness, and a day-by-day breakdown."
      />

      {/* Filters */}
      <Card>
        <CardContent className="flex flex-col gap-4 p-4 lg:flex-row lg:items-end">
          <div className="lg:flex-1">
            <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Employee
            </p>
            <EmployeePicker value={employee} onChange={setEmployee} />
          </div>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-2 lg:flex-1">
            <DateField
              label="From"
              value={start}
              onChange={(v) => {
                setPreset("custom");
                setRange((r) => ({ ...r, start: v }));
              }}
            />
            <DateField
              label="To"
              value={end}
              onChange={(v) => {
                setPreset("custom");
                setRange((r) => ({ ...r, end: v }));
              }}
            />
          </div>
        </CardContent>
        <div className="flex flex-wrap gap-2 border-t bg-muted/20 px-4 py-2">
          {(
            [
              ["today", "Today"],
              ["last_7", "Last 7 days"],
              ["last_30", "Last 30 days"],
              ["this_month", "This month"],
            ] as [RangePreset, string][]
          ).map(([p, label]) => (
            <Button
              key={p}
              size="sm"
              variant={preset === p ? "default" : "ghost"}
              onClick={() => applyPreset(p)}
              className="h-7 px-2.5 text-xs"
            >
              {label}
            </Button>
          ))}
          {preset === "custom" && (
            <span className="ml-1 inline-flex items-center text-xs text-muted-foreground">
              Custom range
            </span>
          )}
        </div>
      </Card>

      {/* Empty / loading states */}
      {!employee ? (
        <EmptyState
          icon={<Users className="h-6 w-6" />}
          title="Pick an employee"
          message="Their daily attendance for the selected range will show up here."
        />
      ) : query.isLoading ? (
        <SummaryLoadingSkeleton />
      ) : days.length === 0 ? (
        <EmptyState
          icon={<CalendarDays className="h-6 w-6" />}
          title="No attendance recorded"
          message={`No daily attendance rows for ${employee.name} between ${start} and ${end}.`}
        />
      ) : (
        <>
          <EmployeeIdentityCard employee={employee} totals={totals} />
          <SummaryGrid totals={totals} />
          <DailyBreakdownTable
            days={days}
            onOpenDay={(workDate) => setOpenEventsDay(workDate)}
          />
        </>
      )}

      <DayEventsDialog
        open={openEventsDay !== null}
        onOpenChange={(v) => !v && setOpenEventsDay(null)}
        employeeId={employee?.id ?? null}
        workDate={openEventsDay}
        employeeName={employee?.name ?? ""}
      />
    </div>
  );
}

// ----------------------------------------------------------------------
// Aggregate computation
// ----------------------------------------------------------------------

interface Totals {
  daysWithRow: number;
  present: number;
  incomplete: number;
  absent: number;
  totalWorkSeconds: number;
  totalBreakSeconds: number;
  totalBreakCount: number;
  totalLateMinutes: number;
  totalEarlyExitMinutes: number;
  daysLate: number;
  daysEarlyExit: number;
  avgWorkSecondsPerActiveDay: number; // averaged across present + incomplete days
}

function computeTotals(days: DailyAttendance[]): Totals {
  let present = 0;
  let incomplete = 0;
  let absent = 0;
  let totalWorkSeconds = 0;
  let totalBreakSeconds = 0;
  let totalBreakCount = 0;
  let totalLateMinutes = 0;
  let totalEarlyExitMinutes = 0;
  let daysLate = 0;
  let daysEarlyExit = 0;
  let activeDays = 0;
  for (const d of days) {
    if (d.status === "PRESENT") present += 1;
    else if (d.status === "INCOMPLETE") incomplete += 1;
    else if (d.status === "ABSENT") absent += 1;
    totalWorkSeconds += d.total_work_seconds;
    totalBreakSeconds += d.total_break_seconds;
    totalBreakCount += d.break_count;
    totalLateMinutes += d.late_minutes;
    totalEarlyExitMinutes += d.early_exit_minutes;
    if (d.late_minutes > 0) daysLate += 1;
    if (d.early_exit_minutes > 0) daysEarlyExit += 1;
    if (d.status === "PRESENT" || d.status === "INCOMPLETE") activeDays += 1;
  }
  return {
    daysWithRow: days.length,
    present,
    incomplete,
    absent,
    totalWorkSeconds,
    totalBreakSeconds,
    totalBreakCount,
    totalLateMinutes,
    totalEarlyExitMinutes,
    daysLate,
    daysEarlyExit,
    avgWorkSecondsPerActiveDay:
      activeDays > 0 ? totalWorkSeconds / activeDays : 0,
  };
}

// ----------------------------------------------------------------------
// Identity card
// ----------------------------------------------------------------------

function EmployeeIdentityCard({
  employee,
  totals,
}: {
  employee: Employee;
  totals: Totals;
}) {
  const initials = (employee.name || employee.employee_code || "?")
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
  return (
    <Card>
      <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <Avatar className="h-14 w-14">
            <AvatarFallback className="text-lg">{initials}</AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <h2 className="truncate text-xl font-semibold leading-tight">
              {employee.name}
            </h2>
            <p className="truncate text-sm text-muted-foreground">
              {employee.employee_code}
              {employee.designation ? ` · ${employee.designation}` : ""}
              {employee.department ? ` · ${employee.department}` : ""}
              {employee.company ? ` · ${employee.company}` : ""}
            </p>
            <div className="mt-1 flex flex-wrap gap-3 text-xs text-muted-foreground">
              {employee.email && (
                <span className="inline-flex items-center gap-1">
                  <Mail className="h-3 w-3" />
                  {employee.email}
                </span>
              )}
              {employee.phone && (
                <span className="inline-flex items-center gap-1">
                  <Phone className="h-3 w-3" />
                  {employee.phone}
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex flex-col items-start gap-1 sm:items-end">
          <Badge
            variant={employee.is_active ? "success" : "secondary"}
            className="text-xs"
          >
            {employee.is_active ? "Active" : "Inactive"}
          </Badge>
          <p className="text-2xl font-bold tabular-nums">
            {formatHours(totals.totalWorkSeconds)}
          </p>
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
            total work hours in range
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

// ----------------------------------------------------------------------
// Summary cards
// ----------------------------------------------------------------------

function SummaryGrid({ totals }: { totals: Totals }) {
  return (
    <div className="space-y-3">
      {/* Hero pair — the two numbers managers actually report up. */}
      <div className="grid gap-3 md:grid-cols-2">
        <HeroStat
          label="Total work hours"
          value={formatHours(totals.totalWorkSeconds)}
          subtitle={`${formatDuration(totals.totalWorkSeconds)} across ${totals.daysWithRow} day${totals.daysWithRow === 1 ? "" : "s"} in range`}
          icon={<Clock className="h-5 w-5" />}
          tone="primary"
        />
        <HeroStat
          label="Days present"
          value={`${totals.present}`}
          subtitle={`${totals.incomplete} incomplete · ${totals.absent} absent`}
          icon={<CheckCircle2 className="h-5 w-5" />}
          tone="success"
        />
      </div>
      {/* Secondary 4-card row */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat
          label="Avg / active day"
          value={formatHours(totals.avgWorkSecondsPerActiveDay)}
          sub="excluding absent days"
          icon={<TrendingDown className="h-4 w-4" />}
          tone="default"
        />
        <Stat
          label="Total break"
          value={formatDuration(totals.totalBreakSeconds)}
          sub={`${totals.totalBreakCount} break${totals.totalBreakCount === 1 ? "" : "s"} taken`}
          icon={<Coffee className="h-4 w-4" />}
          tone="default"
        />
        <Stat
          label="Late"
          value={`${totals.daysLate}`}
          sub={`days · ${totals.totalLateMinutes} min total`}
          icon={<AlertTriangle className="h-4 w-4" />}
          tone={totals.daysLate > 0 ? "warning" : "default"}
        />
        <Stat
          label="Early exit"
          value={`${totals.daysEarlyExit}`}
          sub={`days · ${totals.totalEarlyExitMinutes} min total`}
          icon={<XCircle className="h-4 w-4" />}
          tone={totals.daysEarlyExit > 0 ? "warning" : "default"}
        />
      </div>
    </div>
  );
}

function HeroStat({
  label,
  value,
  subtitle,
  icon,
  tone,
}: {
  label: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  tone: "primary" | "success";
}) {
  const accent =
    tone === "primary"
      ? "from-primary/10 to-primary/0 border-primary/30"
      : "from-success/10 to-success/0 border-success/30";
  const iconBg =
    tone === "primary" ? "bg-primary/15 text-primary" : "bg-success/15 text-success";
  return (
    <Card className={cn("overflow-hidden bg-gradient-to-br", accent)}>
      <CardContent className="flex items-center gap-4 p-5">
        <span
          className={cn(
            "inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-full",
            iconBg,
          )}
        >
          {icon}
        </span>
        <div className="min-w-0">
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          <p className="text-3xl font-bold tabular-nums leading-none">{value}</p>
          <p className="mt-1 truncate text-xs text-muted-foreground">{subtitle}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function Stat({
  label,
  value,
  sub,
  icon,
  tone,
}: {
  label: string;
  value: string;
  sub: string;
  icon: React.ReactNode;
  tone: "default" | "success" | "warning";
}) {
  const ringTone =
    tone === "success"
      ? "bg-success/15 text-success"
      : tone === "warning"
        ? "bg-warning/15 text-warning"
        : "bg-muted text-muted-foreground";
  return (
    <Card>
      <CardContent className="flex flex-col gap-1 p-4">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </span>
          <span
            className={cn(
              "inline-flex h-6 w-6 items-center justify-center rounded-full",
              ringTone,
            )}
          >
            {icon}
          </span>
        </div>
        <span className="text-2xl font-bold tabular-nums">{value}</span>
        <span className="text-[11px] text-muted-foreground">{sub}</span>
      </CardContent>
    </Card>
  );
}

// ----------------------------------------------------------------------
// Per-day table
// ----------------------------------------------------------------------

function DailyBreakdownTable({
  days,
  onOpenDay,
}: {
  days: DailyAttendance[];
  onOpenDay: (workDate: string) => void;
}) {
  // API returns in date order; render newest first for "what happened recently"
  const rows = [...days].sort((a, b) => (a.work_date < b.work_date ? 1 : -1));
  return (
    <Card>
      <CardHeader>
        <CardTitle>Day-by-day breakdown</CardTitle>
        <CardDescription>
          Newest first. Hover the times for full timestamps. Use the
          camera icon on the right to view that day&apos;s captured snapshots.
        </CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>In</TableHead>
              <TableHead>Out</TableHead>
              <TableHead>Work</TableHead>
              <TableHead>Break</TableHead>
              <TableHead>Late</TableHead>
              <TableHead>Early exit</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-24 text-right">Snapshots</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((d) => {
              const hasActivity =
                d.in_time !== null ||
                d.out_time !== null ||
                d.total_work_seconds > 0;
              return (
                <TableRow key={d.id}>
                  <TableCell className="text-sm font-medium tabular-nums">
                    {format(parseISO(d.work_date), "EEE, MMM d")}
                  </TableCell>
                  <TableCell>
                    <TimeCell
                      iso={d.in_time}
                      icon={<LogIn className="h-3 w-3" />}
                    />
                  </TableCell>
                  <TableCell>
                    <TimeCell
                      iso={d.out_time}
                      icon={<LogOut className="h-3 w-3" />}
                    />
                  </TableCell>
                  <TableCell className="text-sm tabular-nums">
                    {d.total_work_seconds > 0
                      ? formatDuration(d.total_work_seconds)
                      : "—"}
                  </TableCell>
                  <TableCell className="text-sm tabular-nums">
                    {d.total_break_seconds > 0 ? (
                      <span
                        title={`${d.break_count} break${d.break_count === 1 ? "" : "s"}`}
                      >
                        {formatDuration(d.total_break_seconds)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm tabular-nums">
                    {d.late_minutes > 0 ? (
                      <span className="text-warning">{d.late_minutes} min</span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm tabular-nums">
                    {d.early_exit_minutes > 0 ? (
                      <span className="text-warning">
                        {d.early_exit_minutes} min
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={d.status} closed={d.is_day_closed} />
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-1.5"
                      onClick={() => onOpenDay(d.work_date)}
                      disabled={!hasActivity}
                      title={
                        hasActivity
                          ? "View captured snapshots for this day"
                          : "No activity recorded"
                      }
                    >
                      <ImageIcon className="h-3.5 w-3.5" />
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function TimeCell({
  iso,
  icon,
}: {
  iso: string | null;
  icon: React.ReactNode;
}) {
  if (!iso) return <span className="text-sm text-muted-foreground">—</span>;
  const dt = parseISO(iso);
  return (
    <span
      className="inline-flex items-center gap-1 text-sm tabular-nums"
      title={format(dt, "PPpp")}
    >
      {icon}
      {format(dt, "h:mm a").toLowerCase()}
    </span>
  );
}

function StatusBadge({
  status,
  closed,
}: {
  status: SessionStatus;
  closed: boolean;
}) {
  const props =
    status === "PRESENT"
      ? { variant: "success" as const, label: "Present" }
      : status === "INCOMPLETE"
        ? { variant: "warning" as const, label: "Incomplete" }
        : { variant: "secondary" as const, label: "Absent" };
  return (
    <span className="inline-flex items-center gap-1.5">
      <Badge variant={props.variant}>{props.label}</Badge>
      {closed && (
        <Badge variant="outline" className="text-[10px]">
          closed
        </Badge>
      )}
    </span>
  );
}

// ----------------------------------------------------------------------
// Misc
// ----------------------------------------------------------------------

function SummaryLoadingSkeleton() {
  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="flex items-center gap-4 p-5">
          <Skeleton className="h-14 w-14 rounded-full" />
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-64" />
          </div>
        </CardContent>
      </Card>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
      <Skeleton className="h-72 w-full" />
      <p className="flex items-center gap-2 text-xs text-muted-foreground">
        <Loader2 className="h-3 w-3 animate-spin" />
        Loading…
      </p>
    </div>
  );
}

function EmptyState({
  icon,
  title,
  message,
}: {
  icon: React.ReactNode;
  title: string;
  message: string;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center gap-2 px-6 py-16 text-center">
        <span className="rounded-full bg-muted p-3 text-muted-foreground">
          {icon}
        </span>
        <p className="text-base font-semibold">{title}</p>
        <p className="max-w-md text-sm text-muted-foreground">{message}</p>
      </CardContent>
    </Card>
  );
}

function DateField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <p className="mb-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <div className="relative">
        <input
          type="date"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={cn(
            "h-10 w-full rounded-md border border-input bg-background px-3 text-sm",
            value && "pr-9",
          )}
        />
        {value && (
          <button
            type="button"
            aria-label={`Clear ${label}`}
            title={`Clear ${label}`}
            onClick={() => onChange("")}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 inline-flex h-6 w-6 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}

function formatHours(totalSeconds: number): string {
  const hours = totalSeconds / 3600;
  return `${hours.toFixed(1)} h`;
}

function formatDuration(totalSeconds: number): string {
  if (totalSeconds <= 0) return "0m";
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  if (h <= 0) return `${m}m`;
  if (m <= 0) return `${h}h`;
  return `${h}h ${m}m`;
}
