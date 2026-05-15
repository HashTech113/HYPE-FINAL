import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  CheckCircle2,
  Cpu,
  ImagePlus,
  Layers,
  ScanFace,
  ScanLine,
  Sparkles,
  Trash2,
} from "lucide-react";

import {
  type Employee,
  type FaceImage,
  addFaceImage,
  captureFaceFromCamera,
  deleteFaceImage,
  enrollFaceImages,
  getFaceImages,
  getRecognitionWorkersHealth,
  type RecognitionWorkersHealthResponse,
} from "@/api/dashboardApi";
import { useEmployees } from "@/contexts/EmployeesContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SearchableSelect } from "@/components/ui/searchable-select";
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
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

// Image-count rules per the face-training spec: at least 3 distinct angles
// for usable embedding diversity, capped at 5 so a single employee's
// reference set doesn't bloat the cache or slow recognition.
const MIN_IMAGES_FOR_TRAINING = 3;
const MAX_IMAGES_PER_EMPLOYEE = 6;

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const value = typeof reader.result === "string" ? reader.result : "";
      if (!value) {
        reject(new Error("Could not read file"));
        return;
      }
      resolve(value);
    };
    reader.onerror = () => reject(new Error("Failed to read the selected image"));
    reader.readAsDataURL(file);
  });
}

// Animation phases for the training overlay. Each one renders a different
// icon + status line, and `phaseOrder` is used to compute the progress bar.
type TrainingPhase = "scanning" | "detecting" | "embedding" | "training";
const PHASE_ORDER: TrainingPhase[] = ["scanning", "detecting", "embedding", "training"];
const PHASE_COPY: Record<TrainingPhase, { title: string; subtitle: string; Icon: typeof ScanLine }> = {
  scanning: {
    title: "Scanning uploaded images",
    subtitle: "Reading pixel data from each reference photo…",
    Icon: ScanLine,
  },
  detecting: {
    title: "Detecting faces",
    subtitle: "Locating bounding boxes and landmarks across angles…",
    Icon: ScanFace,
  },
  embedding: {
    title: "Generating embeddings",
    subtitle: "Computing a 512-dimensional vector per face crop…",
    Icon: Sparkles,
  },
  training: {
    title: "Storing training set",
    subtitle: "Saving embeddings into the recognition index…",
    Icon: Cpu,
  },
};

type TrainingResult = {
  accepted: number;
  rejected: number;
  employeeName: string;
  employeeImage?: string;
  imageThumbnails: string[];
};

