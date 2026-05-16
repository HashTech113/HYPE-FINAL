import { createFileRoute, Link } from "@tanstack/react-router";
import { type RefObject, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  AlertCircle,
  Expand,
  MapPin,
  Minimize,
  PauseCircle,
  RefreshCw,
  UserX,
  Video,
  VideoOff,
} from "lucide-react";
import { SectionShell } from "@/components/dashboard/SectionShell";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  buildCameraStreamUrl,
  getCameraDetections,
  getCameraStreamToken,
  type Camera,
  type CameraHealth,
  type LiveDetection,
} from "@/api/dashboardApi";
import { useCameras, useCamerasHealth } from "@/hooks/use-cameras";

// Admin-only guard lives on the parent layout (_dashboard.cameras.tsx).
export const Route = createFileRoute("/_dashboard/cameras/live")({
  component: LiveCamerasPage,
});

// "Live" means a frame was decoded within this window. The worker keeps
// heart-beating its loop even while RTSP fails silently, so frame-age is
// the only honest signal of stream liveness.
const LIVE_FRAME_AGE_MAX_SECONDS = 15;

function isLive(h: CameraHealth | undefined): boolean {
  if (!h) return false;
  if (!h.is_running) return false;
  if (h.last_error) return false;
  return h.last_frame_age_seconds !== null && h.last_frame_age_seconds < LIVE_FRAME_AGE_MAX_SECONDS;
}

// True when this browser tab is foregrounded. Drives both the MJPEG
// <img> mount and the per-tile detection poll: backgrounded tabs have
// no business holding open multipart streams or pinging the API every
// 1.5 s. Belt-and-braces: setInterval is throttled to ≥1 Hz in hidden
// tabs anyway, but unmounting the <img> is what actually closes the
// streaming socket.
function usePageVisible(): boolean {
  const [visible, setVisible] = useState<boolean>(() =>
    typeof document === "undefined" ? true : !document.hidden,
  );
  useEffect(() => {
    if (typeof document === "undefined") return;
    const onChange = () => setVisible(!document.hidden);
    document.addEventListener("visibilitychange", onChange);
    return () => document.removeEventListener("visibilitychange", onChange);
  }, []);
  return visible;
}

// True when the tile is intersecting the viewport (with a small
// rootMargin so we pre-warm streams just before they scroll into view
// — avoids a black flash for normal scroll velocity). When false we
// unmount the <img> so the browser closes the MJPEG connection,
// stopping bandwidth + JPEG decode for the tile entirely.
function useInViewport<T extends Element>(ref: RefObject<T | null>): boolean {
  const [inView, setInView] = useState<boolean>(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") {
      // No IO support — fall back to "always visible" so streams still
      // work; we lose the optimization but not correctness.
      setInView(true);
      return;
    }
    const obs = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) setInView(entry.isIntersecting);
      },
      { threshold: 0.01, rootMargin: "120px" },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [ref]);
  return inView;
}

