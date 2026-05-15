"use client";

import {
  Activity,
  AlertTriangle,
  Camera as CameraIcon,
  Clock,
  Loader2,
  PowerOff,
  RefreshCw,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { camerasApi } from "@/lib/api/cameras";
import { getToken } from "@/lib/auth/session";
import { useRestartCamera } from "@/lib/hooks/use-cameras";
import type { Camera, CameraHealth } from "@/lib/types/camera";
import { cn } from "@/lib/utils";

interface Props {
  camera: Camera;
  health?: CameraHealth;
  index?: number;
}

// One persistent MJPEG connection per camera. The browser handles the
// `multipart/x-mixed-replace` framing natively and paints each new JPEG
// the moment it arrives — no per-frame HTTP overhead, no
// 6-per-origin cap exhaustion, and no broken-image-icon-stuck-until-
// page-refresh bug that the polling-based <img + ?t=tick> approach
// suffered from. If the stream errors or the tab regains focus, we
// re-mount the <img> with a fresh `?ts=…` so the browser opens a new
// connection cleanly (some browsers don't refire <img> on identical URL).

// Soft "reconnecting" indicator threshold. If we haven't seen a fresh
// frame in this long (per the worker's last_frame_age_seconds health
// signal), show a subtle overlay so a 1–2 s RTSP blip doesn't look
// like a frozen tile.
const RECONNECTING_THRESHOLD_MS = 1_200;
// Hard "stale" — the camera is genuinely down, not a brief blip.
const STALE_THRESHOLD_MS = 10_000;
// On <img onError>, wait this long then force re-mount to reconnect.
// MJPEG-side: TCP-level disconnects (server restart, network drop)
// fire onError. Browsers normally retry once, but some leave the
// element in a permanent broken state.
const ERROR_REMOUNT_DELAY_MS = 1_500;
// If the health endpoint reports the worker hasn't produced a frame
// in this long, force a re-mount. Catches the edge case where the
// MJPEG connection is open but the upstream stalled silently.
const HEALTH_REMOUNT_THRESHOLD_MS = 8_000;

export function CameraPreviewTile({ camera, health, index = 0 }: Props) {
  const token = typeof window !== "undefined" ? getToken() : undefined;

  // Stagger first connect by index so 4 tiles don't open MJPEG
  // sockets in the same millisecond on mount.
  const [ready, setReady] = useState(index === 0);
  useEffect(() => {
    if (ready) return;
    const t = window.setTimeout(() => setReady(true), index * 80);
    return () => window.clearTimeout(t);
  }, [ready, index]);

  // `mountEpoch` bumps whenever we want to force-reopen the stream.
  // Bumping it changes the <img>'s `?ts=…` query, which makes the
  // browser drop the old connection and open a fresh one.
  const [mountEpoch, setMountEpoch] = useState<number>(() => Date.now());
  const reconnect = useCallback(() => setMountEpoch(Date.now()), []);

  // Pause when the tab is hidden; reconnect when it returns. Without
  // this, 4 streams keep eating bandwidth in background tabs and the
  // browser may suspend rendering anyway, leaving stale pixels visible
  // on tab regain. We force a fresh connect on regain to avoid that.
  const [tabVisible, setTabVisible] = useState(
    typeof document === "undefined" ? true : document.visibilityState === "visible",
  );
  useEffect(() => {
    if (typeof document === "undefined") return;
    const onVis = () => {
      const v = document.visibilityState === "visible";
      setTabVisible(v);
      if (v) setMountEpoch(Date.now());
    };
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);

  const streamUrl = useMemo(() => {
    if (!camera.is_active || !token || !ready || !tabVisible) return null;
    const base = camerasApi.mjpegUrl(camera.id, token, {
      fps: 15,
      annotated: true,
      quality: 75,
    });
    // Append the mount epoch so re-mounts always produce a unique URL
    // — some browsers won't reopen an MJPEG with an identical src.
    const sep = base.includes("?") ? "&" : "?";
    return `${base}${sep}ts=${mountEpoch}`;
  }, [camera.id, camera.is_active, token, ready, tabVisible, mountEpoch]);

  const [imgError, setImgError] = useState(false);
  const [updatedAt, setUpdatedAt] = useState<number | null>(null);

  // Reset error/loaded state when the stream URL changes (mount /
  // remount). Without this a successful previous render would keep
  // hasFirstFrame=true even after we deliberately tore down the
  // stream, which made the "Stale" badge race the new connection.
  useEffect(() => {
    if (!streamUrl) return;
    setImgError(false);
    setUpdatedAt(null);
  }, [streamUrl]);

  // Auto-retry on <img onError>. The browser fires onError when the
  // server closes the stream (e.g. backend restart) or when DNS / TCP
  // fails. We schedule a single re-mount after a short delay rather
  // than tight-looping; the new mount produces a fresh URL so the
  // browser opens a brand new connection.
  useEffect(() => {
    if (!imgError || !streamUrl) return;
    const t = window.setTimeout(reconnect, ERROR_REMOUNT_DELAY_MS);
    return () => window.clearTimeout(t);
  }, [imgError, streamUrl, reconnect]);

  // If the health endpoint says the worker hasn't produced a fresh
  // frame in a while but our MJPEG connection is still open and
  // didn't fire onError, force a reconnect. This catches the silent-
  // stall failure mode (TCP open, no bytes flowing) which is the
  // single most common cause of "tile is black, page refresh fixes it".
  const healthAgeMs =
    health?.last_frame_age_seconds != null
      ? Math.round(health.last_frame_age_seconds * 1000)
      : null;
  useEffect(() => {
    if (!streamUrl) return;
    if (healthAgeMs == null) return;
    if (healthAgeMs < HEALTH_REMOUNT_THRESHOLD_MS) return;
    reconnect();
    // Intentionally only re-runs when crossing the threshold.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [Math.floor((healthAgeMs ?? 0) / 1000), streamUrl]);

  const restart = useRestartCamera();
  const imgRef = useRef<HTMLImageElement | null>(null);

  const error = imgError ? "Stream disconnected — reconnecting…" : null;
  const ageMs = healthAgeMs ?? (updatedAt ? Date.now() - updatedAt : null);
  const isStale = ageMs !== null && ageMs > STALE_THRESHOLD_MS;
  const isReconnecting =
    ageMs !== null && ageMs > RECONNECTING_THRESHOLD_MS && !isStale;
  const hasFirstFrame = updatedAt !== null;

  // Force a "now" tick once a second so the "X seconds ago" label
  // actually changes between health refreshes.
  const [, forceTick] = useState(0);
  useEffect(() => {
    const t = window.setInterval(() => forceTick((x) => x + 1), 1000);
    return () => window.clearInterval(t);
  }, []);

  const status = computeStatus(
    camera,
    health,
    streamUrl,
    isStale,
    error,
    hasFirstFrame,
  );

  return (
    <div className="overflow-hidden rounded-lg border bg-card shadow-sm">
      {/* Video panel */}
      <div className="relative aspect-video w-full bg-black">
        {streamUrl ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            ref={imgRef}
            // `key` ties the DOM <img> identity to the mount epoch so
            // a reconnect actually unmounts the old element instead of
            // just swapping its src — that's what cleanly drops the
            // prior MJPEG connection and lets the new one start fresh.
            key={mountEpoch}
            src={streamUrl}
            alt={`${camera.name} preview`}
            className={cn(
              "h-full w-full object-contain transition-opacity",
              isStale && "opacity-50",
            )}
            onLoad={() => {
              // For MJPEG, onLoad fires after the FIRST part has been
              // received (i.e. once we've painted real pixels). It
              // does not fire on every frame — that's expected.
              setUpdatedAt(Date.now());
              setImgError(false);
            }}
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-white/70">
            {!camera.is_active ? (
              <div className="flex flex-col items-center gap-2 text-sm">
                <PowerOff className="h-8 w-8" />
                <span>Camera disabled</span>
              </div>
            ) : !tabVisible ? (
              <div className="flex flex-col items-center gap-2 text-sm">
                <PowerOff className="h-8 w-8" />
                <span>Paused (tab hidden)</span>
              </div>
            ) : error ? (
              <div className="flex max-w-[80%] flex-col items-center gap-2 text-center text-sm">
                <AlertTriangle className="h-8 w-8 text-amber-400" />
                <span className="text-amber-200">{error}</span>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 text-sm">
                <Loader2 className="h-8 w-8 animate-spin" />
                <span>Connecting…</span>
              </div>
            )}
          </div>
        )}

        {/* Top-left: camera type */}
        <Badge
          variant={camera.camera_type === "ENTRY" ? "default" : "secondary"}
          className="absolute left-2 top-2"
        >
          {camera.camera_type}
        </Badge>

        {/* Top-right: live status */}
        <Badge variant={status.variant} className="absolute right-2 top-2 gap-1">
          {status.iconLeft}
          {status.label}
        </Badge>

        {/* Reconnecting overlay — shows within 1.2 s of a real
            upstream stall so a brief network glitch doesn't look like
            a frozen tile. */}
        {isReconnecting && streamUrl && (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-black/30 backdrop-blur-[1px]">
            <div className="flex items-center gap-2 rounded-md bg-black/60 px-3 py-1.5 text-xs font-medium text-white">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Reconnecting…
            </div>
          </div>
        )}

        {/* Stalled banner — only after STALE_THRESHOLD_MS (10 s) of
            no fresh frames; this is "the camera is genuinely down". */}
        {isStale && streamUrl && (
          <div className="pointer-events-none absolute inset-x-0 bottom-0 flex items-center gap-1 bg-amber-500/85 px-3 py-1 text-xs font-medium text-white">
            <AlertTriangle className="h-3.5 w-3.5" />
            Stream stalled — last frame {(ageMs! / 1000).toFixed(1)}s ago
          </div>
        )}
      </div>

      {/* Footer with details + actions */}
      <div className="space-y-2 p-3">
        <div className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <CameraIcon className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              <span className="truncate text-sm font-medium">
                {camera.name}
              </span>
            </div>
            {camera.location && (
              <p className="truncate text-xs text-muted-foreground">
                {camera.location}
              </p>
            )}
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0"
              title="Reconnect stream"
              onClick={reconnect}
              disabled={!camera.is_active}
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0"
              title="Restart worker"
              onClick={() => restart.mutate(camera.id)}
              disabled={!camera.is_active || restart.isPending}
            >
              {restart.isPending && restart.variables === camera.id ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <RefreshCw className="h-3.5 w-3.5" />
              )}
            </Button>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground tabular-nums">
          <span className="inline-flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {ageMs === null
              ? "—"
              : ageMs < 1000
                ? "just now"
                : `${(ageMs / 1000).toFixed(1)}s ago`}
          </span>
          {health?.last_error && (
            <span
              className="truncate text-destructive"
              title={health.last_error}
            >
              {health.last_error}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function computeStatus(
  camera: Camera,
  health: CameraHealth | undefined,
  url: string | null,
  isStale: boolean,
  error: string | null,
  hasFirstFrame: boolean,
): {
  variant:
    | "default"
    | "secondary"
    | "destructive"
    | "outline"
    | "success"
    | "warning";
  label: string;
  iconLeft: React.ReactNode;
} {
  if (!camera.is_active) {
    return {
      variant: "secondary",
      label: "Disabled",
      iconLeft: <PowerOff className="h-3 w-3" />,
    };
  }
  if (health?.last_error) {
    return {
      variant: "destructive",
      label: "Error",
      iconLeft: <AlertTriangle className="h-3 w-3" />,
    };
  }
  if (health && !health.is_running) {
    return {
      variant: "warning",
      label: "Stopped",
      iconLeft: <AlertTriangle className="h-3 w-3" />,
    };
  }
  if (isStale) {
    return {
      variant: "warning",
      label: "Stale",
      iconLeft: <AlertTriangle className="h-3 w-3" />,
    };
  }
  if (url && hasFirstFrame) {
    return {
      variant: "success",
      label: "Live",
      iconLeft: <Activity className="h-3 w-3 animate-pulse" />,
    };
  }
  if (error) {
    return {
      variant: "warning",
      label: "Reconnecting",
      iconLeft: <Loader2 className="h-3 w-3 animate-spin" />,
    };
  }
  return {
    variant: "outline",
    label: "Connecting",
    iconLeft: <Loader2 className="h-3 w-3 animate-spin" />,
  };
}
