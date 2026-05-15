import { createFileRoute, redirect } from "@tanstack/react-router";
import { getCurrentRole } from "@/lib/auth";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Download, RefreshCw, Search, Users } from "lucide-react";
import {
  getSnapshotLogs,
  listCameras,
  type Employee,
  type SnapshotLogItem,
} from "@/api/dashboardApi";
import { useEmployees } from "@/contexts/EmployeesContext";
import { matchesEmployeeName } from "@/lib/nameMatch";
import { SectionShell } from "@/components/dashboard/SectionShell";
import { DatePicker } from "@/components/dashboard/DatePicker";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { cn } from "@/lib/utils";
import { formatDateDash, formatTime12, parseTimestamp } from "@/lib/dateFormat";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export const Route = createFileRoute("/_dashboard/requests")({
  beforeLoad: () => {
    if (getCurrentRole() !== "admin") {
      throw redirect({ to: "/home" });
    }
  },
  component: LiveCapturesPage,
});

const POLL_INTERVAL_MS = 5_000;

function snapshotLocalDateKey(isoTimestamp: string): string {
  const d = parseTimestamp(isoTimestamp);
  if (!d) return "";
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${month}-${day}`;
}

function findEmployeeForName(
  employees: Employee[],
  captureName: string,
): Employee | null {
  if (!captureName) return null;
  for (const employee of employees) {
    if (matchesEmployeeName(captureName, employee.name)) return employee;
  }
  return null;
}

function csvEscape(value: string | number | null | undefined): string {
  const text = String(value ?? "");
  if (text.includes(",") || text.includes("\"") || text.includes("\n")) {
    return `"${text.replace(/"/g, "\"\"")}"`;
  }
  return text;
}