function LiveCamerasPage() {
  const camerasQ = useCameras();
  const healthQ = useCamerasHealth(5_000);

  const cameras = camerasQ.data ?? [];
  const health = healthQ.data ?? [];

  const healthById = useMemo(() => {
    const m = new Map<string, CameraHealth>();
    for (const h of health) m.set(h.id, h);
    return m;
  }, [health]);

  // Show every configured camera — offline ones render an Offline tile
  // variant rather than disappearing, so the operator can see at a glance
  // which feeds are down and isn't surprised by a half-empty grid after a
  // network blip.
  const tiles = cameras;

  const connectedTiles = useMemo(
    () => cameras.filter((c) => c.connection_status === "connected"),
    [cameras],
  );

  const liveCount = useMemo(
    () => connectedTiles.filter((c) => isLive(healthById.get(c.id))).length,
    [connectedTiles, healthById],
  );

  const loading = camerasQ.isLoading;
  const error = camerasQ.error;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <SectionShell
        title="Live Cameras"
        icon={<Video className="h-5 w-5 text-primary" />}
        className="animate-fade-in-up"
        actions={
          // Inline legend + live count. Replaces the previous full-width
          // legend strip below the header — the colour swatches alone tell
          // the operator everything they need (green = recognised, red =
          // unknown); the verbose "name · match %" / heartbeat callouts
          // were redundant noise.
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs sm:gap-x-4">
            <span className="font-medium uppercase tracking-wide text-slate-500">
              Legend
            </span>
            <span className="inline-flex items-center gap-1.5 text-slate-700">
              <span className="inline-block h-2.5 w-3 rounded-sm bg-emerald-500" />
              Recognized employee
            </span>
            <span className="inline-flex items-center gap-1.5 text-slate-700">
              <span className="inline-block h-2.5 w-3 rounded-sm bg-rose-500" />
              Unknown face
            </span>
            <span className="hidden items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-sm sm:inline-flex">
              <Activity className="h-4 w-4 text-emerald-500" />
              <span className="tabular-nums">
                <span className="font-medium text-slate-900">{liveCount}</span>
                <span className="text-slate-500">/{tiles.length} live</span>
              </span>
            </span>
            <Button
              type="button"
              variant="outline"
              onClick={() => { void camerasQ.refetch(); void healthQ.refetch(); }}
              disabled={camerasQ.isFetching}
              className="h-9 gap-2 rounded-xl"
            >
              <RefreshCw className={cn("h-4 w-4", camerasQ.isFetching && "animate-spin")} />
              Refresh
            </Button>
          </div>
        }
      >
        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto p-6">
          {error ? (
            <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error instanceof Error ? error.message : "Failed to load cameras."}
            </div>
          ) : null}

          {loading && cameras.length === 0 ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-2">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="aspect-video animate-pulse rounded-2xl bg-slate-100" />
              ))}
            </div>
          ) : tiles.length === 0 ? (
            <EmptyState totalCameras={cameras.length} />
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {tiles.map((cam) =>
                cam.connection_status === "connected" ? (
                  <CameraTile key={cam.id} camera={cam} health={healthById.get(cam.id)} />
                ) : (
                  <OfflineTile key={cam.id} camera={cam} />
                ),
              )}
            </div>
          )}
        </div>
      </SectionShell>
    </div>
  );
}

function EmptyState({ totalCameras: _totalCameras }: { totalCameras: number }) {
  // Reached only when zero cameras are configured — every other camera
  // state (failed, unknown) renders an OfflineTile in the grid instead.
  return (
    <div className="mt-8 flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 px-6 py-14 text-center">
      <VideoOff className="h-10 w-10 text-slate-400" />
      <div className="text-sm font-medium text-slate-700">
        Add a camera to view the live feed
      </div>
      <Link
        to="/cameras"
        className="mt-2 inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-[#4aa590] to-[#2f8f7b] px-4 py-2 text-xs font-semibold text-white"
      >
        Add Camera
      </Link>
    </div>
  );
}

function CameraTypeBadge({ type }: { type: Camera["type"] }) {
  const isEntry = type === "ENTRY";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold",
        isEntry ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700",
      )}
      title={isEntry ? "Attendance · Person Entry" : "Attendance · Person Exit"}
    >
      {isEntry ? "Person Entry" : "Person Exit"}
    </span>
  );
}

function OfflineTile({ camera }: { camera: Camera }) {
  // Rendered for cameras whose ``connection_status`` is not ``connected``
  // — they keep their grid slot so the operator can see at a glance which
  // feeds are down. The "Re-check" action lives on the Cameras table; we
  // don't duplicate it here to keep this tile focused on visibility.
  const reason =
    camera.last_check_message?.trim() ||
    (camera.connection_status === "failed"
      ? "Last connection check failed"
      : "Connection not yet verified");
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="relative aspect-video w-full bg-slate-100">
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-center text-slate-500">
          <VideoOff className="h-9 w-9" />
          <div className="text-sm font-medium text-slate-700">Offline</div>
          <div className="max-w-[80%] text-[11px] leading-tight">{reason}</div>
        </div>
      </div>
      <div className="flex items-center justify-between gap-3 px-4 py-3">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <div className="truncate text-sm font-semibold text-slate-900">{camera.name}</div>
            <CameraTypeBadge type={camera.type} />
          </div>
          {camera.location ? (
            <div className="mt-0.5 flex items-center gap-1 text-xs text-slate-500">
              <MapPin className="h-3 w-3" />
              <span className="truncate">{camera.location}</span>
            </div>
          ) : null}
        </div>
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium",
            camera.connection_status === "failed"
              ? "bg-rose-50 text-rose-700"
              : "bg-slate-100 text-slate-600",
          )}
          title={reason}
        >
          {camera.connection_status === "failed" ? (
            <>
              <AlertCircle className="h-3 w-3" />
              Offline
            </>
          ) : (
            "Unknown"
          )}
        </span>
      </div>
    </div>
  );
}

