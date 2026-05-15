import { useEffect, useMemo, useState } from "react";
import { Loader2, Pencil, Trash2, UserPlus, X } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { cn } from "@/lib/utils";
import { formatDateDash, formatTime12, parseTimestamp } from "@/lib/dateFormat";
import { getEmployees, type Employee } from "@/api/dashboardApi";
import {
  useDeleteCapture,
  useDiscardCluster,
  usePromoteToExistingEmployee,
  useSetClusterLabel,
  useUnknownCluster,
} from "@/lib/hooks/useUnknowns";
import type { UnknownCapture, UnknownClusterStatus } from "@/lib/types/unknowns";
import { UnknownFaceImage } from "./UnknownFaceImage";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clusterId: number | null;
  onPromoteNew: (clusterId: number) => void;
};

const STATUS_BADGE: Record<UnknownClusterStatus, string> = {
  PENDING: "bg-amber-500/15 text-amber-600 border border-amber-500/30",
  PROMOTED: "bg-emerald-500/15 text-emerald-600 border border-emerald-500/30",
  IGNORED: "bg-slate-500/15 text-slate-600 border border-slate-500/30",
  MERGED: "bg-sky-500/15 text-sky-600 border border-sky-500/30",
};

export function ClusterDetailDialog({ open, onOpenChange, clusterId, onPromoteNew }: Props) {
  const detail = useUnknownCluster(open ? clusterId : null);
  const setLabel = useSetClusterLabel();
  const discardCluster = useDiscardCluster();
  const deleteCapture = useDeleteCapture();
  const promoteExisting = usePromoteToExistingEmployee();

  const employeesQuery = useQuery<Employee[]>({
    queryKey: ["employees"],
    queryFn: getEmployees,
    enabled: open,
    staleTime: 60_000,
  });

  const [labelInput, setLabelInput] = useState<string>("");
  const [editingLabel, setEditingLabel] = useState(false);
  const [existingEmployeeId, setExistingEmployeeId] = useState<string>("");

  // Reset local state when the dialog opens for a new cluster.
  useEffect(() => {
    if (!open) return;
    setLabelInput(detail.data?.label ?? "");
    setEditingLabel(false);
    setExistingEmployeeId("");
  }, [open, clusterId, detail.data?.label]);

  const cluster = detail.data ?? null;
  const isPending = cluster?.status === "PENDING";
  const capturesAll: UnknownCapture[] = cluster?.captures ?? [];
  const keepCount = capturesAll.filter((c) => c.status === "KEEP").length;
  const discardedCount = capturesAll.length - keepCount;

  const employeeOptions = useMemo(
    () =>
      (employeesQuery.data ?? [])
        .filter((e) => e.id !== cluster?.promoted_employee_id)
        .map((e) => ({
          value: e.id,
          label: `${e.name}${e.employeeId ? ` · ${e.employeeId}` : ""}`,
        })),
    [employeesQuery.data, cluster?.promoted_employee_id],
  );

  const firstSeen = parseTimestamp(cluster?.first_seen_at);
  const lastSeen = parseTimestamp(cluster?.last_seen_at);

  function handleSaveLabel() {
    if (!cluster) return;
    const next = labelInput.trim();
    setLabel.mutate(
      { clusterId: cluster.id, label: next || null },
      { onSuccess: () => setEditingLabel(false) },
    );
  }

  function handleDiscard() {
    if (!cluster) return;
    discardCluster.mutate(cluster.id, { onSuccess: () => onOpenChange(false) });
  }

  function handlePromoteExisting() {
    if (!cluster || !existingEmployeeId) return;
    promoteExisting.mutate(
      { clusterId: cluster.id, employeeId: existingEmployeeId },
      { onSuccess: () => onOpenChange(false) },
    );
  }

  function handlePromoteNew() {
    if (!cluster) return;
    // Close this dialog first so the promote-new dialog isn't stacked on top
    // of an open Radix overlay (a known footgun with stacked dialogs —
    // focus-trap + scroll-lock + pointer-events fight each other).
    onOpenChange(false);
    onPromoteNew(cluster.id);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] max-w-3xl overflow-hidden p-0 sm:max-w-3xl">
        <div className="flex h-full max-h-[92vh] flex-col">
          <DialogHeader className="border-b px-5 py-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <DialogTitle className="truncate text-lg">
                  {cluster?.label?.trim() || (cluster ? `Unknown #${cluster.id}` : "Cluster")}
                </DialogTitle>
                <DialogDescription className="text-xs">
                  {cluster ? (
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase",
                        STATUS_BADGE[cluster.status],
                      )}
                    >
                      {cluster.status.toLowerCase()}
                    </span>
                  ) : (
                    "Loading…"
                  )}
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>

          <div className="show-scrollbar flex-1 overflow-y-auto px-5 py-4">
            {detail.isLoading || !cluster ? (
              <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading cluster…
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-2 rounded-lg border bg-muted/30 p-3 text-xs sm:grid-cols-4">
                  <MetaBlock title="First seen" value={firstSeen ? `${formatDateDash(firstSeen)} ${formatTime12(firstSeen)}` : "—"} />
                  <MetaBlock title="Last seen" value={lastSeen ? `${formatDateDash(lastSeen)} ${formatTime12(lastSeen)}` : "—"} />
                  <MetaBlock title="Total faces" value={String(capturesAll.length)} />
                  <MetaBlock title="Kept · Discarded" value={`${keepCount} · ${discardedCount}`} />
                </div>

                {cluster.status === "PROMOTED" && cluster.promoted_employee_id && (
                  <div className="mt-3 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-700">
                    Added as employee <span className="font-semibold">{cluster.promoted_employee_id}</span>
                  </div>
                )}
                {cluster.status === "MERGED" && cluster.merged_into_cluster_id && (
                  <div className="mt-3 rounded-md border border-sky-500/30 bg-sky-500/10 px-3 py-2 text-xs text-sky-700">
                    Merged into cluster #{cluster.merged_into_cluster_id}
                  </div>
                )}

                <div className="mt-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-muted-foreground">Label</span>
                    <span className="text-[10px] text-muted-foreground/80">working name, does not promote</span>
                  </div>
                  {editingLabel && isPending ? (
                    <div className="flex items-center gap-2">
                      <Input
                        value={labelInput}
                        onChange={(e) => setLabelInput(e.target.value)}
                        placeholder="e.g. cafeteria visitor"
                        className="h-9"
                        autoFocus
                      />
                      <Button size="sm" onClick={handleSaveLabel} disabled={setLabel.isPending}>
                        {setLabel.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save"}
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setEditingLabel(false)}>
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <div className="flex-1 truncate text-sm">
                        {cluster.label?.trim() || <span className="text-muted-foreground italic">no label</span>}
                      </div>
                      {isPending && (
                        <Button size="sm" variant="outline" onClick={() => setEditingLabel(true)}>
                          <Pencil className="mr-1 h-3.5 w-3.5" />
                          Edit
                        </Button>
                      )}
                    </div>
                  )}
                </div>

                <div className="mt-5">
                  <div className="mb-2 text-xs font-medium text-muted-foreground">
                    Captures ({capturesAll.length})
                  </div>
                  {capturesAll.length === 0 ? (
                    <div className="rounded-md border border-dashed py-6 text-center text-xs text-muted-foreground">
                      No captures.
                    </div>
                  ) : (
                    <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6">
                      {capturesAll.map((cap) => (
                        <CaptureTile
                          key={cap.id}
                          capture={cap}
                          canDelete={isPending && cap.status === "KEEP"}
                          deleting={deleteCapture.isPending && deleteCapture.variables === cap.id}
                          onDelete={() => deleteCapture.mutate(cap.id)}
                        />
                      ))}
                    </div>
                  )}
                </div>

                {isPending && (
                  <div className="mt-5 rounded-lg border bg-muted/30 p-3">
                    <div className="mb-2 text-xs font-medium text-muted-foreground">
                      Add to existing employee
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="min-w-[220px] flex-1">
                        <SearchableSelect
                          value={existingEmployeeId}
                          options={employeeOptions}
                          onValueChange={setExistingEmployeeId}
                          placeholder={
                            employeesQuery.isLoading
                              ? "Loading employees…"
                              : "Search for an employee…"
                          }
                          disabled={employeesQuery.isLoading || promoteExisting.isPending}
                        />
                      </div>
                      <Button
                        size="sm"
                        onClick={handlePromoteExisting}
                        disabled={!existingEmployeeId || promoteExisting.isPending}
                      >
                        {promoteExisting.isPending && (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        )}
                        Add captures
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {isPending && (
            <DialogFooter className="flex-row items-center justify-between gap-2 border-t px-5 py-3 sm:justify-between">
              <Button
                variant="outline"
                onClick={handleDiscard}
                disabled={discardCluster.isPending}
              >
                {discardCluster.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                <Trash2 className="mr-2 h-4 w-4" />
                Discard
              </Button>
              <Button onClick={handlePromoteNew}>
                <UserPlus className="mr-2 h-4 w-4" />
                Add as new employee
              </Button>
            </DialogFooter>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function MetaBlock({ title, value }: { title: string; value: string }) {
  return (
    <div className="min-w-0">
      <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{title}</div>
      <div className="truncate text-xs font-medium">{value}</div>
    </div>
  );
}

function CaptureTile({
  capture,
  canDelete,
  deleting,
  onDelete,
}: {
  capture: UnknownCapture;
  canDelete: boolean;
  deleting: boolean;
  onDelete: () => void;
}) {
  const isDiscarded = capture.status === "DISCARDED";
  return (
    <div
      className={cn(
        "group relative aspect-square overflow-hidden rounded-md border bg-slate-900",
        isDiscarded && "opacity-50",
      )}
    >
      <UnknownFaceImage captureId={capture.id} />
      {isDiscarded && (
        <span className="absolute left-1 top-1 rounded bg-slate-700/80 px-1 py-0.5 text-[9px] font-semibold uppercase text-white">
          discarded
        </span>
      )}
      {canDelete && (
        <button
          type="button"
          onClick={onDelete}
          disabled={deleting}
          className="absolute right-1 top-1 rounded-full bg-red-600/90 p-1 text-white opacity-0 transition-opacity hover:bg-red-700 group-hover:opacity-100 disabled:opacity-100"
          title="Remove this capture"
        >
          {deleting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Trash2 className="h-3 w-3" />}
        </button>
      )}
    </div>
  );
}
