import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Info,
  Loader2,
  Pencil,
  RefreshCcw,
  Trash2,
  UserPlus,
  X,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { cn } from "@/lib/utils";
import { formatDateDash, formatTime12, parseTimestamp } from "@/lib/dateFormat";
import { getEmployees, type Employee } from "@/api/dashboardApi";
import { PromoteError } from "@/api/unknownsApi";
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
  onPromoteNew: (clusterId: number, selectedCaptureIds: number[]) => void;
};

const STATUS_BADGE: Record<UnknownClusterStatus, string> = {
  PENDING: "bg-amber-500/15 text-amber-600 border border-amber-500/30",
  PROMOTED: "bg-emerald-500/15 text-emerald-600 border border-emerald-500/30",
  IGNORED: "bg-slate-500/15 text-slate-600 border border-slate-500/30",
  MERGED: "bg-sky-500/15 text-sky-600 border border-sky-500/30",
};

// Spec: min 3, max 6 selected captures per training submission. Mirrors
// MAX_EMBEDDINGS_PER_EMPLOYEE on the backend.
const SELECT_MIN = 3;
const SELECT_MAX = 6;

// Quality thresholds for the "poor" badge on capture tiles. Backend
// still re-validates on submit; this is just a UX hint so the admin
// can deselect obvious bad shots before they bother training.
const QUALITY_DET_FLOOR = 0.65;
const QUALITY_SHARP_FLOOR = 30.0;

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
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [notice, setNotice] = useState<{ kind: "info" | "warn" | "error"; text: string } | null>(null);
  // Retrain-on-at-cap prompt: opens when backend returns 409 at_capacity
  // for an add attempt. Admin confirms and we re-submit with mode=replace.
  const [retrainPrompt, setRetrainPrompt] = useState<{
    employeeName: string;
    embeddingsCount: number;
    employeeId: string;
  } | null>(null);

  // Reset per-cluster state when the dialog opens for a different cluster.
  useEffect(() => {
    if (!open) return;
    setLabelInput(detail.data?.label ?? "");
    setEditingLabel(false);
    setExistingEmployeeId("");
    setSelectedIds(new Set());
    setNotice(null);
    setRetrainPrompt(null);
  }, [open, clusterId, detail.data?.label]);

  const cluster = detail.data ?? null;
  const isPending = cluster?.status === "PENDING";
  const capturesAll: UnknownCapture[] = cluster?.captures ?? [];
  const keepCaptures = useMemo(
    () => capturesAll.filter((c) => c.status === "KEEP"),
    [capturesAll],
  );
  const keepCount = keepCaptures.length;
  const discardedCount = capturesAll.length - keepCount;
  const selectedCount = selectedIds.size;

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

  const toggleSelected = (captureId: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(captureId)) {
        next.delete(captureId);
      } else {
        if (next.size >= SELECT_MAX) {
          setNotice({
            kind: "warn",
            text: `You can select at most ${SELECT_MAX} images. Deselect one first.`,
          });
          return prev;
        }
        next.add(captureId);
      }
      setNotice(null);
      return next;
    });
  };

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

  const ensureValidSelection = (): boolean => {
    if (selectedCount < SELECT_MIN) {
      setNotice({
        kind: "warn",
        text: `Please select at least ${SELECT_MIN} clear images.`,
      });
      return false;
    }
    return true;
  };

  function runPromoteExisting(employeeId: string, mode: "add" | "replace") {
    if (!cluster) return;
    const captureIds = Array.from(selectedIds);
    promoteExisting.mutate(
      {
        clusterId: cluster.id,
        employeeId,
        payload: { capture_ids: captureIds, mode },
      },
      {
        onSuccess: () => {
          setNotice({
            kind: "info",
            text:
              mode === "replace"
                ? "Retrained successfully. Old embeddings replaced with the new selection."
                : "Added to employee successfully.",
          });
          setTimeout(() => onOpenChange(false), 700);
        },
        onError: (err) => {
          if (err instanceof PromoteError && err.detail.code === "at_capacity") {
            const empName =
              (employeesQuery.data ?? []).find((e) => e.id === employeeId)?.name ?? employeeId;
            setRetrainPrompt({
              employeeName: empName,
              embeddingsCount: err.detail.embeddings_count ?? 0,
              employeeId,
            });
            return;
          }
          if (err instanceof PromoteError) {
            setNotice({ kind: "error", text: err.detail.message });
            return;
          }
          setNotice({
            kind: "error",
            text: err instanceof Error ? err.message : "Add to existing failed",
          });
        },
      },
    );
  }

  function handlePromoteExisting() {
    if (!cluster || !existingEmployeeId) return;
    if (!ensureValidSelection()) return;
    runPromoteExisting(existingEmployeeId, "add");
  }

  function handleRetrainConfirm() {
    if (!retrainPrompt) return;
    runPromoteExisting(retrainPrompt.employeeId, "replace");
    setRetrainPrompt(null);
  }

  function handlePromoteNew() {
    if (!cluster) return;
    if (!ensureValidSelection()) return;
    onOpenChange(false);
    onPromoteNew(cluster.id, Array.from(selectedIds));
  }

  // Convenience flag the layout uses in a few places.
  const selectionReady = selectedCount >= SELECT_MIN;
  const promoteBusy = promoteExisting.isPending;

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        {/* Widened to 4xl so the new two-column body (captures | actions)
            fits without cramping. p-0 + an inner flex column gives us a
            sticky header / sticky footer / scrolling middle. */}
        <DialogContent className="max-h-[92vh] max-w-4xl overflow-hidden p-0 sm:max-w-4xl">
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
              {detail.isLoading ? (
                <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading cluster…
                </div>
              ) : detail.error ? (
                // Real error surfaced instead of an infinite spinner.
                <div className="flex h-32 flex-col items-center justify-center gap-3 text-center text-sm">
                  <div className="flex items-center gap-2 text-rose-700">
                    <AlertTriangle className="h-4 w-4" />
                    Couldn&apos;t load this cluster.
                  </div>
                  <div
                    className="max-w-md truncate text-xs text-muted-foreground"
                    title={detail.error instanceof Error ? detail.error.message : String(detail.error)}
                  >
                    {detail.error instanceof Error ? detail.error.message : "Unknown error"}
                  </div>
                  <Button size="sm" variant="outline" onClick={() => detail.refetch()}>
                    <Loader2 className={cn("mr-2 h-3.5 w-3.5", detail.isFetching && "animate-spin")} />
                    Retry
                  </Button>
                </div>
              ) : !cluster ? (
                <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
                  No cluster data returned.
                </div>
              ) : (
                <>
                  {/* Top strip: meta + cluster-level label edit. Full
                      width above the two-column body so it doesn't
                      compete with the action panel for real estate. */}
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

                  <div className="mt-4 flex items-center gap-2">
                    <span className="text-xs font-medium text-muted-foreground">Label</span>
                    <span className="text-[10px] text-muted-foreground/80">working name, does not promote</span>
                  </div>
                  {editingLabel && isPending ? (
                    <div className="mt-1.5 flex items-center gap-2">
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
                    <div className="mt-1.5 flex items-center gap-2">
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

                  {notice ? (
                    <div
                      role="status"
                      aria-live="polite"
                      className={cn(
                        "mt-3 flex items-start gap-2 rounded-md border px-3 py-2 text-xs",
                        notice.kind === "error" && "border-rose-200 bg-rose-50 text-rose-700",
                        notice.kind === "warn" && "border-amber-200 bg-amber-50 text-amber-800",
                        notice.kind === "info" && "border-sky-200 bg-sky-50 text-sky-800",
                      )}
                    >
                      {notice.kind === "info" ? (
                        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                      ) : (
                        <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                      )}
                      <span>{notice.text}</span>
                    </div>
                  ) : null}

                  {/* ===== Two-column body: LEFT = captures + selection,
                      RIGHT = actions. Stacks to one column on small
                      screens so it still works on a phone. ===== */}
                  <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
                    {/* LEFT — captures + selection */}
                    <div className="space-y-3">
                      {isPending && keepCount > 0 ? (
                        <div className="flex items-center justify-between gap-3 rounded-lg border bg-slate-50 px-3 py-2 text-xs">
                          <div className="flex items-center gap-2">
                            <CheckCircle2
                              className={cn(
                                "h-4 w-4",
                                selectionReady ? "text-emerald-600" : "text-slate-400",
                              )}
                            />
                            <span className="font-medium text-slate-700">
                              Selected{" "}
                              <span className="tabular-nums">
                                {selectedCount} / {SELECT_MAX}
                              </span>
                            </span>
                            <span className="text-slate-500">· min {SELECT_MIN} to train</span>
                          </div>
                          {selectedCount > 0 ? (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 text-xs"
                              onClick={() => setSelectedIds(new Set())}
                            >
                              Clear
                            </Button>
                          ) : null}
                        </div>
                      ) : null}

                      <div>
                        <div className="mb-2 text-xs font-medium text-muted-foreground">
                          Captures ({capturesAll.length})
                        </div>
                        {capturesAll.length === 0 ? (
                          <div className="rounded-md border border-dashed py-6 text-center text-xs text-muted-foreground">
                            No captures.
                          </div>
                        ) : (
                          <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5">
                            {capturesAll.map((cap) => (
                              <CaptureTile
                                key={cap.id}
                                capture={cap}
                                canSelect={isPending && cap.status === "KEEP"}
                                selected={selectedIds.has(cap.id)}
                                onToggleSelect={() => toggleSelected(cap.id)}
                                canDelete={isPending && cap.status === "KEEP"}
                                deleting={deleteCapture.isPending && deleteCapture.variables === cap.id}
                                onDelete={() => deleteCapture.mutate(cap.id)}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* RIGHT — actions stack. Both promote paths live
                        here so admin sees them side-by-side and can
                        choose without scrolling around. */}
                    {isPending ? (
                      <div className="space-y-3 lg:sticky lg:top-0">
                        {/* Add to Existing Employee */}
                        <section className="rounded-lg border bg-white p-3 shadow-sm">
                          <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-700">
                            <UserPlus className="h-3.5 w-3.5 text-primary" />
                            Add to Existing Employee
                          </div>
                          <p className="mb-2 text-[11px] leading-snug text-muted-foreground">
                            Pick the employee these faces belong to. The {SELECT_MIN}–{SELECT_MAX} selected captures
                            will be trained as new face embeddings for them.
                          </p>
                          <SearchableSelect
                            value={existingEmployeeId}
                            options={employeeOptions}
                            onValueChange={setExistingEmployeeId}
                            placeholder={
                              employeesQuery.isLoading
                                ? "Loading employees…"
                                : "Search for an employee…"
                            }
                            disabled={employeesQuery.isLoading || promoteBusy}
                          />
                          <Button
                            size="sm"
                            onClick={handlePromoteExisting}
                            disabled={
                              !existingEmployeeId ||
                              promoteBusy ||
                              !selectionReady
                            }
                            className="mt-2 h-9 w-full gap-1.5 text-sm font-medium"
                          >
                            {promoteBusy ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <CheckCircle2 className="h-3.5 w-3.5" />
                            )}
                            Train selected ({selectedCount})
                          </Button>
                          {!selectionReady ? (
                            <p className="mt-1.5 text-[11px] text-amber-700">
                              Please select at least {SELECT_MIN} clear images.
                            </p>
                          ) : null}
                          <p className="mt-1.5 text-[11px] text-muted-foreground">
                            If the employee is already at the {SELECT_MAX}-embedding cap, you&apos;ll be
                            asked to confirm a Retrain that replaces the existing set.
                          </p>
                        </section>

                        {/* Add as New Employee */}
                        <section className="rounded-lg border bg-white p-3 shadow-sm">
                          <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-700">
                            <UserPlus className="h-3.5 w-3.5 text-primary" />
                            Add as New Employee
                          </div>
                          <p className="mb-2 text-[11px] leading-snug text-muted-foreground">
                            Create a brand-new employee and use the selected captures
                            as their training images. You&apos;ll fill in their details
                            on the next step.
                          </p>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={handlePromoteNew}
                            disabled={!selectionReady}
                            className="h-9 w-full gap-1.5 text-sm font-medium"
                          >
                            <UserPlus className="h-3.5 w-3.5" />
                            Add new employee ({selectedCount})
                          </Button>
                          {!selectionReady ? (
                            <p className="mt-1.5 text-[11px] text-amber-700">
                              Please select at least {SELECT_MIN} clear images.
                            </p>
                          ) : null}
                        </section>
                      </div>
                    ) : null}
                  </div>
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
                  Discard cluster
                </Button>
                <span className="text-[11px] text-muted-foreground">
                  Discard removes this cluster from the review queue without
                  promoting it.
                </span>
              </DialogFooter>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Retrain confirm — fires when promote-existing returns
          409 at_capacity. Replaces the employee's existing
          embeddings with the current selection. Atomic on backend. */}
      <AlertDialog
        open={retrainPrompt !== null}
        onOpenChange={(o) => {
          if (!o) setRetrainPrompt(null);
        }}
      >
        <AlertDialogContent>
          {retrainPrompt ? (
            <>
              <AlertDialogHeader>
                <AlertDialogTitle className="flex items-center gap-2">
                  <RefreshCcw className="h-5 w-5 text-rose-600" />
                  Retrain this employee?
                </AlertDialogTitle>
                <AlertDialogDescription asChild>
                  <div className="space-y-2 text-sm text-slate-600">
                    <p>
                      <span className="font-semibold text-slate-900">
                        {retrainPrompt.employeeName}
                      </span>{" "}
                      is already fully trained with{" "}
                      <span className="font-semibold tabular-nums text-slate-900">
                        {retrainPrompt.embeddingsCount}
                      </span>{" "}
                      face embeddings.
                    </p>
                    <p>
                      Retraining will <strong className="text-rose-600">remove</strong>{" "}
                      the old embeddings and replace them with the{" "}
                      <span className="font-semibold tabular-nums text-slate-900">
                        {selectedCount}
                      </span>{" "}
                      selected capture{selectedCount === 1 ? "" : "s"}. Continue?
                    </p>
                    <p className="text-xs text-slate-500">
                      Safe replace: if validation fails, the existing trained
                      set is preserved.
                    </p>
                  </div>
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel onClick={() => setRetrainPrompt(null)}>
                  Cancel
                </AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleRetrainConfirm}
                  className="bg-rose-600 text-white hover:bg-rose-700"
                >
                  Retrain
                </AlertDialogAction>
              </AlertDialogFooter>
            </>
          ) : null}
        </AlertDialogContent>
      </AlertDialog>
    </>
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
  canSelect,
  selected,
  onToggleSelect,
  canDelete,
  deleting,
  onDelete,
}: {
  capture: UnknownCapture;
  canSelect: boolean;
  selected: boolean;
  onToggleSelect: () => void;
  canDelete: boolean;
  deleting: boolean;
  onDelete: () => void;
}) {
  const isDiscarded = capture.status === "DISCARDED";
  const lowQuality =
    !isDiscarded &&
    (capture.det_score < QUALITY_DET_FLOOR ||
      capture.sharpness_score < QUALITY_SHARP_FLOOR);
  return (
    <div
      className={cn(
        "group relative aspect-square overflow-hidden rounded-md border bg-slate-900 transition-shadow",
        isDiscarded && "opacity-50",
        canSelect && "cursor-pointer hover:ring-2 hover:ring-primary/40",
        selected && "ring-2 ring-primary",
      )}
      onClick={canSelect ? onToggleSelect : undefined}
      role={canSelect ? "button" : undefined}
      aria-pressed={canSelect ? selected : undefined}
    >
      <UnknownFaceImage captureId={capture.id} />

      {canSelect && (
        <div
          className={cn(
            "absolute left-1 top-1 flex h-5 w-5 items-center justify-center rounded border bg-white/90 text-[10px] font-bold",
            selected
              ? "border-primary bg-primary text-white"
              : "border-slate-300 text-transparent",
          )}
        >
          ✓
        </div>
      )}

      {isDiscarded && (
        <span className="absolute left-1 top-1 rounded bg-slate-700/80 px-1 py-0.5 text-[9px] font-semibold uppercase text-white">
          discarded
        </span>
      )}

      {lowQuality && (
        <span
          className="absolute bottom-1 left-1 inline-flex items-center gap-0.5 rounded bg-amber-500/90 px-1 py-0.5 text-[9px] font-semibold uppercase text-white"
          title={`Low quality — det=${capture.det_score.toFixed(2)} sharp=${capture.sharpness_score.toFixed(0)}`}
        >
          <AlertTriangle className="h-2.5 w-2.5" />
          poor
        </span>
      )}

      {canDelete && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
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
