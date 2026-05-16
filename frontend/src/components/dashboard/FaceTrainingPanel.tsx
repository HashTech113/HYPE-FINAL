import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Cropper, { type Area } from "react-easy-crop";
import {
  AlertTriangle,
  BadgeCheck,
  CheckCircle2,
  Copy,
  Cpu,
  Crop as CropIcon,
  ImagePlus,
  Info,
  Layers,
  RefreshCcw,
  ScanFace,
  ScanLine,
  Sparkles,
  Trash2,
  XCircle,
} from "lucide-react";

import {
  AtCapacityError,
  BadImageError,
  type DuplicateFaceDetail,
  DuplicateFaceError,
  type Employee,
  type FaceImage,
  type FaceTrainingStatus,
  QualityLowerError,
  addFaceImage,
  captureFaceFromCamera,
  deleteFaceImage,
  enrollFaceImages,
  fullRetrainFaceImages,
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
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

// Fallback caps used only for the brief moment between selecting an
// employee and the first /face-images response landing. The backend
// returns the authoritative numbers in the ``training`` block of the
// list response — once that arrives, every UI gate switches over to
// ``trainingStatus.minRequired`` / ``maxRecommended``.
const FALLBACK_MIN = 3;
const FALLBACK_MAX = 6;

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

// Render the chosen crop region to a JPEG data URL. Mirrors the helper
// in EmployeeForm.tsx so the two cropping flows produce identical
// output (same quality, same format). 0.92 is a good face-training
// balance: visually lossless for the eye but ~30% smaller than 1.0.
async function getCroppedDataUrl(src: string, crop: Area): Promise<string> {
  const image = await new Promise<HTMLImageElement>((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("Failed to load image for cropping"));
    img.src = src;
  });
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(crop.width));
  canvas.height = Math.max(1, Math.round(crop.height));
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Canvas 2D context unavailable");
  ctx.drawImage(
    image,
    crop.x,
    crop.y,
    crop.width,
    crop.height,
    0,
    0,
    canvas.width,
    canvas.height,
  );
  return canvas.toDataURL("image/jpeg", 0.92);
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
  // Backend-supplied training status — drives the inline status block
  // ("Already Trained" / "Partially Trained" / "Not Trained") and the
  // capacity gate. Always reflects ACTUAL embeddings count, not visible
  // image rows (which can be stale after the post-train cleanup).
  const [trainingStatus, setTrainingStatus] = useState<FaceTrainingStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  // Inline notice — surfaced at the top of the panel (not a popup) for
  // bad-image rejections, "image quality lower than existing", and
  // similar non-blocking feedback. Auto-clears after ~5 s.
  const [notice, setNotice] = useState<{ kind: "info" | "warn" | "error"; text: string } | null>(null);
  const noticeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const showNotice = useCallback((kind: "info" | "warn" | "error", text: string) => {
    setNotice({ kind, text });
    if (noticeTimerRef.current) clearTimeout(noticeTimerRef.current);
    noticeTimerRef.current = setTimeout(() => setNotice(null), 5000);
  }, []);
  useEffect(() => () => {
    if (noticeTimerRef.current) clearTimeout(noticeTimerRef.current);
  }, []);
  const [deleting, setDeleting] = useState<FaceImage | null>(null);
  const [deletingBusy, setDeletingBusy] = useState<boolean>(false);
  const [trainingPhase, setTrainingPhase] = useState<TrainingPhase | null>(null);
  const [trainingResult, setTrainingResult] = useState<TrainingResult | null>(null);
  const [retrainBusy, setRetrainBusy] = useState<boolean>(false);
  const [capturingBusy, setCapturingBusy] = useState<boolean>(false);
  const [workerStatus, setWorkerStatus] = useState<RecognitionWorkersHealthResponse | null>(null);
  const [workerError, setWorkerError] = useState<string | null>(null);
  const [selectedCameraId, setSelectedCameraId] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  // Separate file input for the Full Retrain CTA so the same file
  // picker can route to the dedicated retrain endpoint.
  const retrainInputRef = useRef<HTMLInputElement | null>(null);

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

  // Duplicate-face prompt — opened by handleFiles when the backend
  // rejects an upload with 409. The dialog is async-Promise-driven: the
  // upload loop awaits ``askDuplicateConfirm`` and only resumes when the
  // admin clicks Cancel (false) or Continue/Retrain (true). Holding the
  // resolver in state lets us drive the dialog with the existing
  // AlertDialog component instead of a blocking window.confirm.
  const [duplicatePrompt, setDuplicatePrompt] = useState<{
    detail: DuplicateFaceDetail;
    selectedEmployeeName: string;
    resolve: (force: boolean) => void;
  } | null>(null);
  const askDuplicateConfirm = useCallback(
    (detail: DuplicateFaceDetail, selectedEmployeeName: string) =>
      new Promise<boolean>((resolve) => {
        setDuplicatePrompt({ detail, selectedEmployeeName, resolve });
      }),
    [],
  );
  const handleDuplicateChoice = (force: boolean) => {
    duplicatePrompt?.resolve(force);
    setDuplicatePrompt(null);
  };

  // (Replace-Weakest capacity prompt removed.) Per the latest spec,
  // when an employee is at the embedding cap the only allowed action
  // is Retrain — Add Face is hidden, the upload button is disabled,
  // and the inline status block tells the admin to use Retrain. If a
  // backend 409 at_capacity still leaks through (e.g. camera-capture
  // path), we surface it as an inline notice routing the admin to
  // Retrain rather than prompting for a partial-replace mid-batch.

  // Full-Retrain confirm — same Promise-driven AlertDialog pattern as
  // the duplicate / capacity prompts. Replaces the previous
  // ``window.confirm`` (the native dialog clashed visually with the
  // dark site chrome and looked unbranded).
  const [retrainConfirm, setRetrainConfirm] = useState<{
    employeeName: string;
    photoCount: number;
    resolve: (proceed: boolean) => void;
  } | null>(null);
  const askRetrainConfirm = useCallback(
    (employeeName: string, photoCount: number) =>
      new Promise<boolean>((resolve) => {
        setRetrainConfirm({ employeeName, photoCount, resolve });
      }),
    [],
  );
  const handleRetrainConfirm = (proceed: boolean) => {
    retrainConfirm?.resolve(proceed);
    setRetrainConfirm(null);
  };

  // Per-image crop step — opens AFTER the file is read into a data URL
  // but BEFORE it gets sent to the backend. Promise-driven so a batch
  // upload steps through one file at a time: each file awaits the
  // admin's crop / skip / cancel choice, then the loop continues with
  // the chosen bytes.
  //
  // Resolutions:
  //   string                — the cropped JPEG data URL, send this
  //   ``original``          — send the file unchanged (skip cropping)
  //   ``cancel``            — drop this file from the batch entirely
  const [cropPrompt, setCropPrompt] = useState<{
    source: string;
    fileName: string;
    index: number;
    total: number;
    resolve: (result: string | "original" | "cancel") => void;
  } | null>(null);
  const [cropPosition, setCropPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [cropZoom, setCropZoom] = useState<number>(1);
  const [cropArea, setCropArea] = useState<Area | null>(null);
  const [cropSaving, setCropSaving] = useState<boolean>(false);

  const askForCrop = useCallback(
    (source: string, fileName: string, index: number, total: number) =>
      new Promise<string | "original" | "cancel">((resolve) => {
        // Reset transform state per file so each new image starts
        // centered + at 1× zoom, not where the previous one left off.
        setCropPosition({ x: 0, y: 0 });
        setCropZoom(1);
        setCropArea(null);
        setCropSaving(false);
        setCropPrompt({ source, fileName, index, total, resolve });
      }),
    [],
  );
  const onCropComplete = useCallback((_: Area, pixels: Area) => {
    setCropArea(pixels);
  }, []);
  const finishCrop = (result: string | "original" | "cancel") => {
    cropPrompt?.resolve(result);
    setCropPrompt(null);
    setCropArea(null);
    setCropSaving(false);
  };
  const handleCropSave = async () => {
    if (!cropPrompt || !cropArea) return;
    try {
      setCropSaving(true);
      const cropped = await getCroppedDataUrl(cropPrompt.source, cropArea);
      finishCrop(cropped);
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "Failed to crop image");
      setCropSaving(false);
    }
  };

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
      const result = await getFaceImages(employeeId);
      setImages(result.items);
      setTrainingStatus(result.training);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Failed to load face images");
      setImages([]);
      setTrainingStatus(null);
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
      setTrainingStatus(null);
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

  // Slot accounting is driven by the BACKEND's embeddings count
  // (trainingStatus.embeddingsCount) rather than the count of visible
  // image rows. After Train, image_data on every row is cleared and
  // list_for_employee filters those out — so visible image count
  // would briefly show 0 even though the embeddings (and the cap)
  // still apply. Falls back to image count for the brief moment
  // before the first /face-images response lands.
  const minRequired = trainingStatus?.minRequired ?? FALLBACK_MIN;
  const maxRecommended = trainingStatus?.maxRecommended ?? FALLBACK_MAX;
  const trainedCount = trainingStatus?.embeddingsCount ?? images.length;
  const remainingSlots = Math.max(0, maxRecommended - trainedCount);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    if (!selectedId) {
      showNotice("warn", "Pick an employee first.");
      return;
    }
    // Frontend gate is friendly-only — the backend cap is the real
    // enforcement. We let admins ATTEMPT to upload past the cap so the
    // capacity prompt (Replace Weakest / Cancel) can fire per file.
    // For batch uploads we still trim the FIRST attempt list to the
    // available slots so we don't open a flurry of capacity prompts;
    // when at cap we accept the full batch and route every file
    // through the prompt.
    const allFiles = Array.from(files);
    const accepted =
      remainingSlots > 0 ? allFiles.slice(0, remainingSlots) : allFiles;
    if (remainingSlots > 0 && accepted.length < allFiles.length) {
      showNotice(
        "info",
        `Only the first ${accepted.length} image(s) will fit — recommended max is ${maxRecommended}.`,
      );
    }
    setUploading(true);
    let added = 0;
    let failed = 0;
    let cancelled = 0;
    const selectedName = selectedEmployee?.name ?? "this employee";
    try {
      for (let i = 0; i < accepted.length; i++) {
        const file = accepted[i];
        if (!file.type.startsWith("image/")) {
          failed += 1;
          continue;
        }
        try {
          const original = await readFileAsDataUrl(file);
          // Crop step. Admin can crop, use the original, or drop this
          // file from the batch entirely. We deliberately make this a
          // required step (not a quiet auto-pass) so admins notice the
          // option exists — but "Use Original" is one click away.
          const cropChoice = await askForCrop(original, file.name, i + 1, accepted.length);
          if (cropChoice === "cancel") {
            cancelled += 1;
            continue;
          }
          const dataUrl = cropChoice === "original" ? original : cropChoice;
          // Per-file state machine. Each attempt may resolve to:
          //   * success (saved=true, added += 1)
          //   * duplicate-prompt ⇒ retry with force=true (or skip)
          //   * at-capacity ⇒ retry with mode=replace_weakest (or skip)
          //   * BadImage / QualityLower ⇒ surface inline notice, skip
          //   * generic error ⇒ count as failed
          // Capped at three attempts so a misbehaving backend can't
          // trap us in a retry loop.
          let force = false;
          let mode: "add" | "replace_weakest" = "add";
          let saved = false;
          let skipFile = false;
          for (let attempt = 0; attempt < 3 && !saved && !skipFile; attempt++) {
            try {
              const created = await addFaceImage(
                selectedId,
                dataUrl,
                label.trim(),
                { force, mode },
              );
              setImages((prev) => [created, ...prev]);
              added += 1;
              saved = true;
            } catch (e) {
              if (e instanceof DuplicateFaceError && !force) {
                const proceed = await askDuplicateConfirm(e.detail, selectedName);
                if (!proceed) { cancelled += 1; skipFile = true; break; }
                force = true;
                continue;
              }
              if (e instanceof AtCapacityError) {
                // Per spec: at cap, Add Face is not allowed. Don't
                // offer a partial-replace fallback — direct the admin
                // to Retrain via an inline notice and skip this file.
                showNotice(
                  "warn",
                  `${selectedName} is already fully trained with ${e.detail.embeddingsCount} face embeddings. Use Retrain to replace the existing face data.`,
                );
                cancelled += 1;
                skipFile = true;
                break;
              }
              if (e instanceof BadImageError) {
                showNotice("error", e.message);
                failed += 1;
                skipFile = true;
                break;
              }
              if (e instanceof QualityLowerError) {
                showNotice("warn", e.message);
                cancelled += 1;
                skipFile = true;
                break;
              }
              throw e;
            }
          }
        } catch (error) {
          failed += 1;
          console.error("face image upload failed", error);
        }
      }
      if (added > 0) {
        const trailing = [
          failed > 0 ? `${failed} failed` : null,
          cancelled > 0 ? `${cancelled} skipped` : null,
        ]
          .filter(Boolean)
          .join(", ");
        showSuccess(
          `Uploaded ${added} image${added === 1 ? "" : "s"}` +
            (trailing ? ` (${trailing})` : ""),
        );
      } else if (cancelled > 0 && failed === 0) {
        showSuccess(
          `${cancelled} upload${cancelled === 1 ? "" : "s"} cancelled.`,
        );
      } else if (failed > 0) {
        window.alert(`All ${failed} upload(s) failed.`);
      }
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
      // Refresh from the server so the status block reflects new
      // embeddings (especially when replace_weakest evicted a row —
      // we wouldn't otherwise know the count change).
      if (selectedId) void loadImages(selectedId);
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
      // Re-pull status: deleting an image cascades to its embedding
      // and shrinks the trained count.
      if (selectedId) void loadImages(selectedId);
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
    if (images.length < minRequired) {
      showNotice(
        "warn",
        `Upload at least ${minRequired} images (front / left / right) before training.`,
      );
      return;
    }
    const employeeName = selectedEmployee?.name ?? "Employee";
    const employeeImage = selectedEmployee?.imageUrl;
    const beforeThumbs = images.slice(0, 6).map((i) => i.imageUrl);
    try {
      // Race the enroll API and the minimum animation duration; await
      // the API result directly so TypeScript can narrow the value to
      // its non-null type after the Promise.all resolves.
      const apiPromise = enrollFaceImages(selectedId);
      await runTrainingAnimation(apiPromise);
      const summary = await apiPromise;
      setImages(summary.items);
      setTrainingStatus(summary.training);
      setTrainingResult({
        accepted: summary.accepted,
        rejected: summary.rejected,
        employeeName,
        employeeImage,
        imageThumbnails: beforeThumbs,
      });
    } catch (error) {
      window.alert(error instanceof Error ? error.message : "Training failed");
    } finally {
      setTrainingPhase(null);
    }
  };

  // Full Retrain — destructive: deletes every existing embedding for
  // the selected employee and replaces them with a fresh batch of
  // photos. Backend validates the entire batch up front and rejects
  // 422 if any single photo fails the quality gate, so we never end
  // up halfway through.
  const handleFullRetrain = async (files: FileList | null) => {
    if (!files || !selectedId) return;
    const list = Array.from(files);
    if (list.length < minRequired) {
      showNotice("warn", `Full Retrain needs at least ${minRequired} clear photos.`);
      return;
    }
    if (list.length > maxRecommended) {
      showNotice("warn", `Full Retrain accepts at most ${maxRecommended} photos.`);
      return;
    }
    const proceed = await askRetrainConfirm(
      selectedEmployee?.name ?? "this employee",
      list.length,
    );
    if (!proceed) {
      if (retrainInputRef.current) retrainInputRef.current.value = "";
      return;
    }
    setRetrainBusy(true);
    try {
      // Cropper runs sequentially per file so each photo can be framed
      // individually before the destructive replace fires.
      const originals = await Promise.all(list.map(readFileAsDataUrl));
      const cropped: string[] = [];
      for (let i = 0; i < originals.length; i++) {
        const choice = await askForCrop(originals[i], list[i].name, i + 1, originals.length);
        if (choice === "cancel") {
          showNotice("warn", "Retrain cancelled — at least one photo was dropped.");
          setRetrainBusy(false);
          if (retrainInputRef.current) retrainInputRef.current.value = "";
          return;
        }
        cropped.push(choice === "original" ? originals[i] : choice);
      }
      const summary = await fullRetrainFaceImages(
        selectedId,
        cropped.map((dataUrl) => ({ image: dataUrl, label: label.trim() })),
      );
      setImages(summary.items);
      setTrainingStatus(summary.training);
      showSuccess(
        `Full retrain complete — ${summary.deletedEmbeddings} old embedding(s) removed, ` +
        `${summary.accepted} new embedding(s) stored.`,
      );
    } catch (error) {
      if (error instanceof BadImageError) {
        showNotice("error", error.message);
      } else {
        showNotice("error", error instanceof Error ? error.message : "Full retrain failed");
      }
    } finally {
      setRetrainBusy(false);
      if (retrainInputRef.current) retrainInputRef.current.value = "";
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
      // Refresh status — capture goes through the same enrollment
      // path, so trainedCount changed.
      void loadImages(selectedId);
    } catch (error) {
      // Camera capture honors the same per-employee cap. Surface a
      // useful inline notice instead of a blank alert when we hit it.
      const msg = error instanceof Error ? error.message : "Camera capture failed";
      showNotice("error", msg);
    } finally {
      setCapturingBusy(false);
    }
  };

  const trainDisabled =
    !selectedId || trainingPhase !== null || images.length < minRequired;

  return (
    <div className="relative flex min-h-0 flex-1 flex-col gap-4">
      {/* Floated success overlay — pinned to the top of the panel,
          outside the flex flow, so showing it doesn't shrink the body
          below. */}
      {successMessage ? (
        <div className="pointer-events-none absolute inset-x-0 -top-10 z-30 flex justify-center px-2">
          <div
            role="status"
            aria-live="polite"
            className="pointer-events-auto flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3.5 py-2.5 text-sm font-medium text-emerald-700 shadow-md"
          >
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{successMessage}</span>
          </div>
        </div>
      ) : null}

      {/* Inline notice (info / warn / error) — bad-image rejections,
          quality-lower retrain refusals, generic capacity messages.
          Rendered ABOVE the controls (in-flow, not absolute) so the
          admin sees it on the natural reading path. */}
      {notice ? (
        <div
          role="status"
          aria-live="polite"
          className={cn(
            "flex items-start gap-2 rounded-xl border px-3.5 py-2.5 text-sm",
            notice.kind === "error" && "border-rose-200 bg-rose-50 text-rose-700",
            notice.kind === "warn" && "border-amber-200 bg-amber-50 text-amber-800",
            notice.kind === "info" && "border-sky-200 bg-sky-50 text-sky-800",
          )}
        >
          {notice.kind === "error" ? (
            <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
          ) : notice.kind === "warn" ? (
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          ) : (
            <Info className="mt-0.5 h-4 w-4 shrink-0" />
          )}
          <span>{notice.text}</span>
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
        {/* Single upload action — Upload images is the only entry
            point for adding photos. The Retrain primary CTA (right
            sidebar) is the destructive replace-all path; the old
            separate "Full Retrain" button was confusing alongside it
            and has been folded into the single Retrain action. */}
        <div className="flex items-end gap-2">
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
          {/* Retrain file picker is hidden; the primary CTA in the
              right sidebar opens it when the employee is already
              trained. */}
          <input
            ref={retrainInputRef}
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            onChange={(e) => void handleFullRetrain(e.target.files)}
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
            // Layout adapts to image count so a sparse set doesn't
            // leave a big empty bottom row:
            //   • ≤ 3 photos → single auto-sized row, place-content-
            //     center vertically. Cards take their natural aspect
            //     and the group sits centered in the panel.
            //   • 4-6 photos → original 3-col × 2-row grid with
            //     ``grid-rows-2`` fills the height (each card flex-1
            //     fills its row).
            <div
              className={cn(
                "grid h-full min-h-0 grid-cols-3 gap-3",
                images.length <= 3
                  ? "place-content-center"
                  : "grid-rows-2",
              )}
            >
              {images.map((img) => (
                <div
                  key={img.id}
                  className={cn(
                    "group relative flex min-h-0 flex-col overflow-hidden rounded-xl border border-slate-200 bg-white",
                    // Lock card to a square when we're centering a
                    // small set, so each one stays a sensible size
                    // (auto-sized rows would otherwise produce ~zero
                    // height cells since the image is absolutely
                    // positioned).
                    images.length <= 3 && "aspect-square",
                  )}
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
            <TrainingStatusCard
              employeeName={selectedEmployee.name}
              company={selectedEmployee.company}
              status={trainingStatus}
              minRequired={minRequired}
              maxRecommended={maxRecommended}
            />
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
                Min {minRequired}, max {maxRecommended} per employee.
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
              {/* Primary CTA: three states keyed off what's in the
                  grid + the backend trained status.
                    • images present     → Train (commit pending photos,
                                            then post-train cleanup
                                            clears image_data so they
                                            stop showing as pending)
                    • no images, trained → Retrain (destructive replace)
                    • no images, not yet → Train Face (disabled until min)

                  Rationale: after upload, the admin sees their photos
                  in the grid and expects a Train button to finalize.
                  Routing them to Retrain in that moment would be both
                  destructive AND counter-intuitive — embeddings were
                  already created inline; "Retrain" should only mean
                  the explicit start-over flow. */}
              {images.length > 0 ? (
                <Button
                  type="button"
                  size="lg"
                  onClick={() => void handleTrain()}
                  disabled={!selectedId || trainingPhase !== null}
                  className="mt-auto h-12 w-full gap-2 text-base font-semibold"
                >
                  <Sparkles className="h-5 w-5" />
                  Train
                </Button>
              ) : trainingStatus?.status === "trained" ||
                trainingStatus?.status === "over_cap" ? (
                <Button
                  type="button"
                  size="lg"
                  onClick={() => retrainInputRef.current?.click()}
                  disabled={!selectedId || retrainBusy}
                  className="mt-auto h-12 w-full gap-2 bg-amber-600 text-base font-semibold text-white hover:bg-amber-700"
                >
                  <RefreshCcw className={cn("h-5 w-5", retrainBusy && "animate-spin")} />
                  {retrainBusy ? "Retraining…" : "Retrain"}
                </Button>
              ) : (
                <Button
                  type="button"
                  size="lg"
                  onClick={() => void handleTrain()}
                  disabled={trainDisabled}
                  className="mt-auto h-12 w-full gap-2 text-base font-semibold"
                >
                  <Sparkles className="h-5 w-5" />
                  Train Face
                </Button>
              )}
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

      {/* Duplicate-face prompt — opened by handleFiles when the
          backend rejects an upload with 409. Two visual variants:
          - Same employee:   info-style, "add another angle?"
          - Different person: warning-style, catches wrong-employee selection.
          Closing the dialog without picking either button is treated
          as Cancel (keeps the upload loop honest). */}
      <AlertDialog
        open={duplicatePrompt !== null}
        onOpenChange={(open) => {
          if (!open && duplicatePrompt) handleDuplicateChoice(false);
        }}
      >
        <AlertDialogContent>
          {duplicatePrompt ? (
            <>
              <AlertDialogHeader>
                <AlertDialogTitle className="flex items-center gap-2">
                  {duplicatePrompt.detail.sameEmployee ? (
                    <Copy className="h-5 w-5 text-sky-600" />
                  ) : (
                    <AlertTriangle className="h-5 w-5 text-amber-600" />
                  )}
                  {duplicatePrompt.detail.sameEmployee
                    ? "Face already trained for this employee"
                    : "This face matches a different employee"}
                </AlertDialogTitle>
                <AlertDialogDescription asChild>
                  <div className="space-y-2 text-sm text-slate-600">
                    {duplicatePrompt.detail.sameEmployee ? (
                      <>
                        <p>
                          This face already appears to be trained for{" "}
                          <span className="font-semibold text-slate-900">
                            {duplicatePrompt.detail.matchedName}
                          </span>
                          .
                        </p>
                        <p className="text-xs text-slate-500">
                          Use <strong>Retrain</strong> on the right panel if you want
                          to replace the old face data. Adding another copy is
                          rarely needed.
                        </p>
                      </>
                    ) : (
                      <p>
                        This face already matches{" "}
                        <span className="font-semibold text-slate-900">
                          {duplicatePrompt.detail.matchedName}
                        </span>
                        . You are about to train it for{" "}
                        <span className="font-semibold text-slate-900">
                          {duplicatePrompt.selectedEmployeeName}
                        </span>
                        . Please check the selected employee — continue only if this is intentional.
                      </p>
                    )}
                    <p className="text-xs text-slate-500">
                      Match confidence:{" "}
                      <span className="font-medium tabular-nums text-slate-700">
                        {Math.round(duplicatePrompt.detail.score * 100)}%
                      </span>
                    </p>
                  </div>
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                {/* Same-employee: default is Skip (safe). Cross-
                    employee: default is Cancel (safer). Both surface
                    the same destructive verb on the confirm button. */}
                <AlertDialogCancel onClick={() => handleDuplicateChoice(false)}>
                  {duplicatePrompt.detail.sameEmployee ? "Skip" : "Cancel"}
                </AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => handleDuplicateChoice(true)}
                  className={cn(
                    duplicatePrompt.detail.sameEmployee
                      ? "bg-sky-600 text-white hover:bg-sky-700"
                      : "bg-amber-600 text-white hover:bg-amber-700",
                  )}
                >
                  {duplicatePrompt.detail.sameEmployee
                    ? "Add Anyway"
                    : "Continue Anyway"}
                </AlertDialogAction>
              </AlertDialogFooter>
            </>
          ) : null}
        </AlertDialogContent>
      </AlertDialog>

      {/* Retrain confirm — destructive, so styled like the delete
          dialog with the same rose action color. Native browser
          confirm() looked unbranded against the dashboard chrome.
          Copy matches the product spec's "replace existing face
          embeddings with the new selected images" wording. */}
      <AlertDialog
        open={retrainConfirm !== null}
        onOpenChange={(open) => {
          if (!open && retrainConfirm) handleRetrainConfirm(false);
        }}
      >
        <AlertDialogContent>
          {retrainConfirm ? (
            <>
              <AlertDialogHeader>
                <AlertDialogTitle className="flex items-center gap-2">
                  <RefreshCcw className="h-5 w-5 text-rose-600" />
                  Retrain this employee?
                </AlertDialogTitle>
                <AlertDialogDescription asChild>
                  <div className="space-y-2 text-sm text-slate-600">
                    <p>
                      Retraining will <strong className="text-rose-600">remove</strong>{" "}
                      the old face embeddings for{" "}
                      <span className="font-semibold text-slate-900">
                        {retrainConfirm.employeeName}
                      </span>{" "}
                      and train them with the{" "}
                      <span className="font-semibold text-slate-900 tabular-nums">
                        {retrainConfirm.photoCount}
                      </span>{" "}
                      new image{retrainConfirm.photoCount === 1 ? "" : "s"} you selected. Continue?
                    </p>
                    <p className="text-xs text-slate-500">
                      Safe replace: the new images are validated and
                      embeddings are staged <em>before</em> the old set is
                      removed. If validation fails, the existing trained
                      faces stay exactly as they were.
                    </p>
                  </div>
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel onClick={() => handleRetrainConfirm(false)}>
                  Cancel
                </AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => handleRetrainConfirm(true)}
                  className="bg-rose-600 text-white hover:bg-rose-700"
                >
                  Retrain
                </AlertDialogAction>
              </AlertDialogFooter>
            </>
          ) : null}
        </AlertDialogContent>
      </AlertDialog>

      {/* Per-file crop step. Closing via X / Esc / outside-click is
          treated as Cancel (drop this file from the batch) — same
          convention as the other prompts. */}
      <Dialog
        open={cropPrompt !== null}
        onOpenChange={(open) => {
          if (!open && cropPrompt) finishCrop("cancel");
        }}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CropIcon className="h-5 w-5 text-primary" />
              Crop image
              {cropPrompt && cropPrompt.total > 1 ? (
                <span className="ml-1 text-xs font-normal text-slate-500">
                  ({cropPrompt.index} of {cropPrompt.total})
                </span>
              ) : null}
            </DialogTitle>
          </DialogHeader>
          {cropPrompt ? (
            <div className="space-y-3">
              <div className="truncate text-xs text-slate-500" title={cropPrompt.fileName}>
                {cropPrompt.fileName}
              </div>
              {/* Square aspect — InsightFace's input pipeline resizes
                  to a square anyway, and the head-shot framing reads
                  cleanly. ``showGrid`` helps the admin center on the
                  face. */}
              <div className="relative h-72 w-full overflow-hidden rounded-lg bg-slate-900">
                <Cropper
                  image={cropPrompt.source}
                  crop={cropPosition}
                  zoom={cropZoom}
                  aspect={1}
                  showGrid
                  onCropChange={setCropPosition}
                  onZoomChange={setCropZoom}
                  onCropComplete={onCropComplete}
                />
              </div>
              <div className="flex items-center gap-2">
                <Label className="text-xs font-medium text-slate-600">Zoom</Label>
                <input
                  type="range"
                  min={1}
                  max={3}
                  step={0.01}
                  value={cropZoom}
                  onChange={(e) => setCropZoom(Number(e.target.value))}
                  className="flex-1 accent-primary"
                />
                <span className="w-10 text-right text-xs tabular-nums text-slate-500">
                  {cropZoom.toFixed(2)}×
                </span>
              </div>
              <p className="text-[11px] leading-snug text-slate-500">
                Center the face in the square — leave a small margin around the
                head. Click <strong>Use Original</strong> to skip cropping for
                this file.
              </p>
            </div>
          ) : null}
          <DialogFooter className="gap-2 sm:gap-2">
            <Button
              variant="outline"
              onClick={() => finishCrop("cancel")}
              disabled={cropSaving}
            >
              Cancel
            </Button>
            <Button
              variant="ghost"
              onClick={() => finishCrop("original")}
              disabled={cropSaving}
            >
              Use Original
            </Button>
            <Button
              onClick={() => void handleCropSave()}
              disabled={!cropArea || cropSaving}
            >
              {cropSaving ? "Cropping…" : "Save Crop"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// -----------------------------------------------------------------------------
// Inline status / training panels — render INSIDE the Face Training section.
// The parent component swaps between the idle Train button, the progress
// view, and the success view based on training state.
// -----------------------------------------------------------------------------

function TrainingStatusCard({
  employeeName,
  company,
  status,
  minRequired,
  maxRecommended,
}: {
  employeeName: string;
  company?: string;
  status: FaceTrainingStatus | null;
  minRequired: number;
  maxRecommended: number;
}) {
  // Visual variant per status. Drives the badge color, the body
  // copy, and (for the over_cap legacy state) a clarifying line so
  // ops know the cap is now backend-enforced.
  const count = status?.embeddingsCount ?? 0;
  const variant: { label: string; tone: string; iconCls: string; Icon: typeof BadgeCheck } =
    status?.status === "trained"
      ? { label: "Already Trained", tone: "border-emerald-200 bg-emerald-50 text-emerald-800", iconCls: "text-emerald-600", Icon: BadgeCheck }
      : status?.status === "partial"
      ? { label: "Partially Trained", tone: "border-amber-200 bg-amber-50 text-amber-900", iconCls: "text-amber-600", Icon: AlertTriangle }
      : status?.status === "over_cap"
      ? { label: "Over Cap", tone: "border-rose-200 bg-rose-50 text-rose-800", iconCls: "text-rose-600", Icon: AlertTriangle }
      : { label: "Not Trained", tone: "border-slate-200 bg-slate-50 text-slate-700", iconCls: "text-slate-500", Icon: Info };
  const { Icon } = variant;
  return (
    <div className={cn("rounded-xl border px-3.5 py-2.5 text-sm", variant.tone)}>
      <div className="font-semibold text-slate-900">{employeeName}</div>
      {company ? <div className="text-xs text-slate-500">{company}</div> : null}
      <div className="mt-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide">
        <Icon className={cn("h-3.5 w-3.5", variant.iconCls)} />
        {variant.label}
      </div>
      <div className="mt-1 text-xs">
        Embeddings:{" "}
        <span className="font-semibold tabular-nums">
          {count} / {maxRecommended}
        </span>
        {" · min "}
        <span className="tabular-nums">{minRequired}</span>
      </div>
      {status?.status === "trained" && count >= maxRecommended ? (
        // At-capacity (fully trained) wording — distinct from the
        // generic "trained" copy. Tells the admin Add Face is gated
        // and Retrain is the only path to change the face set.
        <div className="mt-1 text-[11px] leading-snug text-emerald-700/80">
          This employee is already fully trained with {count} face embedding
          {count === 1 ? "" : "s"}. Use <strong>Retrain</strong> to replace the
          existing face data with new images.
        </div>
      ) : status?.status === "trained" ? (
        <div className="mt-1 text-[11px] leading-snug text-emerald-700/80">
          This employee is already trained with {count} face embedding
          {count === 1 ? "" : "s"}. Add more angles up to {maxRecommended}, or
          Retrain to replace the existing set.
        </div>
      ) : status?.status === "partial" ? (
        <div className="mt-1 text-[11px] leading-snug">
          Need {minRequired - count} more clear photo
          {minRequired - count === 1 ? "" : "s"} to train.
        </div>
      ) : status?.status === "over_cap" ? (
        <div className="mt-1 text-[11px] leading-snug">
          Cap is now {maxRecommended}. New uploads will be rejected — use
          Retrain to start fresh.
        </div>
      ) : null}
    </div>
  );
}

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
        // Centered flex strip instead of a fixed 6-col grid — fewer
        // than 6 thumbnails used to be left-stacked with a large
        // empty right half. justify-center + width-capped children
        // keeps the strip looking intentional at any count.
        <div className="mb-3 flex flex-wrap justify-center gap-2">
          {imageThumbnails.slice(0, 6).map((src, i) => (
            <div
              key={`${src}-${i}`}
              className="relative aspect-square w-[14%] min-w-[64px] max-w-[110px] overflow-hidden rounded-md border border-slate-200 bg-slate-100"
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
