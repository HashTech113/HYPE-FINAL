import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  createEmployeeRemote,
  deleteEmployeeRemote,
  getEmployees,
  updateEmployeeRemote,
  type Employee,
} from "@/api/dashboardApi";
import { companyMatches, getCurrentCompany, getCurrentRole } from "@/lib/auth";

// v2 is the active cache key. v1 is kept as a *fallback* (not deleted at
// module load) so an API outage doesn't simultaneously evict the
// working copy — we only prune legacy keys AFTER the new key has been
// successfully populated from a fresh API response. Bumped from v1 in
// 2026-05 after a transient API stall left some clients holding stale
// company assignments.
const STORAGE_KEY = "attendance-dashboard:employees:v2";
const LEGACY_STORAGE_KEYS = ["attendance-dashboard:employees:v1"] as const;

function pruneLegacyKeys(): void {
  if (typeof window === "undefined") return;
  try {
    for (const k of LEGACY_STORAGE_KEYS) window.localStorage.removeItem(k);
  } catch {
    // ignore quota / private-mode errors
  }
}

function readCacheFallback(): Employee[] | null {
  if (typeof window === "undefined") return null;
  // Try v2 (current) first, then walk legacy keys in order. Any source
  // that parses cleanly wins; the rest are ignored.
  for (const key of [STORAGE_KEY, ...LEGACY_STORAGE_KEYS]) {
    try {
      const raw = window.localStorage.getItem(key);
      if (!raw) continue;
      const parsed = JSON.parse(raw) as Employee[];
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    } catch {
      // ignore — try the next key
    }
  }
  return null;
}

const COMPANY_ALIAS_MAP: Record<string, string> = {
  "branch a": "WAWU",
  "branch b": "WAWU",
  "branch c": "WAWU",
};

function normalizeCompany(value: string): string {
  const cleaned = (value || "").trim();
  if (!cleaned) return cleaned;
  return COMPANY_ALIAS_MAP[cleaned.toLowerCase()] ?? cleaned;
}

function normalizeEmployees(list: Employee[]): Employee[] {
  return list.map((employee) => ({
    ...employee,
    company: normalizeCompany(employee.company),
  }));
}

type EmployeesContextValue = {
  employees: Employee[];
  loading: boolean;
  /** Non-null when the most recent load attempt failed. UI uses this to
   * render an actionable error banner so a backend outage isn't shown
   * as "no employees". */
  error: string | null;
  /** True when ``employees`` is being served from localStorage because
   * the API call failed — i.e. the data is potentially stale. */
  isStale: boolean;
  /** Re-run the API fetch. Used by the error banner's Retry button so
   * the operator doesn't have to reload the whole page. */
  reload: () => void;
  /** Company the current user is scoped to, or null for admins (full access). */
  scopedCompany: string | null;
  /** Async; resolves with the saved record from the server (or rejects on
   * API failure). The optimistic UI update happens immediately; the
   * resolved value is the canonical post-save state and is also written
   * into local state, so callers don't need to do their own refetch. */
  updateEmployee: (id: string, patch: Partial<Employee>) => Promise<Employee>;
  addEmployee: (employee: Employee) => Promise<Employee>;
  deleteEmployee: (id: string) => Promise<void>;
  resetToDefaults: () => Promise<void>;
};

const EmployeesContext = createContext<EmployeesContextValue | null>(null);

function writeToStorage(employees: Employee[]) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(employees));
  } catch {
    // ignore quota errors — context state still works in-memory
  }
}