const STREAM_TOKEN_REFRESH_MS = 4 * 60 * 1000; // refresh ~1 min before 5-min expiry
const DETECTIONS_POLL_MS = 1500;

function CameraTile({ camera, health }: { camera: Camera; health: CameraHealth | undefined }) {
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [imgFailed, setImgFailed] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [detections, setDetections] = useState<LiveDetection[]>([]);
  const [detectionsStale, setDetectionsStale] = useState(false);
  // Heartbeat dot — flips ON briefly each time a fresh inference pass lands.
  const [pulse, setPulse] = useState(false);
  const lastCapturedAtRef = useRef<number | null>(null);
  const pulseTimerRef = useRef<number | null>(null);
  const refreshRef = useRef<number | null>(null);
  const tileRef = useRef<HTMLDivElement | null>(null);
  // Combined visibility gate: stream + detection-poll only run when the
  // tab is foregrounded AND the tile itself is in (or near) the
  // viewport. Off-screen tiles in a long grid stop pulling MJPEG
  // bytes and stop hitting /detections every 1.5s.
  const pageVisible = usePageVisible();
  const tileInView = useInViewport(tileRef);
  const active = pageVisible && tileInView;

  useEffect(() => {
    let cancelled = false;
    const fetchToken = async () => {
      try {
        const { token } = await getCameraStreamToken(camera.id);
        if (cancelled) return;
        setStreamUrl(buildCameraStreamUrl(camera.id, token));
        setStreamError(null);
        setImgFailed(false);
      } catch (err) {
        if (cancelled) return;
        setStreamError(err instanceof Error ? err.message : "Could not authorize stream.");
      }
    };
    void fetchToken();
    refreshRef.current = window.setInterval(() => void fetchToken(), STREAM_TOKEN_REFRESH_MS);
    return () => {
      cancelled = true;
      if (refreshRef.current !== null) {
        window.clearInterval(refreshRef.current);
        refreshRef.current = null;
      }
    };
  }, [camera.id]);

  useEffect(() => {
    const onFullscreenChange = () => {
      setIsFullscreen(document.fullscreenElement === tileRef.current);
    };
    document.addEventListener("fullscreenchange", onFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", onFullscreenChange);
  }, []);

  // When the tile re-activates (scrolled back into view, or tab
  // re-foregrounded), clear any sticky <img> error so the remount has
  // a clean shot at the stream. Without this, an earlier transient
  // network blip would keep the "Stream unavailable" placeholder up
  // even after the conditions that caused it have cleared.
  useEffect(() => {
    if (active) setImgFailed(false);
  }, [active]);

  useEffect(() => {
    // Skip the entire interval setup when the tile is not active —
    // off-screen tiles + hidden tabs don't need to ping /detections at
    // all. The effect re-runs on activation change so polling resumes
    // immediately when the tile scrolls back into view (or the tab is
    // re-foregrounded).
    if (!active) return;
    let cancelled = false;
    const tick = async () => {
      try {
        const out = await getCameraDetections(camera.id);
        if (cancelled) return;
        setDetections(out.detections);
        const stale = out.age_seconds !== null && out.age_seconds > 5;
        setDetectionsStale(stale);
        if (
          out.captured_at !== null &&
          out.captured_at !== lastCapturedAtRef.current &&
          !stale
        ) {
          lastCapturedAtRef.current = out.captured_at;
          setPulse(true);
          if (pulseTimerRef.current !== null) window.clearTimeout(pulseTimerRef.current);
          pulseTimerRef.current = window.setTimeout(() => {
            setPulse(false);
            pulseTimerRef.current = null;
          }, 120);
        } else if (stale) {
          if (pulseTimerRef.current !== null) {
            window.clearTimeout(pulseTimerRef.current);
            pulseTimerRef.current = null;
          }
          setPulse(false);
        }
      } catch {
        if (cancelled) return;
        setDetections([]);
        setDetectionsStale(true);
      }
    };
    void tick();
    const handle = window.setInterval(() => void tick(), DETECTIONS_POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(handle);
      if (pulseTimerRef.current !== null) {
        window.clearTimeout(pulseTimerRef.current);
        pulseTimerRef.current = null;
      }
    };
  }, [camera.id, active]);

  const toggleFullscreen = async () => {
    const tile = tileRef.current;
    if (!tile) return;
    try {
      if (document.fullscreenElement === tile) await document.exitFullscreen();
      else await tile.requestFullscreen();
    } catch {
      /* fullscreen rejected — usually because not a user gesture */
    }
  };

  const live = isLive(health);
  const frameAge = health?.last_frame_age_seconds;

  return (
    <div
      ref={tileRef}
      className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
    >
      <div className="relative aspect-video w-full bg-slate-900">
        {streamError ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-xs text-rose-200">
            <VideoOff className="h-8 w-8" />
            {streamError}
          </div>
        ) : !active ? (
          // Tile is off-screen or the tab is hidden — unmount the <img>
          // so the browser tears down the MJPEG socket. The placeholder
          // keeps the layout stable; the stream resumes on activation.
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-1.5 text-[11px] text-slate-400">
            <PauseCircle className="h-7 w-7" />
            <span>{pageVisible ? "Paused — off-screen" : "Paused — tab hidden"}</span>
          </div>
        ) : streamUrl && !imgFailed ? (
          <img
            src={streamUrl}
            alt={`${camera.name} live feed`}
            className="h-full w-full object-cover"
            onError={() => setImgFailed(true)}
          />
        ) : imgFailed ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-xs text-slate-300">
            <VideoOff className="h-8 w-8" />
            Stream unavailable
          </div>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-xs text-slate-300">
            Connecting…
          </div>
        )}
      </div>
      <div className="flex items-center justify-between gap-3 px-4 py-3">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <div className="truncate text-sm font-semibold text-slate-900">{camera.name}</div>
            <CameraTypeBadge type={camera.type} />
          </div>
          {camera.location ? (
            <div className="mt-0.5 flex items-center gap-1 text-xs text-slate-500">
              <MapPin className="h-3 w-3" />
              <span className="truncate">{camera.location}</span>
            </div>
          ) : null}
        </div>
        <div className="inline-flex items-center gap-1.5">
          {live ? (
            <span
              className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700"
              title={`Frame age ${frameAge?.toFixed(1) ?? "?"}s · ${health?.processed_frames ?? 0} processed`}
            >
              <span
                aria-hidden="true"
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  pulse ? "bg-amber-400" : "bg-transparent",
                )}
              />
              Live
            </span>
          ) : health?.last_error ? (
            <span
              className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-[11px] font-medium text-rose-700"
              title={health.last_error}
            >
              <AlertCircle className="h-3 w-3" />
              Error
            </span>
          ) : health?.is_running ? (
            <span
              className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-700"
              title={frameAge !== null && frameAge !== undefined ? `Last frame ${frameAge.toFixed(1)}s ago` : "No frame yet"}
            >
              Stalled
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
              Idle
            </span>
          )}
          <Button
            type="button"
            variant="outline"
            size="icon"
            onClick={() => void toggleFullscreen()}
            className="h-6 w-6 rounded-full border-slate-200 text-slate-600"
            title={isFullscreen ? "Exit fullscreen" : "View fullscreen"}
            aria-label={isFullscreen ? "Exit fullscreen" : "View fullscreen"}
          >
            {isFullscreen ? <Minimize className="h-3.5 w-3.5" /> : <Expand className="h-3.5 w-3.5" />}
          </Button>
        </div>
      </div>
      <DetectionsStrip detections={detections} stale={detectionsStale} />
    </div>
  );
}

function DetectionsStrip({
  detections, stale,
}: { detections: LiveDetection[]; stale: boolean }) {
  if (detections.length === 0) {
    return (
      <div className="border-t border-slate-100 px-4 py-2 text-[11px] text-slate-400">
        Waiting for first recognition…
      </div>
    );
  }
  return (
    <div className="flex flex-wrap items-center gap-1.5 border-t border-slate-100 px-4 py-2">
      {detections.slice(0, 6).map((d, i) => (
        <DetectionChip key={`${d.employee_id ?? "u"}-${i}`} detection={d} />
      ))}
      {stale ? (
        <span className="text-[10px] text-slate-400" title="Detection data older than 5s">
          stale
        </span>
      ) : null}
    </div>
  );
}

function DetectionChip({ detection }: { detection: LiveDetection }) {
  const pct = Math.round(Math.max(0, Math.min(1, detection.score)) * 100);
  if (detection.matched) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
        {detection.name} · {pct}%
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-[11px] font-medium text-rose-700">
      <UserX className="h-3 w-3" />
      Unknown · {pct}%
    </span>
  );
}
