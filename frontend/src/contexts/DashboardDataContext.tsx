/**
 * Global dashboard data — fetched once (with polling), normalized once, shared
 * to every widget via context. Widgets derive their own view via builders from
 * `lib/dashboardData.ts`; they never refetch on their own.
 *
 * Fallback order:
 *   1. /api/attendance (live)
 *   2. /mock-api/dashboard.json (bundled mock, matches DashboardApiResponse)
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  getAttendanceLogs,
  type AttendanceSummaryItem,
} from "@/api/dashboardApi";
import {
  normalizeAttendance,
  type NormalizedAttendance,
} from "@/lib/dashboardData";
import { companyMatches, getCurrentCompany, getCurrentRole } from "@/lib/auth";

type DashboardDataContextValue = {
  attendance: NormalizedAttendance[];
  raw: AttendanceSummaryItem[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refresh: () => Promise<void>;
};

const DashboardDataContext = createContext<DashboardDataContextValue | null>(null);

const POLL_INTERVAL_MS = 30_000;
// Covers Presence Trend's 8-week weekly window (4 current + 4 previous)
// plus a buffer week, so the previous-period average is computed from
// real data instead of empty buckets.
const ATTENDANCE_LOOKBACK_DAYS = 63;

function formatYmd(d: Date): string {
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
}

async function fetchFromMock(): Promise<AttendanceSummaryItem[]> {
  // The bundled mock doesn't ship this shape directly — it has `presenceHistory`.
  // Shim it into an AttendanceSummaryItem-compatible stub so the UI still
  // renders something when the API is unreachable.
  try {
    const resp = await fetch("/mock-api/dashboard.json");
    if (!resp.ok) return [];
    const body = (await resp.json()) as {
      employees?: Array<{
        name: string;
        employeeId: string;
        company: string;
      }>;
      presenceHistory?: Array<{
        id: string;
        employeeName: string;
        employeeId: string;
        company?: string | null;
        entryTime: string;
        exitTime: string | null;
        totalHours: string;
        status: "Present" | "Late" | "Early Exit" | "Absent";
        date: string;
      }>;
    };
    const rows = body.presenceHistory ?? [];
    const companyByEmployeeId = new Map(
      (body.employees ?? []).map((employee) => [employee.employeeId, employee.company]),
    );
    return rows.map<AttendanceSummaryItem>((r) => ({
      id: `${r.employeeId}|${r.date}`,
      name: r.employeeName,
      company: r.company ?? companyByEmployeeId.get(r.employeeId) ?? null,
      date: r.date,
      entry_time: r.entryTime || null,
      exit_time: r.exitTime,
      late_entry_minutes: 0,
      late_entry_seconds: 0,
      early_exit_minutes: 0,
      early_exit_seconds: 0,
      status: r.status,
      total_hours: r.totalHours,
      entry_image_url: null,
      exit_image_url: null,
    }));
  } catch {
    return [];
  }
}

export function DashboardDataProvider({ children }: { children: ReactNode }) {
  const [raw, setRaw] = useState<AttendanceSummaryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const activeRef = useRef(true);

  const fetchOnce = useCallback(async () => {
    const today = new Date();
    const start = new Date(today);
    start.setDate(start.getDate() - (ATTENDANCE_LOOKBACK_DAYS - 1));
    try {
      const resp = await getAttendanceLogs({
        start: formatYmd(start),
        end: formatYmd(today),
      });
      if (!activeRef.current) return;
      setRaw(resp.items);
      setError(null);
      setLastUpdated(new Date());
      return;
    } catch (err) {
      if (!activeRef.current) return;
      // fall through to mock
      const mockRows = await fetchFromMock();
      if (!activeRef.current) return;
      if (mockRows.length > 0) {
        setRaw(mockRows);
        setError(null);
        setLastUpdated(new Date());
      } else {
        setError(err instanceof Error ? err.message : "Failed to load dashboard data");
      }
    }
  }, []);

  useEffect(() => {
    activeRef.current = true;
    setLoading(true);
    (async () => {
      await fetchOnce();
      if (activeRef.current) setLoading(false);
    })();
    const id = setInterval(fetchOnce, POLL_INTERVAL_MS);
    return () => {
      activeRef.current = false;
      clearInterval(id);
    };
  }, [fetchOnce]);

  // HR users only see attendance for their own company. Admin sees all.
  // Read once at provider mount — the provider only renders post-auth.
  const scopedCompany = useMemo<string | null>(() => {
    return getCurrentRole() === "hr" ? getCurrentCompany() : null;
  }, []);

  const scopedRaw = useMemo<AttendanceSummaryItem[]>(() => {
    if (!scopedCompany) return raw;
    return raw.filter((item) => companyMatches(item.company, scopedCompany));
  }, [raw, scopedCompany]);

  const attendance = useMemo(() => normalizeAttendance(scopedRaw), [scopedRaw]);

  const refresh = useCallback(async () => {
    await fetchOnce();
  }, [fetchOnce]);

  const value = useMemo<DashboardDataContextValue>(
    () => ({ attendance, raw: scopedRaw, loading, error, lastUpdated, refresh }),
    [attendance, scopedRaw, loading, error, lastUpdated, refresh],
  );

  return (
    <DashboardDataContext.Provider value={value}>{children}</DashboardDataContext.Provider>
  );
}

export function useDashboardData(): DashboardDataContextValue {
  const ctx = useContext(DashboardDataContext);
  if (!ctx) {
    throw new Error("useDashboardData must be used inside <DashboardDataProvider>");
  }
  return ctx;
}
