import { createFileRoute } from "@tanstack/react-router";
import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import {
  ChevronDown,
  ChevronRight,
  FileText,
  Search,
} from "lucide-react";
import {
  type AttendanceSummaryItem,
  type Employee,
} from "@/api/dashboardApi";
import { useEmployees } from "@/contexts/EmployeesContext";
import { useAttendanceSummaries } from "@/contexts/AttendanceSummariesContext";
import { companyMatches } from "@/lib/auth";
import { matchesEmployeeName } from "@/lib/nameMatch";
import { SectionShell } from "@/components/dashboard/SectionShell";
import { EmployeeManagementTabs } from "@/components/dashboard/EmployeeManagementTabs";
import { DatePicker } from "@/components/dashboard/DatePicker";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
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
import { formatClock12, formatDateDash, formatDateKeyDash, formatTime12, parseTimestamp } from "@/lib/dateFormat";

export const Route = createFileRoute("/_dashboard/reports")({
  component: ReportsPage,
});

function ImageCell({
  url,
  archived,
  alt,
  borderClass,
  bgClass,
}: {
  url: string | null;
  archived: boolean;
  alt: string;
  borderClass: string;
  bgClass: string;
}) {
  const [previewPos, setPreviewPos] = useState<{ left: number; top: number } | null>(null);
  const canUseDom = typeof window !== "undefined" && typeof document !== "undefined";

  const positionPreview = useCallback((el: HTMLElement) => {
    if (!canUseDom) return;
    const rect = el.getBoundingClientRect();
    const viewportW = window.innerWidth;
    const viewportH = window.innerHeight;
    const gap = 12;
    const previewW = 248; // p-3 + (w-56)
    const previewH = 184; // p-3 + (h-40)
    const edge = 8;

    let left = rect.right + gap;
    if (left + previewW > viewportW - edge) {
      left = rect.left - gap - previewW;
    }
    if (left < edge) {
      left = Math.max(edge, Math.min(viewportW - previewW - edge, rect.left + rect.width / 2 - previewW / 2));
    }

    let top = rect.top + rect.height / 2 - previewH / 2;
    top = Math.max(edge, Math.min(viewportH - previewH - edge, top));

    setPreviewPos({ left, top });
  }, [canUseDom]);

  if (url) {
    return (
      <>
        <button
          type="button"
          className="relative block h-10 w-10 shrink-0 rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
          title={`Preview ${alt}`}
          onMouseEnter={(e) => positionPreview(e.currentTarget)}
          onMouseMove={(e) => positionPreview(e.currentTarget)}
          onMouseLeave={() => setPreviewPos(null)}
          onFocus={(e) => positionPreview(e.currentTarget)}
          onBlur={() => setPreviewPos(null)}
        >
          <img
            src={url}
            alt={alt}
            className={cn(
              "h-10 w-10 shrink-0 rounded-md border object-cover",
              borderClass,
            )}
            loading="lazy"
          />
        </button>
        {canUseDom && previewPos
          ? createPortal(
              <div
                className="pointer-events-none fixed z-[120]"
                style={{ left: `${previewPos.left}px`, top: `${previewPos.top}px` }}
                role="presentation"
              >
                <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-xl">
                  <div className="flex h-40 w-56 items-center justify-center overflow-hidden rounded-lg bg-slate-100">
                    <img
                      src={url}
                      alt=""
                      className="block max-h-full max-w-full object-contain"
                      loading="lazy"
                    />
                  </div>
                </div>
              </div>,
              document.body,
            )
          : null}
      </>
    );
  }
  if (archived) {
    return (
      <div
        title="Image archived"
        className={cn(
          "flex h-10 w-10 items-center justify-center rounded-md border border-dashed text-[9px] font-medium leading-tight",
          borderClass,
          bgClass,
        )}
      >
        Image
        <br />
        archived
      </div>
    );
  }
  return (
    <div
      className={cn(
        "h-10 w-10 rounded-md border border-dashed",
        borderClass,
        bgClass,
      )}
    />
  );
}