export function FaceTrainingPanel() {
  const { employees } = useEmployees();
  const [selectedId, setSelectedId] = useState<string>("");
  const [label, setLabel] = useState<string>("");
  const [images, setImages] = useState<FaceImage[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<FaceImage | null>(null);
  const [deletingBusy, setDeletingBusy] = useState<boolean>(false);
  const [trainingPhase, setTrainingPhase] = useState<TrainingPhase | null>(null);
  const [trainingResult, setTrainingResult] = useState<TrainingResult | null>(null);
  const [capturingBusy, setCapturingBusy] = useState<boolean>(false);
  const [workerStatus, setWorkerStatus] = useState<RecognitionWorkersHealthResponse | null>(null);
  const [workerError, setWorkerError] = useState<string | null>(null);
  const [selectedCameraId, setSelectedCameraId] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const successTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const showSuccess = (message: string) => {
    setSuccessMessage(message);
    if (successTimerRef.current) clearTimeout(successTimerRef.current);
    successTimerRef.current = setTimeout(() => setSuccessMessage(null), 3000);
  };
  useEffect(
    () => () => {
      if (successTimerRef.current) clearTimeout(successTimerRef.current);
    },
    [],
  );

  // "Akash - Hype Technologies" — combined employee + company in a single
  // searchable label so the operator can find a face by either side of the
  // identifier. Employee-id is kept out of the visible label per the spec
  // (still searchable via the SearchableSelect query, but not displayed).
  const employeeOptions = useMemo(
    () =>
      employees
        .map((e: Employee) => ({
          value: e.id,
          label: e.company ? `${e.name} - ${e.company}` : e.name,
        }))
        .sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: "base" })),
    [employees],
  );

  const selectedEmployee = useMemo(
    () => employees.find((e) => e.id === selectedId) ?? null,
    [employees, selectedId],
  );
  const cameraOptions = useMemo(
    () =>
      (workerStatus?.workers ?? [])
        .filter((w) => w.running)
        .map((w) => ({
          value: w.cameraId,
          label: `${w.name}${w.connected ? "" : " (disconnected)"}`,
        }))
        .sort((a, b) => a.label.localeCompare(b.label, undefined, { sensitivity: "base" })),
    [workerStatus],
  );

  const loadImages = useCallback(async (employeeId: string) => {
    setLoading(true);
    setLoadError(null);
    try {
      const list = await getFaceImages(employeeId);
      setImages(list);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Failed to load face images");
      setImages([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadWorkerStatus = useCallback(async () => {
    try {
      const status = await getRecognitionWorkersHealth();
      setWorkerStatus(status);
      setWorkerError(null);
    } catch (error) {
      setWorkerError(error instanceof Error ? error.message : "Failed to load camera worker status");
      setWorkerStatus(null);
    }
  }, []);

  useEffect(() => {
    if (selectedId) {
      void loadImages(selectedId);
    } else {
      setImages([]);
    }
  }, [selectedId, loadImages]);

  useEffect(() => {
    void loadWorkerStatus();
    const handle = window.setInterval(() => {
      void loadWorkerStatus();
    }, 10_000);
    return () => window.clearInterval(handle);
  }, [loadWorkerStatus]);

  useEffect(() => {
    if (!cameraOptions.some((opt) => opt.value === selectedCameraId)) {
      setSelectedCameraId(cameraOptions[0]?.value ?? "");
    }
  }, [cameraOptions, selectedCameraId]);

  const remainingSlots = Math.max(0, MAX_IMAGES_PER_EMPLOYEE - images.length);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    if (!selectedId) {
      window.alert("Pick an employee first.");
      return;
    }
    // Enforce the 5-image cap at upload time — the backend would also
    // reject extras, but failing loudly in the UI is friendlier than
    // having the upload succeed and the cap silently truncate.
    if (remainingSlots === 0) {
      window.alert(
        `Maximum ${MAX_IMAGES_PER_EMPLOYEE} images per employee. Delete an existing one before adding more.`,
      );
      return;
    }
    const accepted = Array.from(files).slice(0, remainingSlots);
    if (accepted.length < files.length) {
      window.alert(
        `Only the first ${accepted.length} image(s) will be uploaded — ${MAX_IMAGES_PER_EMPLOYEE}-image cap.`,
      );
    }
    setUploading(true);
    let added = 0;
    let failed = 0;
    try {
      for (const file of accepted) {
        if (!file.type.startsWith("image/")) {
          failed += 1;
          continue;
        }
        try {
          const dataUrl = await readFileAsDataUrl(file);
          const created = await addFaceImage(selectedId, dataUrl, label.trim());
          setImages((prev) => [created, ...prev]);
          added += 1;
        } catch (error) {
          failed += 1;
          console.error("face image upload failed", error);
        }
      }
      if (added > 0) {
        showSuccess(
          `Uploaded ${added} image${added === 1 ? "" : "s"}` +
            (failed > 0 ? ` (${failed} failed)` : ""),
        );
      } else if (failed > 0) {
        window.alert(`All ${failed} upload(s) failed.`);
      }
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleting) return;
    setDeletingBusy(true);
    try {
      await deleteFaceImage(deleting.id);
      const removed = deleting;
      setImages((prev) => prev.filter((img) => img.id !== removed.id));
      showSuccess("Image deleted.");
      setDeleting(null);
    } catch (error) {
      window.alert(error instanceof Error ? error.message : "Delete failed");
    } finally {
      setDeletingBusy(false);
    }
  };

  // Drives the visual training animation. Each phase is held for a minimum
  // duration so the operator can read what's happening even if the backend
  // resolves quickly. The real API call runs in parallel.
  const runTrainingAnimation = async (apiCall: Promise<unknown>) => {
    const PHASE_MS = 850;
    let phaseIndex = 0;
    setTrainingPhase(PHASE_ORDER[0]);
    const interval = window.setInterval(() => {
      phaseIndex = Math.min(phaseIndex + 1, PHASE_ORDER.length - 1);
      setTrainingPhase(PHASE_ORDER[phaseIndex]);
    }, PHASE_MS);
    try {
      // Wait for both: the real API call, AND a minimum total duration so
      // the animation has time to cycle through every phase.
      const minDuration = new Promise((r) =>
        setTimeout(r, PHASE_MS * PHASE_ORDER.length),
      );
      await Promise.all([apiCall, minDuration]);
    } finally {
      window.clearInterval(interval);
    }
  };

  const handleTrain = async () => {
    if (!selectedId) return;
    if (images.length < MIN_IMAGES_FOR_TRAINING) {
      window.alert(
        `Upload at least ${MIN_IMAGES_FOR_TRAINING} images (front / left / right) before training.`,
      );
      return;
    }
    const employeeName = selectedEmployee?.name ?? "Employee";
    const employeeImage = selectedEmployee?.imageUrl;
    const beforeThumbs = images.slice(0, 6).map((i) => i.imageUrl);
    try {
      let summary: Awaited<ReturnType<typeof enrollFaceImages>> | null = null;
      const apiPromise = enrollFaceImages(selectedId).then((res) => {
        summary = res;
        return res;
      });
      await runTrainingAnimation(apiPromise);
      if (summary) {
        setImages(summary.items);
        setTrainingResult({
          accepted: summary.accepted,
          rejected: summary.rejected,
          employeeName,
          employeeImage,
          imageThumbnails: beforeThumbs,
        });
      }
    } catch (error) {
      window.alert(error instanceof Error ? error.message : "Training failed");
    } finally {
      setTrainingPhase(null);
    }
  };

  const handleCaptureFromCamera = async () => {
    if (!selectedId || !selectedCameraId) return;
    setCapturingBusy(true);
    try {
      const created = await captureFaceFromCamera(selectedId, {
        cameraId: selectedCameraId,
        label: label.trim(),
      });
      setImages((prev) => [created, ...prev]);
      showSuccess("Captured from live camera and enrolled.");
    } catch (error) {
      window.alert(error instanceof Error ? error.message : "Camera capture failed");
    } finally {
      setCapturingBusy(false);
    }
  };

  const trainDisabled =
    !selectedId || trainingPhase !== null || images.length < MIN_IMAGES_FOR_TRAINING;

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

      <div className="grid grid-cols-1 gap-3 md:grid-cols-[2fr_1fr_auto]">
        <div className="space-y-1.5">
          <Label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Employee — Company
          </Label>
          <SearchableSelect
            value={selectedId}
            options={employeeOptions}
            onValueChange={setSelectedId}
            placeholder="Search by name or company…"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Angle label (optional)
          </Label>
          <Input
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="front / left / right"
            maxLength={64}
            disabled={!selectedId}
          />
        </div>
        <div className="flex items-end">
          <Button
            type="button"
            disabled={!selectedId || uploading || remainingSlots === 0}
            onClick={() => fileInputRef.current?.click()}
            className="h-10 gap-1.5"
          >
            <ImagePlus className="h-4 w-4" />
            {uploading
              ? "Uploading…"
              : remainingSlots === 0
                ? "Max reached"
                : `Upload images (${remainingSlots} left)`}
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            onChange={(e) => void handleFiles(e.target.files)}
          />
        </div>
      </div>

      {loadError ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700">
          {loadError}
        </div>
      ) : null}

      {/* Two-column body: training images / animation on the left, status
          + recommendations + Train CTA on the right. Right sidebar is
          ``self-start`` so cards hug their content rather than stretching
          to fill the row, freeing vertical space below. Stacks to one
          column on narrow viewports. */}
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        {/* LEFT — image grid OR training panel OR success panel. The
            container is ``overflow-hidden`` (not auto) because the grid
            uses fractional rows: with max 6 images in a 3×2 layout, the
            two rows share the available height equally and the tiles
            scale down to fit instead of pushing scroll. */}
        <div className="flex min-h-0 flex-col overflow-hidden rounded-xl border border-slate-200 bg-slate-50/40 p-3">
          {trainingPhase !== null ? (
            <div className="flex min-h-0 flex-1">
              <TrainingInlinePanel
                phase={trainingPhase}
                employeeName={selectedEmployee?.name ?? ""}
                imageThumbnails={images.slice(0, 6).map((i) => i.imageUrl)}
              />
            </div>
          ) : trainingResult !== null ? (
            <div className="flex min-h-0 flex-1">
              <TrainingSuccessInlinePanel
                result={trainingResult}
                onDismiss={() => setTrainingResult(null)}
              />
            </div>
          ) : loading ? (
            <div className="flex flex-1 items-center justify-center py-8 text-center text-sm text-muted-foreground">
              Loading…
            </div>
          ) : images.length === 0 && selectedId ? (
            <div className="flex flex-1 items-center justify-center py-8 text-center text-sm text-muted-foreground">
              No face images yet. Upload one or more to build a reference set.
            </div>
          ) : !selectedId ? (
            <div className="flex flex-1 items-center justify-center py-8 text-center text-sm text-muted-foreground">
              Pick an employee above to view or add their face training images.
            </div>
          ) : (
            <div className="grid h-full min-h-0 grid-cols-3 grid-rows-2 gap-3">
              {images.map((img) => (
                <div
                  key={img.id}
                  className="group relative flex min-h-0 flex-col overflow-hidden rounded-xl border border-slate-200 bg-white"
                >
                  {/* The image area fills whatever vertical space the
                      grid row gives it (``flex-1`` + ``min-h-0``), so 6
                      images at 3×2 always fit inside the section
                      without scrolling. ``object-contain`` shows the
                      whole face uncropped (any aspect-ratio mismatch
                      becomes background-coloured letterboxing). */}
                  <div className="relative min-h-0 flex-1 bg-slate-100">
                    <img
                      src={img.imageUrl}
                      alt={img.label || "Face training image"}
                      className="absolute inset-0 h-full w-full object-contain"
                      loading="lazy"
                    />
                  </div>
                  <div className="flex shrink-0 items-center justify-between gap-2 px-2.5 py-1.5 text-xs">
                    <div className="min-w-0">
                      <div className="truncate font-medium text-slate-700">
                        {img.label || "(no label)"}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 text-destructive hover:bg-rose-50 hover:text-destructive"
                      onClick={() => setDeleting(img)}
                      title="Delete image"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* RIGHT — status / recommendations at the top, Train CTA pinned
            to the bottom so the action sits at the natural focus point
            and the column visually anchors to the section's lower edge. */}
        <aside className="flex min-h-0 flex-col gap-3">
          {selectedEmployee ? (
            <div className="rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-600">
              <div className="font-semibold text-slate-900">{selectedEmployee.name}</div>
              {selectedEmployee.company ? (
                <div className="text-xs text-slate-500">{selectedEmployee.company}</div>
              ) : null}
              <div className="mt-1.5 text-xs">
                Stored:{" "}
                <span className="font-semibold">
                  {images.length} / {MAX_IMAGES_PER_EMPLOYEE}
                </span>{" "}
                image{images.length === 1 ? "" : "s"}
                {images.length < MIN_IMAGES_FOR_TRAINING ? (
                  <div className="mt-0.5 text-amber-700">
                    Need {MIN_IMAGES_FOR_TRAINING - images.length} more to train
                  </div>
                ) : null}
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white px-3.5 py-6 text-center text-sm text-muted-foreground">
              Pick an employee above.
            </div>
          )}

          {selectedId ? (
            <div className="rounded-xl border border-sky-100 bg-sky-50/60 px-3.5 py-2.5 text-xs text-sky-800">
              <div className="mb-1 font-semibold">Recommended angles</div>
              <ul className="list-inside list-disc space-y-0.5">
                <li>Front view</li>
                <li>Eye view</li>
                <li>Top view</li>
                <li>Down view</li>
                <li>Left-side view</li>
                <li>Right-side view</li>
              </ul>
              <div className="mt-1.5 text-[11px] text-sky-700/80">
                Min {MIN_IMAGES_FOR_TRAINING}, max {MAX_IMAGES_PER_EMPLOYEE} per employee.
              </div>
            </div>
          ) : null}

          {/* Train CTA — ``flex-1`` so the card itself stretches to fill
              the empty space between the recommendations and the section
              footer. Inside, the helper text sits at the top and the
              button is pushed to the bottom of the card with ``mt-auto``,
              so there's no awkward blank gap. Hidden while training or
              success owns the left slot so the section reads as one
              focused state. */}
          {trainingPhase === null && trainingResult === null ? (
            <div className="flex min-h-0 flex-1 flex-col gap-3 rounded-xl border border-slate-200 bg-white px-3.5 py-3">
              <div className="flex items-start gap-2 text-xs text-slate-600">
                <ScanFace className="h-4 w-4 shrink-0 text-primary" />
                <span>
                  Train using multiple angles for maximum recognition accuracy
                  on connected cameras.
                </span>
              </div>
              <Button
                type="button"
                size="lg"
                onClick={() => void handleTrain()}
                disabled={trainDisabled}
                className="mt-auto h-12 w-full gap-2 text-base font-semibold"
              >
                <Sparkles className="h-5 w-5" />
                Train
              </Button>
            </div>
          ) : null}
        </aside>
      </div>

      <AlertDialog
        open={deleting !== null}
        onOpenChange={(open) => {
          if (!open && !deletingBusy) setDeleting(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete face image?</AlertDialogTitle>
            <AlertDialogDescription>
              This permanently removes one image from this employee&apos;s face training set.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deletingBusy}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              disabled={deletingBusy}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deletingBusy ? "Deleting…" : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// -----------------------------------------------------------------------------
// Inline training panels — render INSIDE the Face Training section, no modal
// overlay. The parent component swaps between the idle Train button, this
// progress view, and the success view based on training state.
// -----------------------------------------------------------------------------

function TrainingInlinePanel({
  phase,
  employeeName,
  imageThumbnails,
}: {
  phase: TrainingPhase;
  employeeName: string;
  imageThumbnails: string[];
}) {
  const phaseIndex = PHASE_ORDER.indexOf(phase);
  const progressPct = ((phaseIndex + 1) / PHASE_ORDER.length) * 100;
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Face training in progress"
      className="h-full w-full rounded-xl border border-primary/30 bg-white px-5 py-5 shadow-sm"
    >
      <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-primary">
        <Layers className="h-4 w-4" />
        Face training pipeline
      </div>

      {/* Thumbnail strip with a sweeping scan-line — visualises the
          "images are being scanned" beat of the animation. */}
      {imageThumbnails.length > 0 ? (
        <div className="mb-3 grid grid-cols-6 gap-2">
          {imageThumbnails.slice(0, 6).map((src, i) => (
            <div
              key={`${src}-${i}`}
              className="relative aspect-square overflow-hidden rounded-md border border-slate-200 bg-slate-100"
            >
              <img
                src={src}
                alt={`Reference ${i + 1}`}
                className="h-full w-full object-cover"
              />
              <div
                className="pointer-events-none absolute inset-x-0 h-1 bg-gradient-to-b from-emerald-400/80 to-transparent"
                style={{
                  animation: "face-train-scan 1.2s linear infinite",
                  animationDelay: `${i * 120}ms`,
                }}
              />
            </div>
          ))}
        </div>
      ) : null}

      {/* Phase pills */}
      <div className="mb-3 grid grid-cols-4 gap-1.5">
        {PHASE_ORDER.map((p, i) => {
          const active = i === phaseIndex;
          const done = i < phaseIndex;
          return (
            <div
              key={p}
              className={cn(
                "flex flex-col items-center gap-1 rounded-lg border px-2 py-2 text-[10px] font-semibold uppercase tracking-wide transition-colors",
                done
                  ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                  : active
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-slate-200 bg-slate-50 text-slate-400",
              )}
            >
              {(() => {
                const Icon = PHASE_COPY[p].Icon;
                return (
                  <Icon
                    className={cn("h-4 w-4", active && "animate-pulse")}
                    aria-hidden="true"
                  />
                );
              })()}
              <span className="text-center leading-tight">{p}</span>
            </div>
          );
        })}
      </div>

      {/* Active phase copy + progress bar */}
      <div className="mb-2 flex items-center gap-2">
        {(() => {
          const Icon = PHASE_COPY[phase].Icon;
          return <Icon className="h-5 w-5 animate-pulse text-primary" aria-hidden="true" />;
        })()}
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-slate-900">
            {PHASE_COPY[phase].title}
            {employeeName ? <span className="text-slate-400"> · {employeeName}</span> : null}
          </div>
          <div className="truncate text-xs text-slate-500">{PHASE_COPY[phase].subtitle}</div>
        </div>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-primary transition-[width] duration-500"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Keyframe injected here so the parent doesn't need a global CSS rule. */}
      <style>{`
        @keyframes face-train-scan {
          0%   { top: 0; opacity: 0.0; }
          10%  { opacity: 1; }
          90%  { opacity: 1; }
          100% { top: 100%; opacity: 0.0; }
        }
      `}</style>
    </div>
  );
}

function TrainingSuccessInlinePanel({
  result,
  onDismiss,
}: {
  result: TrainingResult;
  onDismiss: () => void;
}) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex h-full w-full flex-col rounded-xl border border-emerald-200 bg-emerald-50/60 px-5 py-5 shadow-sm"
    >
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-emerald-700">
        <CheckCircle2 className="h-5 w-5" />
        Employee face trained successfully
      </div>
      <p className="mb-3 text-xs text-emerald-800/80">
        The recognition index now includes this employee&apos;s face data. They
        will be matched automatically the next time they appear on a connected
        camera.
      </p>
      <div className="flex items-center gap-3 rounded-lg border border-emerald-200 bg-white px-3 py-2.5">
        <Avatar className="h-12 w-12 border border-slate-200 bg-white">
          {result.employeeImage ? (
            <AvatarImage
              src={result.employeeImage}
              alt={result.employeeName}
              className="object-cover"
            />
          ) : null}
          <AvatarFallback className="text-base font-semibold text-slate-600">
            {(result.employeeName.charAt(0) || "?").toUpperCase()}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-slate-900">
            {result.employeeName}
          </div>
          <div className="text-xs text-slate-500">
            {result.accepted} embedding{result.accepted === 1 ? "" : "s"} stored
            {result.rejected > 0 ? ` · ${result.rejected} rejected` : ""}
          </div>
          <div className="mt-1 inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700">
            <CheckCircle2 className="h-3 w-3" />
            Training completed
          </div>
        </div>
      </div>
      {/* Centred Done button — ``mt-auto`` pushes it to the bottom of
          the (now full-height) success card so the action sits below
          the Training completed summary. */}
      <div className="mt-auto flex justify-center pt-4">
        <Button
          type="button"
          onClick={onDismiss}
          size="lg"
          className="h-11 min-w-[160px] gap-2 bg-emerald-600 text-white hover:bg-emerald-700"
        >
          <CheckCircle2 className="h-4 w-4" />
          Done
        </Button>
      </div>
    </div>
  );
}
