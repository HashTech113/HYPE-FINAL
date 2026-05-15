import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  ATTENDANCE_CORRECTION_EVENT,
  getAttendanceLogs,
  type AttendanceSummaryItem,
} from "@/api/dashboardApi";

// Polling cadence shared by /reports and /presence. Tuned to match what
// those pages used independently before this context existed, but now
// runs as a single timer regardless of which tab is mounted.
const POLL_INTERVAL_MS = 5_000;

type AttendanceSummariesContextValue = {
  items: AttendanceSummaryItem[];
  loading: boolean;
  error: string | null;
  /** Force-refetch immediately. Returns the resolved items. */
  reload: () => Promise<AttendanceSummaryItem[] | null>;
};

const AttendanceSummariesContext =
  createContext<AttendanceSummariesContextValue | null>(null);

/**
 * Holds the result of ``GET /api/attendance`` in shared state so the
 * Reports and Attendance History pages don't each refetch (a ~10–100 MB
 * payload on a real dataset) every time the operator switches tabs.
 *
 * Before this provider existed, every mount of either page kicked off
 * its own fetch + its own 5-second poll. Switching tabs four times in
 * ten seconds therefore meant four cold fetches and four interleaved
 * polls. With the provider, the fetch happens once, polls run on a
 * single shared timer, and tab switches read from cached state — first
 * paint is instant after the initial load.
 *
 * The provider also rebroadcasts the existing ``ATTENDANCE_CORRECTION_EVENT``
 * so HR edits in Settings still flush the cache without a poll lag.
 */
export function AttendanceSummariesProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [items, setItems] = useState<AttendanceSummaryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // ``activeRef`` guards against a stale fetch resolving after the
  // provider unmounts (only happens on logout).
  const activeRef = useRef(true);
  // Tracks whether a fetch is in flight so the polling timer doesn't
  // pile concurrent /api/attendance requests on a slow connection.
  const inFlightRef = useRef(false);

  const fetchOnce = useCallback(async (): Promise<
    AttendanceSummaryItem[] | null
  > => {
    if (inFlightRef.current) return null;
    inFlightRef.current = true;
    try {
      const data = await getAttendanceLogs();
      if (!activeRef.current) return null;
      setItems(data.items);
      setError(null);
      return data.items;
    } catch (err) {
      if (!activeRef.current) return null;
      const message =
        err instanceof Error ? err.message : "Failed to load attendance data";
      setError(message);
      // Keep the previous ``items`` on screen — a transient backend hiccup
      // shouldn't blank the table.
      return null;
    } finally {
      inFlightRef.current = false;
      if (activeRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    activeRef.current = true;
    void fetchOnce();
    const id = window.setInterval(() => {
      void fetchOnce();
    }, POLL_INTERVAL_MS);
    const onCorrection = () => {
      void fetchOnce();
    };
    window.addEventListener(ATTENDANCE_CORRECTION_EVENT, onCorrection);
    return () => {
      activeRef.current = false;
      window.clearInterval(id);
      window.removeEventListener(ATTENDANCE_CORRECTION_EVENT, onCorrection);
    };
  }, [fetchOnce]);

  return (
    <AttendanceSummariesContext.Provider
      value={{ items, loading, error, reload: fetchOnce }}
    >
      {children}
    </AttendanceSummariesContext.Provider>
  );
}

export function useAttendanceSummaries(): AttendanceSummariesContextValue {
  const ctx = useContext(AttendanceSummariesContext);
  if (ctx === null) {
    throw new Error(
      "useAttendanceSummaries must be used within an AttendanceSummariesProvider",
    );
  }
  return ctx;
}
