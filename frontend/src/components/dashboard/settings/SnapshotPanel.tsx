import { useCallback, useEffect, useRef, useState } from "react";
import { CheckCircle2, HardDrive, RefreshCw, Trash2 } from "lucide-react";

import {
  type SnapshotStats,
  getSnapshotStats,
  purgeSnapshotsBefore,
} from "@/api/dashboardApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

function formatBytes(bytes: number): string {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  let n = bytes;
  while (n >= 1024 && i < units.length - 1) {
    n /= 1024;
    i++;
  }
  return `${n.toFixed(n >= 100 || i === 0 ? 0 : n >= 10 ? 1 : 2)} ${units[i]}`;
}

function todayLocalIso(): string {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function defaultPurgeCutoff(): string {
  // Default to "30 days ago" so the most common use (free up old data, keep
  // last month) is one click away.
  const d = new Date();
  d.setDate(d.getDate() - 30);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export function SnapshotPanel() {
  const [stats, setStats] = useState<SnapshotStats | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [cutoff, setCutoff] = useState<string>(defaultPurgeCutoff());
  const [confirmOpen, setConfirmOpen] = useState<boolean>(false);
  const [purging, setPurging] = useState<boolean>(false);

  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const successTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const showSuccess = (message: string) => {
    setSuccessMessage(message);
    if (successTimerRef.current) clearTimeout(successTimerRef.current);
    successTimerRef.current = setTimeout(() => setSuccessMessage(null), 4000);
  };
  useEffect(
    () => () => {
      if (successTimerRef.current) clearTimeout(successTimerRef.current);
    },
    [],
  );

  const refresh = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      setStats(await getSnapshotStats());
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Failed to load snapshot stats");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handlePurge = async () => {
    setPurging(true);
    try {
      const result = await purgeSnapshotsBefore(cutoff);
      const totalCleared = Object.values(result.cleared).reduce((a, b) => a + b, 0);
      showSuccess(
        `Purged image data on ${totalCleared.toLocaleString()} row${
          totalCleared === 1 ? "" : "s"
        } older than ${result.before_date}.`,
      );
      setConfirmOpen(false);
      await refresh();
    } catch (e) {
      window.alert(e instanceof Error ? e.message : "Purge failed");
    } finally {
      setPurging(false);
    }
  };

  const today = todayLocalIso();

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      {successMessage ? (
        <div
          role="status"
          aria-live="polite"
          className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3.5 py-2.5 text-sm font-medium text-emerald-700"
        >
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{successMessage}</span>
        </div>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
          <HardDrive className="h-5 w-5 text-primary" />
          Snapshot Storage
        </h2>
        <Button
          variant="outline"
          size="sm"
          className="h-9 gap-1.5"
          onClick={() => void refresh()}
          disabled={loading}
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {loadError ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700">
          {loadError}
        </div>
      ) : null}

      {stats ? (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <StatCard label="Total rows" value={stats.totalRows.toLocaleString()} />
            <StatCard
              label="With image data"
              value={stats.totalRowsWithImage.toLocaleString()}
            />
            <StatCard label="Approx. size" value={formatBytes(stats.totalBytes)} />
            <StatCard
              label="Oldest image"
              value={
                stats.oldestImageTimestamp
                  ? new Date(stats.oldestImageTimestamp).toLocaleDateString()
                  : "—"
              }
            />
          </div>

          <div className="overflow-hidden rounded-xl border border-slate-200">
            <table className="w-full text-sm">
              <thead className="bg-slate-50/60 text-left text-xs font-semibold uppercase tracking-wide text-slate-700">
                <tr>
                  <th className="px-3 py-2">Table</th>
                  <th className="px-3 py-2 text-right">Rows</th>
                  <th className="px-3 py-2 text-right">With image</th>
                  <th className="px-3 py-2 text-right">Approx. size</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats.tables).map(([name, t]) => (
                  <tr key={name} className="border-t border-slate-200">
                    <td className="px-3 py-2 font-mono text-xs text-slate-700">{name}</td>
                    <td className="px-3 py-2 text-right">{t.rows.toLocaleString()}</td>
                    <td className="px-3 py-2 text-right">
                      {t.rowsWithImage.toLocaleString()}
                    </td>
                    <td className="px-3 py-2 text-right">{formatBytes(t.approxBytes)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : loading ? (
        <div className="py-8 text-center text-sm text-muted-foreground">Loading…</div>
      ) : null}

      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
        <h3 className="text-sm font-semibold text-amber-900">Manual purge</h3>
        <p className="mt-1 text-xs text-amber-800">
          Clears the base64 <code>image_data</code> on every snapshot/attendance row older
          than the cutoff. Rows themselves stay (so attendance counts are unaffected); only
          their thumbnails go. The nightly auto-prune already preserves entry/exit images
          for older days — this manual purge does not, so use it when you really need to
          free space.
        </p>
        <div className="mt-3 flex flex-wrap items-end gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs font-semibold uppercase tracking-wide text-amber-900">
              Purge images older than
            </Label>
            <Input
              type="date"
              value={cutoff}
              max={today}
              onChange={(e) => setCutoff(e.target.value)}
              className="h-9 w-48 border-amber-300 bg-white"
            />
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-9 gap-1.5 border-rose-300 text-rose-700 hover:bg-rose-50 hover:text-rose-800"
            onClick={() => setConfirmOpen(true)}
            disabled={!cutoff || purging}
          >
            <Trash2 className="h-3.5 w-3.5" />
            Purge images
          </Button>
        </div>
      </div>

      <AlertDialog
        open={confirmOpen}
        onOpenChange={(open) => {
          if (!open && !purging) setConfirmOpen(false);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Purge snapshot images?</AlertDialogTitle>
            <AlertDialogDescription>
              This permanently clears the image data on every capture row older than{" "}
              <span className="font-semibold">{cutoff}</span>. Attendance rows themselves
              are kept; only the JPEG/base64 payload is dropped. This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={purging}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handlePurge}
              disabled={purging}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {purging ? "Purging…" : "Purge"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-3.5 py-2.5">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-lg font-bold text-slate-900">{value}</div>
    </div>
  );
}