function downloadCsv(rows: string[][], filename: string) {
  const csv = rows.map((row) => row.map(csvEscape).join(",")).join("\n");
  // Leading BOM (\uFEFF) tells Excel the file is UTF-8 so characters like "—"
  // (U+2014) render correctly instead of as "â€"".
  const blob = new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function SnapshotThumb({ src, alt }: { src: string; alt: string }) {
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

  return (
    <>
      <button
        type="button"
        className="relative block h-14 w-14 shrink-0 rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
        title={`Preview ${alt}`}
        onMouseEnter={(e) => positionPreview(e.currentTarget)}
        onMouseMove={(e) => positionPreview(e.currentTarget)}
        onMouseLeave={() => setPreviewPos(null)}
        onFocus={(e) => positionPreview(e.currentTarget)}
        onBlur={() => setPreviewPos(null)}
      >
        <img
          src={src}
          alt={alt}
          className="h-14 w-14 shrink-0 rounded-md border border-sky-200 object-cover"
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
                    src={src}
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

function LiveCapturesPage() {
  const { employees } = useEmployees();

  const [selectedEmployee, setSelectedEmployee] = useState<string>("all");
  const [selectedCompany, setSelectedCompany] = useState<string>("all");
  const [selectedDate, setSelectedDate] = useState<string>("");

  const [snapshotItems, setSnapshotItems] = useState<SnapshotLogItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  // Yellow "new capture just landed" indicator. Flashes ON for ~2 s each
  // time a fresh snapshot row arrives (highest ID advanced between
  // polls); stays OFF the rest of the time so the operator doesn't see
  // a constant glow. Mirrors the sidebar Live Captures dot — having it
  // inline on the page itself means the operator gets the same feedback
  // without glancing away to the sidebar.
  const [newCapturePulse, setNewCapturePulse] = useState(false);
  const [newCaptureCount, setNewCaptureCount] = useState(0);
  const newestIdRef = useRef<number | null>(null);
  const pulseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Lookup map cam-id → friendly name (e.g. "Work Place") so the table
  // can show what the operator typed in Add Camera instead of the
  // opaque generated cam-id.
  const [cameraNamesById, setCameraNamesById] = useState<Record<string, string>>({});
  const [cameraUsecaseById, setCameraUsecaseById] = useState<Record<string, string>>({});
  const activeRef = useRef(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Load camera names once — cameras are admin-CRUD only, so we don't
  // need to keep this in sync minute-by-minute. A page reload picks up
  // any rename, which is the same UX the cameras list itself has.
  useEffect(() => {
    let cancelled = false;
    void listCameras()
      .then((cameras) => {
        if (cancelled) return;
        const map: Record<string, string> = {};
        const usecaseMap: Record<string, string> = {};
        for (const c of cameras) map[c.id] = c.name;
        for (const c of cameras) usecaseMap[c.id] = c.type;
        setCameraNamesById(map);
        setCameraUsecaseById(usecaseMap);
      })
      .catch(() => {
        // Non-fatal: the column simply falls back to showing the raw
        // camera_id, which is at least useful enough for an admin
        // debugging a routing problem.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const companyOptions = useMemo(
    () => Array.from(new Set(employees.map((employee) => employee.company))).sort(),
    [employees],
  );

  const employeesForSelectedCompany = useMemo(
    () =>
      selectedCompany === "all"
        ? employees
        : employees.filter((employee) => employee.company === selectedCompany),
    [employees, selectedCompany],
  );
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

  useEffect(() => {
    if (selectedEmployee === "all") return;
    const stillVisible = employeesForSelectedCompany.some(
      (employee) => employee.employeeId === selectedEmployee,
    );
    if (!stillVisible) setSelectedEmployee("all");
  }, [employeesForSelectedCompany, selectedEmployee]);

  const fetchData = useCallback(
    async ({ manual = false }: { manual?: boolean } = {}) => {
      if (manual) setRefreshing(true);
      try {
        const snapsResult = await getSnapshotLogs();
        if (!activeRef.current) return;
        // Detect fresh captures by comparing the highest snapshot id
        // against the previous poll. The very first poll just records
        // the baseline so a page-load with old data doesn't flash the
        // indicator — only genuinely new rows since the operator
        // started watching the page light it up.
        const newestThisPoll = snapsResult.items.reduce(
          (max, it) => (it.id > max ? it.id : max),
          0,
        );
        if (newestIdRef.current === null) {
          newestIdRef.current = newestThisPoll;
        } else if (newestThisPoll > newestIdRef.current) {
          const added = snapsResult.items.filter(
            (it) => it.id > (newestIdRef.current ?? 0),
          ).length;
          newestIdRef.current = newestThisPoll;
          setNewCaptureCount(added);
          setNewCapturePulse(true);
          if (pulseTimerRef.current) clearTimeout(pulseTimerRef.current);
          pulseTimerRef.current = setTimeout(() => {
            if (activeRef.current) setNewCapturePulse(false);
            pulseTimerRef.current = null;
          }, 2_000);
        }
        setSnapshotItems(snapsResult.items);
        setError(null);
        setLastUpdated(new Date());
      } catch (err) {
        if (!activeRef.current) return;
        setError(err instanceof Error ? err.message : "Failed to load records");
      } finally {
        if (activeRef.current) {
          setLoading(false);
          if (manual) setRefreshing(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    activeRef.current = true;
    setLoading(true);
    void fetchData();
    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(() => void fetchData(), POLL_INTERVAL_MS);
    return () => {
      activeRef.current = false;
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (pulseTimerRef.current) clearTimeout(pulseTimerRef.current);
    };
  }, [fetchData]);

  const handleRefresh = useCallback(async () => {
    await fetchData({ manual: true });
  }, [fetchData]);

  const selectedEmployeeObj = useMemo(
    () => employees.find((employee) => employee.employeeId === selectedEmployee) ?? null,
    [employees, selectedEmployee],
  );

  const rowPasses = useCallback(
    (rowName: string, rowDateKey: string) => {
      if (selectedDate && rowDateKey !== selectedDate) return false;

      const matchedEmployee = findEmployeeForName(employees, rowName);

      if (selectedEmployee !== "all") {
        if (!selectedEmployeeObj) return false;
        return matchedEmployee?.employeeId === selectedEmployee;
      }

      if (selectedCompany !== "all") {
        return matchedEmployee?.company === selectedCompany;
      }

      return true;
    },
    [employees, selectedDate, selectedEmployee, selectedEmployeeObj, selectedCompany],
  );

  const filteredSnapshots = useMemo(() => {
    return snapshotItems.filter((item) =>
      rowPasses(item.name, snapshotLocalDateKey(item.timestamp)),
    );
  }, [snapshotItems, rowPasses]);

  const handleExport = useCallback(() => {
    const header = ["S/N", "Employee Name", "Company", "Date", "Time"];
    const rows = filteredSnapshots.map((item, index) => {
      const emp = findEmployeeForName(employees, item.name);
      const captureDate = parseTimestamp(item.timestamp);
      return [
        String(index + 1),
        item.name,
        item.company ?? emp?.company ?? "—",
        formatDateDash(captureDate),
        formatTime12(captureDate),
      ];
    });
    downloadCsv(
      [header, ...rows],
      `live-captures-snapshot-${selectedDate || "all"}.csv`,
    );
  }, [employees, filteredSnapshots, selectedDate]);

  const itemCount = filteredSnapshots.length;
  const updatedLabel = lastUpdated
    ? `Updated ${lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: true })}`
    : "Updated —";

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <SectionShell
        title="Live Captures"
        icon={<Users className="h-5 w-5 text-primary" />}
        className="animate-fade-in-up"
        actions={
          <div className="flex w-full flex-wrap items-center gap-2 md:w-auto md:gap-3">
            {/* Yellow "new capture" indicator. Stays hidden by default; flashes
                ON for ~2 s each time a fresh row lands and is then cleared.
                Matches the sidebar Live Captures dot for consistency. */}
            {newCapturePulse ? (
              <span
                role="status"
                aria-live="polite"
                className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-1 text-[11px] font-semibold text-amber-700 ring-1 ring-amber-200"
                title="New capture just arrived"
              >
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
                </span>
                +{newCaptureCount} new
              </span>
            ) : null}
            <span className="text-xs font-medium text-slate-600">{updatedLabel}</span>
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="h-10 gap-1.5 px-4"
              onClick={() => void handleRefresh()}
              disabled={refreshing}
              title="Refresh live captures"
            >
              <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
              {refreshing ? "Refreshing…" : "Refresh"}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="h-10 gap-1.5 px-4"
              onClick={handleExport}
              disabled={itemCount === 0}
              title="Export filtered rows as CSV"
            >
              <Download className="h-4 w-4" />
              Export Report
            </Button>
          </div>
        }
      >
        <Card className="flex min-h-0 flex-1 flex-col">
          <CardContent className="flex min-h-0 flex-1 flex-col gap-3 pt-4">
            {/* Filter row */}
            <div className="flex flex-wrap items-center gap-3 border-b border-slate-200 pb-3">
              <Search className="h-5 w-5 text-primary" />

              <div className="flex items-center gap-2">
                <span className="whitespace-nowrap text-sm font-semibold text-sky-900">
                  Employees
                </span>
                <SearchableSelect
                  value={selectedEmployee}
                  onValueChange={setSelectedEmployee}
                  options={employeeFilterOptions}
                  clearValue="all"
                  placeholder="All Employees"
                  className="h-9 w-[140px] border-sky-200 focus-visible:ring-sky-300 sm:w-[150px] md:w-[160px]"
                />
              </div>

              <div className="flex items-center gap-2">
                <span className="whitespace-nowrap text-sm font-semibold text-[#393E2E]">
                  Companies
                </span>
                <SearchableSelect
                  value={selectedCompany}
                  onValueChange={setSelectedCompany}
                  options={companyFilterOptions}
                  clearValue="all"
                  placeholder="All Companies"
                  className="h-9 w-[125px] border-indigo-200 focus-visible:ring-indigo-300 sm:w-[135px] md:w-[145px]"
                />
              </div>

              <div className="flex items-center gap-2">
                <span className="whitespace-nowrap text-sm font-semibold text-emerald-900">
                  Date
                </span>
                <DatePicker
                  value={selectedDate}
                  onChange={setSelectedDate}
                  className="w-[280px]"
                />
              </div>

            </div>

            {error && (
              <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
                {error}
              </div>
            )}

            <div className="show-scrollbar min-h-0 flex-1 overflow-hidden">
              <SnapshotTable
                items={filteredSnapshots}
                employees={employees}
                cameraNamesById={cameraNamesById}
                cameraUsecaseById={cameraUsecaseById}
                loading={loading}
              />
            </div>
          </CardContent>
        </Card>
      </SectionShell>
    </div>
  );
}

function SnapshotTable({
  items,
  employees,
  cameraNamesById,
  cameraUsecaseById,
  loading,
}: {
  items: SnapshotLogItem[];
  employees: Employee[];
  cameraNamesById: Record<string, string>;
  cameraUsecaseById: Record<string, string>;
  loading: boolean;
}) {
  return (
    <Table className="min-w-[1010px] table-fixed">
      <TableHeader>
        <TableRow className="bg-slate-50/60 hover:bg-slate-50/80">
          <TableHead className="w-14 whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-slate-700 last:border-r-0">S/N</TableHead>
          <TableHead className="w-[260px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-sky-700 last:border-r-0">Employee Name</TableHead>
          <TableHead className="w-[180px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-indigo-700 last:border-r-0">Company</TableHead>
          <TableHead className="w-[120px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-sky-700 last:border-r-0">Image</TableHead>
          <TableHead className="w-[140px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-purple-700 last:border-r-0">Camera Name</TableHead>
          <TableHead className="w-[120px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-fuchsia-700 last:border-r-0">Usecase</TableHead>
          <TableHead className="w-[140px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-emerald-700 last:border-r-0">Date</TableHead>
          <TableHead className="w-[130px] whitespace-nowrap border-r border-slate-200 font-bold uppercase tracking-wide text-sky-700 last:border-r-0">Time</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.length === 0 ? (
          <TableRow>
            <TableCell colSpan={8} className="py-10 text-center text-muted-foreground">
              {loading ? "Loading snapshot…" : "No snapshot records match the current filters."}
            </TableCell>
          </TableRow>
        ) : (
          items.map((item, index) => {
            const emp = findEmployeeForName(employees, item.name);
            const company = item.company ?? emp?.company ?? "—";
            const captureDate = parseTimestamp(item.timestamp);
            return (
              <TableRow key={item.id} className="transition-colors hover:bg-slate-50/60">
                <TableCell className="border-r border-slate-200 py-2 align-middle text-slate-500 last:border-r-0">
                  {index + 1}
                </TableCell>
                <TableCell className="border-r border-slate-200 py-2 align-middle last:border-r-0">
                  <span className="font-medium text-foreground">{item.name}</span>
                </TableCell>
                <TableCell className="whitespace-nowrap border-r border-slate-200 py-2 align-middle font-medium text-indigo-700 last:border-r-0">
                  {company}
                </TableCell>
                <TableCell className="border-r border-slate-200 py-2 align-middle last:border-r-0">
                  <SnapshotThumb src={item.image_url} alt={item.name} />
                </TableCell>
                <TableCell className="whitespace-nowrap border-r border-slate-200 py-2 align-middle text-purple-700 last:border-r-0">
                  {item.camera_id ? (
                    (() => {
                      const friendlyName = cameraNamesById[item.camera_id];
                      const display = friendlyName ?? item.camera_id;
                      return (
                        <span
                          className="inline-flex items-center rounded-full bg-purple-50 px-2 py-0.5 text-xs font-medium"
                          title={`Camera id: ${item.camera_id}`}
                        >
                          {display.length > 22 ? `${display.slice(0, 20)}…` : display}
                        </span>
                      );
                    })()
                  ) : (
                    <span className="text-xs italic text-slate-400">API ingest</span>
                  )}
                </TableCell>
                <TableCell className="whitespace-nowrap border-r border-slate-200 py-2 align-middle last:border-r-0">
                  {(() => {
                    const usecase = item.camera_id ? cameraUsecaseById[item.camera_id] : undefined;
                    if (!usecase) return <span className="text-slate-400">—</span>;
                    const isEntry = usecase === "ENTRY";
                    return (
                      <span
                        className={
                          "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold " +
                          (isEntry ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700")
                        }
                      >
                        {isEntry ? "Person Entry" : "Person Exit"}
                      </span>
                    );
                  })()}
                </TableCell>
                <TableCell className="whitespace-nowrap border-r border-slate-200 py-2 align-middle font-medium text-emerald-700 last:border-r-0">
                  {formatDateDash(captureDate)}
                </TableCell>
                <TableCell className="whitespace-nowrap border-r border-slate-200 py-2 align-middle text-sky-700 last:border-r-0">
                  {formatTime12(captureDate)}
                </TableCell>
              </TableRow>
            );
          })
        )}
      </TableBody>
    </Table>
  );
}