export function EmployeesProvider({ children }: { children: ReactNode }) {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isStale, setIsStale] = useState(false);
  // Bumping this re-runs the load effect — used by reload() below.
  const [reloadTick, setReloadTick] = useState(0);

  const reload = useCallback(() => {
    setReloadTick((t) => t + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getEmployees()
      .then((list) => {
        if (cancelled) return;
        const normalized = normalizeEmployees(list);
        setEmployees(normalized);
        setIsStale(false);
        setError(null);
        writeToStorage(normalized);
        // Only NOW is it safe to drop the legacy key — the new one is
        // populated, so if the API breaks later we still fall back to
        // STORAGE_KEY (v2) instead of getting stranded with nothing.
        pruneLegacyKeys();
      })
      .catch((err) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Failed to load employees";
        console.error("Failed to load employees", err);
        const fallback = readCacheFallback();
        if (fallback) {
          const normalized = normalizeEmployees(fallback);
          setEmployees(normalized);
          setIsStale(true);
          setError(
            `Couldn't reach the server (${message}). Showing the last cached roster — values may be out of date.`,
          );
        } else {
          // No fallback available — surface a clear, actionable error
          // instead of silently showing an empty list.
          setEmployees([]);
          setIsStale(false);
          setError(
            `Couldn't reach the server (${message}). Make sure the backend (uvicorn) is running, then click Retry.`,
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reloadTick]);

  const updateEmployee = useCallback(async (id: string, patch: Partial<Employee>): Promise<Employee> => {
    // Optimistic UI update; rollback on failure. Returning a promise so
    // callers (the edit dialog) can await the canonical server response
    // before closing — that way a silent backend failure surfaces as a
    // visible error instead of looking like a successful save.
    let rollback: Employee[] | null = null;
    setEmployees((prev) => {
      rollback = prev;
      const next = prev.map((e) => (e.id === id ? { ...e, ...patch } : e));
      writeToStorage(next);
      return next;
    });
    try {
      const saved = await updateEmployeeRemote(id, patch);
      setEmployees((prev) => {
        // Replace local row with the canonical server record. Spreading
        // ``saved`` last guarantees salaryPackage / company / etc. always
        // reflect what's actually in PostgreSQL, not the in-flight patch.
        const next = prev.map((e) => (e.id === id ? { ...e, ...saved } : e));
        writeToStorage(next);
        return next;
      });
      return saved;
    } catch (error) {
      console.error("updateEmployee failed, rolling back", error);
      if (rollback) {
        setEmployees(rollback);
        writeToStorage(rollback);
      }
      throw error;
    }
  }, []);

  const addEmployee = useCallback(async (employee: Employee): Promise<Employee> => {
    let rollback: Employee[] | null = null;
    setEmployees((prev) => {
      rollback = prev;
      const next = [...prev, employee];
      writeToStorage(next);
      return next;
    });
    try {
      const saved = await createEmployeeRemote(employee);
      setEmployees((prev) => {
        // Backend may have assigned a new id — reconcile.
        const next = prev.map((e) => (e.id === employee.id ? saved : e));
        writeToStorage(next);
        return next;
      });
      return saved;
    } catch (error) {
      console.error("addEmployee failed, rolling back", error);
      if (rollback) {
        setEmployees(rollback);
        writeToStorage(rollback);
      }
      throw error;
    }
  }, []);

  const deleteEmployee = useCallback(async (id: string): Promise<void> => {
    let rollback: Employee[] | null = null;
    setEmployees((prev) => {
      rollback = prev;
      const next = prev.filter((e) => e.id !== id);
      writeToStorage(next);
      return next;
    });
    try {
      await deleteEmployeeRemote(id);
    } catch (error) {
      console.error("deleteEmployee failed, rolling back", error);
      if (rollback) {
        setEmployees(rollback);
        writeToStorage(rollback);
      }
      throw error;
    }
  }, []);

  const resetToDefaults = useCallback(async () => {
    const list = normalizeEmployees(await getEmployees());
    setEmployees(list);
    writeToStorage(list);
  }, []);

  // HR users only see their own company's employees. Admins see everyone.
  // Read once at provider mount — the provider lifecycle is tied to the
  // dashboard, which itself only mounts after authentication.
  const scopedCompany = useMemo<string | null>(() => {
    return getCurrentRole() === "hr" ? getCurrentCompany() : null;
  }, []);

  const visibleEmployees = useMemo<Employee[]>(() => {
    if (!scopedCompany) return employees;
    return employees.filter((employee) => companyMatches(employee.company, scopedCompany));
  }, [employees, scopedCompany]);

  const value = useMemo(
    () => ({
      employees: visibleEmployees,
      loading,
      error,
      isStale,
      reload,
      scopedCompany,
      updateEmployee,
      addEmployee,
      deleteEmployee,
      resetToDefaults,
    }),
    [visibleEmployees, loading, error, isStale, reload, scopedCompany, updateEmployee, addEmployee, deleteEmployee, resetToDefaults]
  );

  return <EmployeesContext.Provider value={value}>{children}</EmployeesContext.Provider>;
}

export function useEmployees(): EmployeesContextValue {
  const context = useContext(EmployeesContext);
  if (!context) {
    throw new Error("useEmployees must be used within an EmployeesProvider");
  }
  return context;
}
