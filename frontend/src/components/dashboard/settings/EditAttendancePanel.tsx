import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarCheck, Loader2, RefreshCw, Save, Trash2 } from "lucide-react";

import {
  type AttendanceCorrection,
  type AttendanceStatusFull,
  type AttendanceSummaryItem,
  deleteAttendanceCorrection,
  getAttendanceLogs,
  listAttendanceCorrections,
  upsertAttendanceCorrection,
} from "@/api/dashboardApi";
import { useEmployees } from "@/contexts/EmployeesContext";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SearchableSelect } from "@/components/ui/searchable-select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

const STATUS_CHOICES: AttendanceStatusFull[] = [
  "Present",
  "Late",
  "Early Exit",
  "Absent",
  "WFH",
  "Paid Leave",
  "LOP",
  "Holiday",
];

const MONTH_OPTIONS = [
  { value: "01", label: "Jan" },
  { value: "02", label: "Feb" },
  { value: "03", label: "Mar" },
  { value: "04", label: "Apr" },
  { value: "05", label: "May" },
  { value: "06", label: "Jun" },
  { value: "07", label: "Jul" },
  { value: "08", label: "Aug" },
  { value: "09", label: "Sep" },
  { value: "10", label: "Oct" },
  { value: "11", label: "Nov" },
  { value: "12", label: "Dec" },
] as const;

// User-facing label override for the dropdown. The wire/API value stays
// "Holiday" so the backend's status_override whitelist keeps working.
const STATUS_DROPDOWN_LABEL: Partial<Record<AttendanceStatusFull, string>> = {
  Holiday: "Company Leave",
};

const STATUS_TEXT_CLASS: Record<AttendanceStatusFull, string> = {
  Present: "text-emerald-700",
  Late: "text-amber-700",
  "Early Exit": "text-orange-700",
  Absent: "text-rose-700",
  WFH: "text-violet-700",
  "Paid Leave": "text-blue-700",
  LOP: "text-rose-800",
  Holiday: "text-sky-700",
};

type DayRow = {
  date: string;
  dayLabel: string;
  weekday: string;
  isFuture: boolean;
  effective: AttendanceSummaryItem | null;
  // Local edit buffer; null when the day has no pending edits.
  draft: DayDraft | null;
};

// Drafts now only carry the override status. Paid Leave / LOP / WFH flags
// are derived from the override on save (see `flagsFromStatus`) — there's
// no separate UI control for them anymore since "Override Status" already
// expresses the same intent.
type DayDraft = {
  status_override: AttendanceStatusFull | null;
};

function flagsFromStatus(status: AttendanceStatusFull | null): {
  paid_leave: boolean;
  lop: boolean;
  wfh: boolean;
} {
  return {
    paid_leave: status === "Paid Leave",
    lop: status === "LOP",
    wfh: status === "WFH",
  };
}

