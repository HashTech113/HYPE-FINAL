"use client";

import {
  Camera as CameraIcon,
  Loader2,
  Power,
  RefreshCw,
  Trash2,
  Video,
  VideoOff,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Props {
  /** Disable everything (e.g. submitting / max images reached). */
  disabled?: boolean;
  /** Submitting state from the upload mutation. */
  submitting?: boolean;
  /**
   * Called when the user hits "Save". Receives one File per snapshot
   * the user has taken since opening the panel — they're sent in a
   * single batch through the existing `/training/images` upload
   * endpoint, so they share embedding-cache invalidation, the
   * `replace` option, etc.
   */
  onSubmit: (files: File[], replace: boolean) => void;
  /** Cap the number of snapshots the user can hold in the queue. */
  max: number;
}

const VIDEO_CONSTRAINTS: MediaStreamConstraints = {
  video: {
    width: { ideal: 1280 },
    height: { ideal: 720 },
    facingMode: "user",
  },
  audio: false,
};

interface Snapshot {
  id: string;
  blob: Blob;
  url: string; // object URL for the thumbnail
}

export function WebcamCapture({
  disabled,
  submitting,
  onSubmit,
  max,
}: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [replace, setReplace] = useState(false);

  // Always tear down stream + revoke blob URLs on unmount or stream swap.
  useEffect(() => {
    return () => {
      stream?.getTracks().forEach((t) => t.stop());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream]);

  useEffect(() => {
    return () => {
      snapshots.forEach((s) => URL.revokeObjectURL(s.url));
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Wire the stream into the <video> as soon as both exist.
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    v.srcObject = stream;
    if (stream) v.play().catch(() => undefined);
  }, [stream]);

  const startCamera = useCallback(async () => {
    setError(null);
    setStarting(true);
    try {
      if (
        typeof navigator === "undefined" ||
        !navigator.mediaDevices?.getUserMedia
      ) {
        throw new Error("This browser doesn't support webcam access.");
      }
      const next = await navigator.mediaDevices.getUserMedia(VIDEO_CONSTRAINTS);
      setStream((prev) => {
        prev?.getTracks().forEach((t) => t.stop());
        return next;
      });
    } catch (e) {
      const msg =
        e instanceof Error
          ? e.message
          : "Could not start the webcam.";
      setError(msg);
      toast.error(msg);
    } finally {
      setStarting(false);
    }
  }, []);

  const stopCamera = useCallback(() => {
    setStream((prev) => {
      prev?.getTracks().forEach((t) => t.stop());
      return null;
    });
  }, []);

  const takeSnapshot = useCallback(() => {
    const v = videoRef.current;
    if (!v || !stream) {
      toast.error("Start the webcam first");
      return;
    }
    if (snapshots.length >= max) {
      toast.error(`At most ${max} snapshot${max === 1 ? "" : "s"} per batch`);
      return;
    }
    const w = v.videoWidth;
    const h = v.videoHeight;
    if (!w || !h) {
      toast.error("Webcam frame not ready yet");
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      toast.error("Could not get a 2D drawing context");
      return;
    }
    ctx.drawImage(v, 0, 0, w, h);
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          toast.error("Could not encode the snapshot");
          return;
        }
        const id =
          (typeof crypto !== "undefined" && "randomUUID" in crypto
            ? crypto.randomUUID()
            : Math.random().toString(36).slice(2)) + ".jpg";
        const url = URL.createObjectURL(blob);
        setSnapshots((prev) => [...prev, { id, blob, url }]);
      },
      "image/jpeg",
      0.92,
    );
  }, [stream, snapshots.length, max]);

  const removeSnapshot = useCallback((id: string) => {
    setSnapshots((prev) => {
      const tgt = prev.find((s) => s.id === id);
      if (tgt) URL.revokeObjectURL(tgt.url);
      return prev.filter((s) => s.id !== id);
    });
  }, []);

  const submit = useCallback(() => {
    if (snapshots.length === 0) {
      toast.error("Take at least one snapshot first");
      return;
    }
    const files = snapshots.map(
      (s) =>
        new File([s.blob], `webcam-${s.id}`, {
          type: "image/jpeg",
          lastModified: Date.now(),
        }),
    );
    onSubmit(files, replace);
    // Mutation parent will reset by re-rendering; but we also clear our
    // local queue so the "saved" state is unambiguous.
    snapshots.forEach((s) => URL.revokeObjectURL(s.url));
    setSnapshots([]);
  }, [snapshots, replace, onSubmit]);

  const live = stream !== null;

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-md border bg-black">
        <div className="relative aspect-video w-full">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={cn(
              "h-full w-full object-contain transition-opacity",
              !live && "opacity-30",
            )}
          />
          {!live && (
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-2 text-white/80">
              <VideoOff className="h-8 w-8" />
              <p className="text-sm">
                Webcam is off. Click <span className="font-medium">Start</span>{" "}
                to enable.
              </p>
              {error && (
                <p className="max-w-[80%] text-center text-xs text-amber-300">
                  {error}
                </p>
              )}
            </div>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2 border-t bg-background p-2">
          {!live ? (
            <Button
              size="sm"
              variant="outline"
              onClick={startCamera}
              disabled={starting || disabled}
            >
              {starting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Video className="h-4 w-4" />
              )}
              {starting ? "Starting…" : "Start webcam"}
            </Button>
          ) : (
            <>
              <Button
                size="sm"
                variant="outline"
                onClick={stopCamera}
                disabled={disabled}
              >
                <Power className="h-4 w-4" />
                Stop
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  stopCamera();
                  void startCamera();
                }}
                disabled={disabled || starting}
              >
                <RefreshCw className="h-4 w-4" />
                Restart
              </Button>
              <Button
                size="sm"
                onClick={takeSnapshot}
                disabled={disabled || snapshots.length >= max}
              >
                <CameraIcon className="h-4 w-4" />
                Capture ({snapshots.length}/{max})
              </Button>
            </>
          )}
        </div>
      </div>

      {snapshots.length > 0 && (
        <div className="space-y-3 rounded-md border p-3">
          <p className="text-sm font-medium">
            {snapshots.length} snapshot{snapshots.length === 1 ? "" : "s"} ready
            to enroll
          </p>
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-5 md:grid-cols-6">
            {snapshots.map((s) => (
              <div
                key={s.id}
                className="group relative overflow-hidden rounded-md border bg-card"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={s.url}
                  alt="Webcam snapshot"
                  className="aspect-square w-full object-cover"
                />
                <button
                  type="button"
                  aria-label="Remove snapshot"
                  onClick={() => removeSnapshot(s.id)}
                  disabled={submitting}
                  className="absolute right-1.5 top-1.5 inline-flex h-6 w-6 items-center justify-center rounded-full bg-black/60 text-white opacity-0 shadow transition-opacity hover:bg-destructive focus:opacity-100 group-hover:opacity-100 disabled:pointer-events-none"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between gap-2">
            <label className="flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-input accent-primary"
                checked={replace}
                onChange={(e) => setReplace(e.target.checked)}
                disabled={submitting}
              />
              Replace existing images for this employee
            </label>
            <Button
              size="sm"
              onClick={submit}
              disabled={disabled || submitting || snapshots.length === 0}
            >
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <CameraIcon className="h-4 w-4" />
              )}
              {submitting
                ? "Enrolling…"
                : `Enroll ${snapshots.length} face${
                    snapshots.length === 1 ? "" : "s"
                  }`}
            </Button>
          </div>
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        Snapshots are uploaded to the backend like regular training images.
        Detection + embedding happens server-side using the same InsightFace
        model the cameras use, so accuracy is identical to the other tabs.
      </p>
    </div>
  );
}