function findEmployeeForName(employees: Employee[], captureName: string): Employee | null {
  if (!captureName) return null;
  for (const employee of employees) {
    if (matchesEmployeeName(captureName, employee.name)) return employee;
  }
  return null;
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

function movementTypeClass(movementType: string): string {
  const value = movementType.trim().toLowerCase();
  if (value === "entry") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  if (value === "final exit") return "border-rose-200 bg-rose-50 text-rose-700";
  if (value === "break out") return "border-amber-200 bg-amber-50 text-amber-700";
  if (value === "break in") return "border-sky-200 bg-sky-50 text-sky-700";
  return "border-slate-200 bg-slate-100 text-slate-700";
}

function cameraDisplayName(cameraName?: string | null, cameraId?: string | null): string {
  const raw = (cameraName || cameraId || "").trim();
  if (!raw) return "—";
  return raw.toLowerCase() === "api ingest" ? "Eye Camera" : raw;
}

function MovementHistoryPanel({ item }: { item: AttendanceSummaryItem }) {
  const history = [...(item.movement_history ?? [])].sort((a, b) => {
    const left = parseTimestamp(a.timestamp_iso)?.getTime() ?? 0;
    const right = parseTimestamp(b.timestamp_iso)?.getTime() ?? 0;
    return left - right;
  });

  if (history.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-200 bg-white px-4 py-5 text-sm text-slate-600">
        No break timeline snapshots available for this day.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-300 bg-white">
      <table className="w-full table-fixed border-collapse text-sm">
        <colgroup>
          <col className="w-[11%]" />
          <col className="w-[17%]" />
          <col className="w-[16%]" />
          <col className="w-[17%]" />
          <col className="w-[17%]" />
          <col className="w-[12%]" />
        </colgroup>
        <thead>
          <tr className="border-b border-slate-300 bg-slate-50/80">
            <th className="border-b border-r border-slate-300 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">
              Event
            </th>
            <th className="border-b border-r border-slate-300 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">
              Type
            </th>
            <th className="border-b border-r border-slate-300 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">
              Date
            </th>
            <th className="border-b border-r border-slate-300 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">
              Time
            </th>
            <th className="border-b border-r border-slate-300 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">
              Camera
            </th>
            <th className="border-b border-slate-300 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">
              Snapshot
            </th>
          </tr>
        </thead>
        <tbody>
          {history.map((event, index) => {
            const dt = parseTimestamp(event.timestamp_iso);
            return (
              <tr key={event.event_id || `${event.movement_type}-${index}`} className="border-b border-slate-200 last:border-b-0">
                <td className="border-r border-slate-300 px-3 py-2 font-medium text-slate-600">
                  {index + 1}
                </td>
                <td className="border-r border-slate-300 px-3 py-2">
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold",
                      movementTypeClass(event.movement_type),
                    )}
                  >
                    {event.movement_type}
                  </span>
                </td>
                <td className="border-r border-slate-300 px-3 py-2 font-medium text-slate-700">
                  {dt ? formatDateDash(dt) : formatDateKeyDash(item.date)}
                </td>
                <td className="border-r border-slate-300 px-3 py-2 font-medium text-slate-700">
                  {dt ? formatTime12(dt) : formatClock12(event.timestamp)}
                </td>
                <td className="border-r border-slate-300 px-3 py-2 text-slate-600">
                  {cameraDisplayName(event.camera_name, event.camera_id)}
                </td>
                <td className="px-3 py-2">
                  <ImageCell
                    url={event.snapshot_url ?? null}
                    archived={Boolean(event.snapshot_archived)}
                    alt={`${item.name} ${event.movement_type} snapshot`}
                    borderClass="border-slate-200 text-slate-700"
                    bgClass="bg-slate-50"
                  />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function ReportsPage() {
  const { employees, scopedCompany } = useEmployees();
  const isCompanyScoped = scopedCompany !== null;

  const [selectedEmployee, setSelectedEmployee] = useState<string>("all");
  const [selectedCompany, setSelectedCompany] = useState<string>(
    isCompanyScoped ? (scopedCompany as string) : "all",
  );
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");

  // Pull the (cached + shared) attendance dataset from the provider instead
  // of fetching here. Tab switches reuse the cache so first paint is
  // instant; a single shared poll keeps it fresh.
  const {
    items: attendanceItems,
    loading,
    error,
  } = useAttendanceSummaries();

  const companyOptions = useMemo(
    () => Array.from(new Set(employees.map((e) => e.company))).sort(),
    [employees],
  );

  // For HR users, drop any attendance row that doesn't belong to their company.
  // This page fetches its own attendance data, so the context-level scoping
  // doesn't apply — we have to gate it here too.
  const scopedAttendanceItems = useMemo<AttendanceSummaryItem[]>(() => {
    if (!scopedCompany) return attendanceItems;
    return attendanceItems.filter((item) => {
      const itemCompany = item.company ?? findEmployeeForName(employees, item.name)?.company ?? null;
      return companyMatches(itemCompany, scopedCompany);
    });
  }, [attendanceItems, employees, scopedCompany]);

  const employeesForSelectedCompany = useMemo(
    () =>
      selectedCompany === "all"
        ? employees
        : employees.filter((e) => e.company === selectedCompany),
    [employees, selectedCompany],
  );

  useEffect(() => {
    if (selectedEmployee === "all") return;
    const stillVisible = employeesForSelectedCompany.some(
      (e) => e.employeeId === selectedEmployee,
    );
    if (!stillVisible) setSelectedEmployee("all");
  }, [employeesForSelectedCompany, selectedEmployee]);

  const selectedEmployeeObj = useMemo(
    () => employees.find((e) => e.employeeId === selectedEmployee) ?? null,
    [employees, selectedEmployee],
  );

  const filteredItems = useMemo(() => {
    return scopedAttendanceItems.filter((item) => {
      const matchedEmployee = findEmployeeForName(employees, item.name);

      if (selectedEmployee !== "all") {
        if (!selectedEmployeeObj) return false;
        if (matchedEmployee?.employeeId !== selectedEmployee) return false;
      } else if (selectedCompany !== "all") {
        const rowCompany = item.company ?? matchedEmployee?.company ?? null;
        if (!companyMatches(rowCompany, selectedCompany)) return false;
      }

      if (startDate && item.date < startDate) return false;
      if (endDate && item.date > endDate) return false;

      return true;
    });
  }, [
    scopedAttendanceItems,
    employees,
    selectedEmployee,
    selectedEmployeeObj,
    selectedCompany,
    startDate,
    endDate,
  ]);

  const employeeFilterOptions = useMemo(
    () => [
      { value: "all", label: "All Employees" },
      ...[...employeesForSelectedCompany]
        .sort((a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }))
        .map((employee) => ({
        value: employee.employeeId,
        label: employee.name,
      })),
    ],
    [employeesForSelectedCompany],
  );
  const companyFilterOptions = useMemo(
    () => [
      { value: "all", label: "All Companies" },
      ...companyOptions.map((company) => ({ value: company, label: company })),
    ],
    [companyOptions],
  );

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <SectionShell
        title="Reports"
        icon={<FileText className="h-5 w-5 text-primary" />}
        className="animate-fade-in-up"
        inlineActions
        actions={<EmployeeManagementTabs />}
      >
        <Card className="flex min-h-0 flex-1 flex-col">
          <CardContent className="flex min-h-0 flex-1 flex-col gap-3 px-0 pt-4">
            <div className="flex flex-col gap-3 border-b border-slate-200 pb-3 md:flex-row md:items-center md:justify-between">
              {/* Mobile: each filter group is its own full-width row with a
                  fixed-width label, so all controls (selects + date pickers)
                  line up at the same right edge. From sm+ they reflow inline. */}
              <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
                <Search className="hidden h-5 w-5 text-primary sm:block" />

                <div className="flex w-full items-center gap-2 sm:w-auto">
                  <span className="w-[100px] shrink-0 whitespace-nowrap text-sm font-semibold text-sky-900 sm:w-auto">
                    Employees
                  </span>
                  <SearchableSelect
                    value={selectedEmployee}
                    onValueChange={setSelectedEmployee}
                    options={employeeFilterOptions}
                    clearValue="all"
                    placeholder="All Employees"
                    className="h-9 min-w-0 flex-1 border-sky-200 focus-visible:ring-sky-300 sm:w-[150px] sm:flex-initial md:w-[160px]"
                  />
                </div>

                {/* Company picker is admin-only — HR users are scoped to one
                    company already, so showing it (or its locked badge) is
                    redundant. The data filter still uses scopedCompany. */}
                {!isCompanyScoped ? (
                  <div className="flex w-full items-center gap-2 sm:w-auto">
                    <span className="w-[100px] shrink-0 whitespace-nowrap text-sm font-semibold text-[#393E2E] sm:w-auto">
                      Company
                    </span>
                    <SearchableSelect
                      value={selectedCompany}
                      onValueChange={setSelectedCompany}
                      options={companyFilterOptions}
                      clearValue="all"
                      placeholder="All Companies"
                      className="h-9 min-w-0 flex-1 border-indigo-200 focus-visible:ring-indigo-300 sm:w-[135px] sm:flex-initial md:w-[145px]"
                    />
                  </div>
                ) : null}

                {/* Date Range — label gets its own row on mobile, then two
                    full-width date pickers stack underneath so they don't
                    overflow narrow viewports. From sm+ everything goes inline. */}
                <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-2">
                  <span className="whitespace-nowrap text-sm font-semibold text-emerald-900">
                    Date Range
                  </span>
                  <DatePicker
                    value={startDate}
                    onChange={setStartDate}
                    className="w-full sm:w-[215px]"
                  />
                  <DatePicker
                    value={endDate}
                    onChange={setEndDate}
                    className="w-full sm:w-[215px]"
                  />
                </div>

                {(startDate ||
                  endDate ||
                  selectedEmployee !== "all" ||
                  (!isCompanyScoped && selectedCompany !== "all")) ? (
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    className="h-9 self-start px-3 text-xs sm:self-auto"
                    onClick={() => {
                      setSelectedEmployee("all");
                      // HR users stay locked to their company.
                      if (!isCompanyScoped) setSelectedCompany("all");
                      setStartDate("");
                      setEndDate("");
                    }}
                  >
                    Clear filters
                  </Button>
                ) : null}
              </div>
            </div>

            {error ? (
              <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
                {error}
              </div>
            ) : null}

            <div className="min-h-0 flex-1 overflow-hidden">
              <ReportTable
                items={filteredItems}
                employees={employees}
                loading={loading}
              />
            </div>
          </CardContent>
        </Card>
      </SectionShell>
    </div>
  );
}

function ReportTable({
  items,
  employees,
  loading,
}: {
  items: AttendanceSummaryItem[];
  employees: Employee[];
  loading: boolean;
}) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  useEffect(() => {
    setExpandedRows((prev) => {
      const valid = new Set(items.map((item) => item.id));
      const next = new Set<string>();
      for (const rowId of prev) {
        if (valid.has(rowId)) next.add(rowId);
      }
      return next;
    });
  }, [items]);

  const toggleExpanded = useCallback((rowId: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(rowId)) next.delete(rowId);
      else next.add(rowId);
      return next;
    });
  }, []);

  return (
    <Table className="min-w-[1080px] [&_td]:border-r-slate-300 [&_th]:border-r-slate-300">
      <TableHeader>
        <TableRow className="bg-slate-50/60 hover:bg-slate-50/80">
          <TableHead className="w-[240px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-sky-700 last:border-r-0">Employee Name</TableHead>
          <TableHead className="w-[90px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-indigo-700 last:border-r-0">Company</TableHead>
          <TableHead className="w-[95px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-emerald-700 last:border-r-0">Date</TableHead>
          <TableHead className="w-[80px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-sky-700 last:border-r-0">Entry Image</TableHead>
          <TableHead className="w-[95px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-sky-700 last:border-r-0">Entry Time</TableHead>
          <TableHead className="w-[80px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-rose-700 last:border-r-0">Exit Image</TableHead>
          <TableHead className="w-[110px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-rose-700 last:border-r-0">Exit Time</TableHead>
          <TableHead className="w-[100px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-amber-700 last:border-r-0">Total Break</TableHead>
          <TableHead className="w-[130px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-indigo-700 last:border-r-0">Total Working</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.length === 0 ? (
          <TableRow>
            <TableCell colSpan={9} className="py-10 text-center text-muted-foreground">
              {loading ? "Loading report…" : "No attendance records match the current filters."}
            </TableCell>
          </TableRow>
        ) : (
          items.map((item) => {
            const emp = findEmployeeForName(employees, item.name);
            const company = item.company ?? emp?.company ?? "—";
            const isExpanded = expandedRows.has(item.id);
            return (
              <Fragment key={item.id}>
                <TableRow className="transition-colors hover:bg-slate-50/60">
                  <TableCell className="border-r border-slate-200 py-2 align-middle last:border-r-0">
                    <div className="flex min-w-0 items-start gap-2">
                      <button
                        type="button"
                        onClick={() => toggleExpanded(item.id)}
                        className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-100"
                        title={isExpanded ? "Hide break timeline" : "Show break timeline"}
                        aria-label={isExpanded ? "Collapse break history" : "Expand break history"}
                        aria-expanded={isExpanded}
                      >
                        {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      </button>
                      <Avatar className="h-8 w-8 shrink-0 border border-sky-200 bg-sky-50">
                        {emp?.imageUrl ? (
                          <AvatarImage
                            src={emp.imageUrl}
                            alt={item.name}
                            className="object-cover"
                          />
                        ) : null}
                        <AvatarFallback className="text-xs font-semibold text-sky-700">
                          {initials(item.name)}
                        </AvatarFallback>
                      </Avatar>
                      <span className="min-w-0 break-words whitespace-normal font-medium leading-tight text-foreground">
                        {item.name}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="whitespace-nowrap border-r border-slate-200 py-2 align-middle font-medium text-indigo-700 last:border-r-0">
                    {company}
                  </TableCell>
                  <TableCell className="whitespace-nowrap border-r border-slate-200 py-2 align-middle font-medium text-emerald-700 last:border-r-0">
                    {formatDateKeyDash(item.date)}
                  </TableCell>
                  <TableCell className="border-r border-slate-200 py-2 align-middle last:border-r-0">
                    <ImageCell
                      url={item.entry_image_url}
                      archived={Boolean(item.entry_image_archived)}
                      alt={`${item.name} entry`}
                      borderClass="border-sky-200 text-sky-700"
                      bgClass="bg-sky-50/40"
                    />
                  </TableCell>
                  <TableCell className="whitespace-nowrap border-r border-slate-200 py-2 align-middle text-sky-700 last:border-r-0">
                    {formatClock12(item.entry_time)}
                  </TableCell>
                  <TableCell className="border-r border-slate-200 py-2 align-middle last:border-r-0">
                    <ImageCell
                      url={item.exit_image_url}
                      archived={Boolean(item.exit_image_archived)}
                      alt={`${item.name} exit`}
                      borderClass="border-rose-200 text-rose-700"
                      bgClass="bg-rose-50/40"
                    />
                  </TableCell>
                  <TableCell className="whitespace-nowrap border-r border-slate-200 py-2 align-middle text-rose-700 last:border-r-0">
                    {item.missing_checkout ? (
                      <span title="Missing checkout — admin correction recommended" className="font-medium text-amber-700">
                        Missing checkout
                      </span>
                    ) : (
                      formatClock12(item.exit_time)
                    )}
                  </TableCell>
                  <TableCell className="whitespace-nowrap border-r border-slate-200 py-2 align-middle font-semibold text-amber-700 last:border-r-0">
                    {item.total_break_time ?? "—"}
                  </TableCell>
                  <TableCell className="whitespace-nowrap border-r border-slate-200 py-2 align-middle font-semibold text-indigo-700 last:border-r-0">
                    {item.total_working_hours ?? item.total_hours}
                  </TableCell>
                </TableRow>
                {isExpanded ? (
                  <TableRow className="bg-slate-50/40 hover:bg-slate-50/40">
                    <TableCell colSpan={9} className="border-r-0 border-t-0 px-4 py-4 last:border-r-0">
                      <div className="mb-3">
                        <p className="text-sm font-semibold text-slate-800">
                          Break History & Movement Timeline
                        </p>
                      </div>
                      <MovementHistoryPanel item={item} />
                    </TableCell>
                  </TableRow>
                ) : null}
              </Fragment>
            );
          })
        )}
      </TableBody>
    </Table>
  );
}