function monthStartEnd(monthKey: string): { start: string; end: string; days: string[] } {
  const [year, month] = monthKey.split("-").map(Number);
  const endDate = new Date(year, month, 0);
  const days: string[] = [];
  for (let d = 1; d <= endDate.getDate(); d += 1) {
    const iso = `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    days.push(iso);
  }
  return {
    start: days[0],
    end: days[days.length - 1],
    days,
  };
}

function todayKey(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function thisMonthKey(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

function monthParts(monthKey: string): { year: string; month: string } {
  const match = monthKey.match(/^(\d{4})-(0[1-9]|1[0-2])$/);
  if (match) {
    return { year: match[1], month: match[2] };
  }
  const [year, month] = thisMonthKey().split("-");
  return { year, month };
}

function weekdayLabel(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("en-US", { weekday: "short" });
}

function correctionToDraft(correction: AttendanceCorrection | undefined): DayDraft | null {
  if (!correction) return null;
  if (!correction.status_override) return null;
  return { status_override: correction.status_override };
}

export function EditAttendancePanel() {
  const { employees } = useEmployees();
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string>("");
  const [selectedMonth, setSelectedMonth] = useState<string>(thisMonthKey());
  const monthKey = selectedMonth || thisMonthKey();
  const { year: selectedYearPart, month: selectedMonthPart } = useMemo(
    () => monthParts(monthKey),
    [monthKey],
  );
  const yearOptions = useMemo(() => {
    const currentYear = new Date().getFullYear();
    return Array.from({ length: 31 }, (_, idx) => {
      const year = String(currentYear + 2 - idx);
      return { value: year, label: year };
    });
  }, []);
  const employeeFilterOptions = useMemo(
    () => employees.map((emp) => ({ value: emp.employeeId, label: emp.name })),
    [employees],
  );

  const selectedEmployee = useMemo(
    () => employees.find((e) => e.employeeId === selectedEmployeeId) ?? null,
    [employees, selectedEmployeeId],
  );

  const [summaries, setSummaries] = useState<AttendanceSummaryItem[]>([]);
  const [corrections, setCorrections] = useState<AttendanceCorrection[]>([]);
  const [loading, setLoading] = useState(false);
  const [savingDate, setSavingDate] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, DayDraft | null>>({});

  const { start, end, days } = useMemo(() => monthStartEnd(monthKey), [monthKey]);

  const refresh = useCallback(async () => {
    if (!selectedEmployee) {
      setSummaries([]);
      setCorrections([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [logsResp, corrList] = await Promise.all([
        getAttendanceLogs({ name: selectedEmployee.name, start, end }),
        listAttendanceCorrections({ name: selectedEmployee.name, start, end }),
      ]);
      setSummaries(logsResp.items);
      setCorrections(corrList);
      const seed: Record<string, DayDraft | null> = {};
      for (const corr of corrList) {
        seed[corr.date] = correctionToDraft(corr);
      }
      setDrafts(seed);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load attendance data");
    } finally {
      setLoading(false);
    }
  }, [selectedEmployee, start, end]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!feedback) return;
    const timer = window.setTimeout(() => {
      setFeedback(null);
    }, 2000);
    return () => window.clearTimeout(timer);
  }, [feedback]);

  // Per-day rows for the current month, joined with API summaries + drafts.
  const today = todayKey();
  const rows: DayRow[] = useMemo(() => {
    const summaryByDate = new Map<string, AttendanceSummaryItem>();
    for (const item of summaries) summaryByDate.set(item.date, item);
    return days.map((date) => ({
      date,
      dayLabel: date.slice(8),
      weekday: weekdayLabel(date),
      isFuture: date > today,
      effective: summaryByDate.get(date) ?? null,
      draft: drafts[date] ?? null,
    }));
  }, [days, summaries, drafts, today]);

  // Monthly summary, computed off the merged effective values so HR sees
  // the impact of saved edits without an extra refresh.
  const monthly = useMemo(() => {
    let present = 0;
    let absent = 0;
    let late = 0;
    let earlyExit = 0;
    let paid = 0;
    let lop = 0;
    let wfh = 0;
    let holiday = 0;
    for (const r of rows) {
      if (r.isFuture || !r.effective) continue;
      const status = r.effective.status;
      if (status === "Present") present += 1;
      else if (status === "Late") {
        present += 1;
        late += 1;
      } else if (status === "Early Exit") {
        present += 1;
        earlyExit += 1;
      } else if (status === "Absent") absent += 1;
      else if (status === "Paid Leave") paid += 1;
      else if (status === "LOP") lop += 1;
      else if (status === "WFH") wfh += 1;
      else if (status === "Holiday") holiday += 1;
    }
    return { present, absent, late, earlyExit, paid, lop, wfh, holiday };
  }, [rows]);

  const updateDraft = (date: string, status: AttendanceStatusFull | null) => {
    setDrafts((prev) => ({ ...prev, [date]: status ? { status_override: status } : null }));
  };

  const saveRow = async (date: string) => {
    if (!selectedEmployee) return;
    const draft = drafts[date];
    if (!draft) return;
    setSavingDate(date);
    setError(null);
    setFeedback(null);
    try {
      const flags = flagsFromStatus(draft.status_override);
      await upsertAttendanceCorrection({
        name: selectedEmployee.name,
        date,
        status_override: draft.status_override,
        ...flags,
      });
      setFeedback(`Saved ${date}`);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save correction");
    } finally {
      setSavingDate(null);
    }
  };

  const clearRow = async (date: string) => {
    if (!selectedEmployee) return;
    setSavingDate(date);
    setError(null);
    setFeedback(null);
    try {
      await deleteAttendanceCorrection(selectedEmployee.name, date);
      setFeedback(`Cleared correction for ${date}`);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to clear correction");
    } finally {
      setSavingDate(null);
    }
  };

  const hasCorrection = (date: string): boolean =>
    corrections.some((c) => c.date === date);

  return (
    <div className="flex h-full min-h-0 flex-col">
      {/* Top region: heading + filters + summary. Sits as a fixed-height
          flex child so only the table region below scrolls. */}
      <div className="flex shrink-0 flex-col gap-3 bg-white pb-3">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
          <CalendarCheck className="h-5 w-5 text-primary" />
          Attendance Corrections
        </h2>

        <div className="flex flex-wrap items-end gap-4 rounded-2xl border border-slate-200 bg-slate-50/50 p-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-semibold text-sky-900">
              Employee
            </label>
            <SearchableSelect
              value={selectedEmployeeId}
              onValueChange={setSelectedEmployeeId}
              options={employeeFilterOptions}
              clearValue=""
              placeholder="Select employee"
              className="h-9 w-[220px] border-sky-200 focus-visible:ring-sky-300"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm font-semibold text-emerald-900">
              Choose Month
            </label>
            <div className="flex w-[230px] items-center gap-2">
              <SearchableSelect
                value={selectedMonthPart}
                onValueChange={(value) => setSelectedMonth(`${selectedYearPart}-${value}`)}
                options={MONTH_OPTIONS}
                placeholder="Month"
                showClear={false}
                className="h-9 w-[108px] border-emerald-200 focus-visible:ring-emerald-300"
                dropdownClassName="max-h-56"
              />
              <SearchableSelect
                value={selectedYearPart}
                onValueChange={(value) => setSelectedMonth(`${value}-${selectedMonthPart}`)}
                options={yearOptions}
                placeholder="Year"
                showClear={false}
                className="h-9 w-[114px] border-emerald-200 focus-visible:ring-emerald-300"
                dropdownClassName="max-h-56"
              />
            </div>
          </div>

          <div className="ml-auto flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => void refresh()}
              disabled={loading || !selectedEmployee}
              className="h-9 gap-1.5"
            >
              <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
              Refresh
            </Button>
          </div>
        </div>

        {selectedEmployee ? (
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-xs text-slate-700">
            <SummaryStat label="Present" value={monthly.present} className="text-emerald-700" />
            <Divider />
            <SummaryStat label="Absent" value={monthly.absent} className="text-rose-700" />
            <Divider />
            <SummaryStat label="Late" value={monthly.late} className="text-amber-700" />
            <Divider />
            <SummaryStat label="Early Exit" value={monthly.earlyExit} className="text-orange-700" />
            <Divider />
            <SummaryStat label="Paid Leave" value={monthly.paid} className="text-blue-700" />
            <Divider />
            <SummaryStat label="LOP" value={monthly.lop} className="text-rose-800" />
            <Divider />
            <SummaryStat label="WFH" value={monthly.wfh} className="text-violet-700" />
            <Divider />
            <SummaryStat label="Holiday" value={monthly.holiday} className="text-sky-700" />
          </div>
        ) : null}

        {error ? (
          <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error}
          </div>
        ) : null}
        {feedback ? (
          <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
            {feedback}
          </div>
        ) : null}
      </div>

      {/* Scroll body: only the table data scrolls. The Table component
          already provides an inner scroll wrapper and sticky `th`s, so we
          just need to give it a bounded height via flex. */}
      <div className="mt-3 min-h-0 flex-1">
        {!selectedEmployee ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/40 px-6 py-12 text-center text-sm text-slate-500">
            Select an employee to view and edit their attendance for the month.
          </div>
        ) : (
          <Table className="min-w-[680px]">
            <TableHeader>
              <TableRow className="bg-slate-50/60">
                <TableHead className="w-20">Date</TableHead>
                <TableHead className="w-20">Day</TableHead>
                <TableHead className="w-[160px]">Current Status</TableHead>
                <TableHead className="w-[200px]">Override Status</TableHead>
                <TableHead className="w-[160px] text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
              <TableBody>
                {rows.map((row) => {
                  const draft = row.draft;
                  const effectiveStatus = row.effective?.status ?? null;
                  const isCorrected = hasCorrection(row.date);
                  const draftDirty = Boolean(draft);
                  const isSaving = savingDate === row.date;
                  return (
                    <TableRow
                      key={row.date}
                      className={cn(
                        "transition-colors",
                        row.isFuture && "opacity-50",
                        isCorrected && "bg-amber-50/40",
                      )}
                    >
                      <TableCell className="font-mono text-slate-700">{row.dayLabel}</TableCell>
                      <TableCell className="text-slate-500">{row.weekday}</TableCell>
                      <TableCell>
                        {effectiveStatus ? (
                          <span
                            className={cn(
                              "text-sm font-semibold",
                              STATUS_TEXT_CLASS[effectiveStatus] ?? "text-slate-700",
                            )}
                          >
                            {effectiveStatus}
                          </span>
                        ) : (
                          <span className="text-xs italic text-slate-400">No record</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Select
                          value={draft?.status_override ?? "__keep__"}
                          onValueChange={(value) =>
                            updateDraft(
                              row.date,
                              value === "__keep__" ? null : (value as AttendanceStatusFull),
                            )
                          }
                          disabled={row.isFuture}
                        >
                          <SelectTrigger className="h-8 w-full border-slate-200">
                            <SelectValue placeholder="Keep current" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="__keep__">Keep current</SelectItem>
                            {STATUS_CHOICES.map((s) => (
                              <SelectItem key={s} value={s}>
                                {STATUS_DROPDOWN_LABEL[s] ?? s}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            className="h-8 gap-1 px-2"
                            disabled={!draftDirty || isSaving || row.isFuture}
                            onClick={() => void saveRow(row.date)}
                          >
                            {isSaving ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <Save className="h-3.5 w-3.5" />
                            )}
                            Save
                          </Button>
                          {isCorrected ? (
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="h-8 gap-1 px-2 text-rose-600 hover:bg-rose-50 hover:text-rose-700"
                              disabled={isSaving}
                              onClick={() => void clearRow(row.date)}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                              Clear
                            </Button>
                          ) : null}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}

function SummaryStat({
  label,
  value,
  className,
}: {
  label: string;
  value: number;
  className: string;
}) {
  return (
    <span className="inline-flex items-baseline gap-1">
      <span className="font-semibold text-slate-900">{label}:</span>
      <span className={cn("font-bold", className)}>{value}</span>
    </span>
  );
}

function Divider() {
  return <span aria-hidden="true" className="text-slate-300">|</span>;
}
