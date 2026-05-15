import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import {
  AlertCircle,
  Camera as CameraIcon,
  CheckCircle2,
  Eye,
  EyeOff,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  Sparkles,
  TestTube2,
  Trash2,
  XCircle,
} from "lucide-react";
import { SectionShell } from "@/components/dashboard/SectionShell";
import { Button } from "@/components/ui/button";
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
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type {
  Camera,
  CameraBrand,
  CameraConnectionStatus,
  CameraCreatePayload,
  CameraHealth,
  CameraSmartProbeResponse,
  CameraType,
} from "@/api/dashboardApi";
import {
  useCameras,
  useCamerasHealth,
  useCreateCamera,
  useDeleteCamera,
  useRecheckCamera,
  useSmartProbeCamera,
  useTestCameraConnection,
  useUpdateCamera,
} from "@/hooks/use-cameras";

// Admin-only guard lives on the parent layout (_dashboard.cameras.tsx).
export const Route = createFileRoute("/_dashboard/cameras/")({
  component: CamerasPage,
});

const DEFAULT_RTSP_PATH = "/Streaming/Channels/101";
const DEFAULT_PORT = 554;

// Per-brand default RTSP path. The Smart Connect tab now also runs a
// multi-template probe on the backend — this map seeds the form so the
// auto-built URL preview reflects the brand the operator picked. The
// backend will try other templates on top during the probe.
const BRAND_LABELS: Record<CameraBrand, string> = {
  hikvision: "Hikvision",
  cp_plus: "CP Plus",
  dahua: "Dahua",
  axis: "Axis",
  generic: "Generic / Other",
};

const BRAND_DEFAULT_PATHS: Record<CameraBrand, string> = {
  hikvision: "/Streaming/Channels/101",
  cp_plus: "/cam/realmonitor?channel=1&subtype=0",
  dahua: "/cam/realmonitor?channel=1&subtype=0",
  axis: "/axis-media/media.amp",
  generic: "/Streaming/Channels/101",
};

function inferBrandFromRtspPath(rtspPath: string): CameraBrand {
  const p = (rtspPath || "").toLowerCase();
  if (p.includes("realmonitor")) return "cp_plus";
  if (p.includes("streaming/channels")) return "hikvision";
  if (p.includes("axis-media")) return "axis";
  return "hikvision";
}

/** Parse a user-supplied RTSP URL into the parts the backend stores.
 *
 * Hand-rolled (no regex) because RTSP credentials commonly contain ``@``
 * or ``:`` (e.g. ``Admin@123``), and a greedy regex split would pick the
 * wrong delimiter and produce a corrupted host. We split on the LAST
 * ``@`` (credentials/host boundary) and the FIRST ``:`` in the credential
 * part (username/password boundary). */
type ParsedRtsp = {
  username: string;
  password: string;
  ip: string;
  port: number;
  rtsp_path: string;
};
function parseRtspUrl(raw: string): { ok: true; parts: ParsedRtsp } | { ok: false; reason: string } {
  const trimmed = raw.trim();
  if (!trimmed) return { ok: false, reason: "RTSP URL is required." };
  const SCHEME = "rtsp://";
  if (!trimmed.toLowerCase().startsWith(SCHEME)) {
    return { ok: false, reason: "URL must start with rtsp://" };
  }
  const afterScheme = trimmed.slice(SCHEME.length);
  const atIdx = afterScheme.lastIndexOf("@");
  if (atIdx === -1) return { ok: false, reason: "RTSP URL must include user:password@ before the host." };
  const credPart = afterScheme.slice(0, atIdx);
  const hostPart = afterScheme.slice(atIdx + 1);
  const colonIdx = credPart.indexOf(":");
  if (colonIdx === -1) return { ok: false, reason: "Credentials must look like user:password before '@'." };
  let username: string;
  let password: string;
  try {
    username = decodeURIComponent(credPart.slice(0, colonIdx));
    password = decodeURIComponent(credPart.slice(colonIdx + 1));
  } catch {
    return { ok: false, reason: "Could not decode credentials — check for stray %XX sequences." };
  }
  if (!username || !password) return { ok: false, reason: "Both username and password are required before '@'." };
  let hostPortPart = hostPart;
  let path = "/";
  const slashIdx = hostPart.indexOf("/");
  if (slashIdx !== -1) {
    hostPortPart = hostPart.slice(0, slashIdx);
    path = hostPart.slice(slashIdx);
  }
  let ip = hostPortPart;
  let port: number = DEFAULT_PORT;
  const colonInHost = hostPortPart.lastIndexOf(":");
  if (colonInHost !== -1) {
    ip = hostPortPart.slice(0, colonInHost);
    const portStr = hostPortPart.slice(colonInHost + 1);
    const parsedPort = Number.parseInt(portStr, 10);
    if (!Number.isFinite(parsedPort) || parsedPort < 1 || parsedPort > 65535) {
      return { ok: false, reason: "Port must be between 1 and 65535." };
    }
    port = parsedPort;
  }
  if (!ip) return { ok: false, reason: "Host / IP is missing in the URL." };
  return { ok: true, parts: { username, password, ip, port, rtsp_path: path } };
}

function buildRtspUrlDisplay({
  username, ip, port, rtsp_path,
}: { username: string; ip: string; port: string; rtsp_path: string }): string {
  const path = rtsp_path.startsWith("/") ? rtsp_path : `/${rtsp_path}`;
  const _port = port || String(DEFAULT_PORT);
  const _user = username || "user";
  const _host = ip || "ip";
  return `rtsp://${_user}:****@${_host}:${_port}${path}`;
}

// ============================================================================
// Page
// ============================================================================

function CamerasPage() {
  const camerasQ = useCameras();
  const healthQ = useCamerasHealth(5_000);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Camera | null>(null);
  const [viewing, setViewing] = useState<Camera | null>(null);
  const [toDelete, setToDelete] = useState<Camera | null>(null);

  const recheck = useRecheckCamera();
  const remove = useDeleteCamera();

  const cameras = camerasQ.data ?? [];
  const health = healthQ.data ?? [];
  const healthById = useMemo(() => {
    const m = new Map<string, CameraHealth>();
    for (const h of health) m.set(h.id, h);
    return m;
  }, [health]);

  // "Live" means the worker thread has actually seen a frame in the last
  // 15s — the worker keeps heartbeating even while RTSP fails silently,
  // so frame-age is the only honest signal.
  const summary = useMemo(() => {
    const total = cameras.length;
    const connected = cameras.filter((c) => c.connection_status === "connected").length;
    const live = health.filter(
      (h) => h.is_running && !h.last_error
        && h.last_frame_age_seconds !== null && h.last_frame_age_seconds < 15,
    ).length;
    const entry = cameras.filter((c) => c.type === "ENTRY").length;
    const exit = cameras.filter((c) => c.type === "EXIT").length;
    return { total, connected, live, entry, exit };
  }, [cameras, health]);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <SectionShell
        title="Add Camera"
        icon={<CameraIcon className="h-5 w-5 text-primary" />}
        className="animate-fade-in-up"
        actions={
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => void camerasQ.refetch()}
              className="h-9 gap-2 rounded-xl"
              disabled={camerasQ.isFetching}
            >
              <RefreshCw className={cn("h-4 w-4", camerasQ.isFetching && "animate-spin")} />
              Refresh
            </Button>
            <Button
              type="button"
              onClick={() => { setEditing(null); setFormOpen(true); }}
              className="h-9 gap-2 rounded-xl bg-gradient-to-r from-[#4aa590] to-[#2f8f7b] text-white hover:from-[#3f9382] hover:to-[#256f60]"
            >
              <Plus className="h-4 w-4" />
              Add Camera
            </Button>
          </div>
        }
      >
        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto p-6">
          {camerasQ.error ? (
            <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {camerasQ.error instanceof Error ? camerasQ.error.message : "Failed to load cameras."}
            </div>
          ) : null}

          {/* Summary stats — mirrors the Super_Admin reference layout. The
              "Live workers" tile turns warning-orange when some cameras
              should be live but aren't, drawing attention without making
              the whole page noisy. */}
          <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <SummaryStat label="Total" value={summary.total} />
            <SummaryStat label="Connected" value={`${summary.connected}/${summary.total}`} />
            <SummaryStat
              label="Live workers"
              value={summary.live}
              tone={summary.connected > 0 && summary.live < summary.connected ? "warning" : "success"}
            />
            <SummaryStat label="Person Entry / Exit" value={`${summary.entry} / ${summary.exit}`} />
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>IP / Port</TableHead>
                  <TableHead>Use Case</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Worker</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {camerasQ.isLoading && cameras.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="py-10 text-center text-sm text-slate-500">
                      Loading cameras…
                    </TableCell>
                  </TableRow>
                ) : cameras.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="py-10 text-center text-sm text-slate-500">
                      No cameras yet. Click <span className="font-medium">Add Camera</span> to get started.
                    </TableCell>
                  </TableRow>
                ) : (
                  cameras.map((cam) => (
                    <TableRow key={cam.id}>
                      <TableCell className="font-medium text-slate-900">
                        <span className="inline-flex flex-wrap items-center gap-1.5">
                          {cam.name}
                          {cam.auto_discovery_enabled ? (
                            <span
                              className="inline-flex items-center rounded-full bg-sky-50 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-sky-700"
                              title="Auto-discovery on"
                            >
                              Auto-discover
                            </span>
                          ) : null}
                        </span>
                      </TableCell>
                      <TableCell className="text-slate-600">{cam.location || "—"}</TableCell>
                      <TableCell className="text-slate-600">
                        <div>{cam.ip}:{cam.port}</div>
                        {cam.last_known_ip && cam.last_known_ip !== cam.ip ? (
                          <div className="text-[10px] text-slate-400">was {cam.last_known_ip}</div>
                        ) : null}
                      </TableCell>
                      <TableCell><UseCaseBadge type={cam.type} enableFaceIngest={cam.enable_face_ingest} /></TableCell>
                      <TableCell><StatusBadge status={cam.connection_status} /></TableCell>
                      <TableCell><WorkerCell health={healthById.get(cam.id)} /></TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end gap-1">
                          <Button type="button" variant="ghost" size="sm" onClick={() => setViewing(cam)} title="View details">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            type="button" variant="ghost" size="sm"
                            onClick={() => recheck.mutate(cam.id, {
                              onSuccess: (r) => r.ok ? toast.success(`Re-check OK (${r.latency_ms} ms)`) : toast.error(r.message),
                              onError: (e) => toast.error(e instanceof Error ? e.message : "Re-check failed"),
                            })}
                            title="Re-check connection"
                            disabled={recheck.isPending && recheck.variables === cam.id}
                          >
                            <RefreshCw className={cn("h-4 w-4", recheck.isPending && recheck.variables === cam.id && "animate-spin")} />
                          </Button>
                          <Button type="button" variant="ghost" size="sm" onClick={() => { setEditing(cam); setFormOpen(true); }} title="Edit">
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            type="button" variant="ghost" size="sm"
                            onClick={() => setToDelete(cam)} title="Delete"
                            className="text-rose-600 hover:bg-rose-50 hover:text-rose-700"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </SectionShell>

      <CameraFormDialog
        open={formOpen}
        camera={editing}
        onOpenChange={(open) => { setFormOpen(open); if (!open) setEditing(null); }}
      />

      <CameraDetailsDialog
        camera={viewing}
        onOpenChange={(open) => !open && setViewing(null)}
      />

      <AlertDialog open={!!toDelete} onOpenChange={(open) => !open && setToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this camera?</AlertDialogTitle>
            <AlertDialogDescription>
              This removes <span className="font-medium">{toDelete?.name}</span> from the dashboard.
              The camera itself isn't affected.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-rose-600 text-white hover:bg-rose-700"
              onClick={() => {
                if (!toDelete) return;
                remove.mutate(toDelete.id, {
                  onSuccess: () => { toast.success(`Removed ${toDelete.name}`); setToDelete(null); },
                  onError: (e) => toast.error(e instanceof Error ? e.message : "Delete failed"),
                });
              }}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// ============================================================================
// Stat tiles + small badges
// ============================================================================

function SummaryStat({
  label, value, tone,
}: { label: string; value: string | number; tone?: "warning" | "success" }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums text-slate-900">{value}</p>
      {tone ? (
        <span className={cn(
          "mt-2 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium",
          tone === "success" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700",
        )}>
          {tone === "success" ? "All healthy" : "Some down"}
        </span>
      ) : null}
    </div>
  );
}

function UseCaseBadge({ type, enableFaceIngest }: { type: CameraType; enableFaceIngest: boolean }) {
  if (!enableFaceIngest) {
    return (
      <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
        Live View
      </span>
    );
  }
  const isEntry = type === "ENTRY";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium",
        isEntry ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700",
      )}
      title={isEntry ? "Attendance · Person Entry" : "Attendance · Person Exit"}
    >
      {isEntry ? "Person Entry" : "Person Exit"}
    </span>
  );
}

function StatusBadge({ status }: { status: CameraConnectionStatus }) {
  if (status === "connected") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
        <CheckCircle2 className="h-3.5 w-3.5" /> Connected
      </span>
    );
  }
  if (status === "failed") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-1 text-xs font-medium text-rose-700">
        <XCircle className="h-3.5 w-3.5" /> Failed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
      Unknown
    </span>
  );
}

function WorkerCell({ health }: { health: CameraHealth | undefined }) {
  if (!health) {
    return <span className="text-xs text-slate-400">—</span>;
  }
  if (!health.is_running) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-600">
        Idle
      </span>
    );
  }
  const age = health.last_frame_age_seconds;
  if (age !== null && age < 15) {
    return (
      <span
        className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700"
        title={`Last frame ${age.toFixed(1)}s ago · ${health.processed_frames} frames`}
      >
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
        Live · {age.toFixed(1)}s
      </span>
    );
  }
  if (health.last_error) {
    return (
      <span
        className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-[11px] font-medium text-rose-700"
        title={health.last_error}
      >
        <AlertCircle className="h-3 w-3" />
        Error
      </span>
    );
  }
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-700"
      title={age !== null ? `Last frame ${age.toFixed(1)}s ago` : "No frame yet"}
    >
      Stalled
    </span>
  );
}

// ============================================================================
// Details dialog
// ============================================================================

function CameraDetailsDialog({
  camera, onOpenChange,
}: { camera: Camera | null; onOpenChange: (open: boolean) => void }) {
  return (
    <Dialog open={!!camera} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md rounded-2xl">
        <DialogHeader>
          <DialogTitle>Camera details</DialogTitle>
          <DialogDescription>
            Read-only view of the saved camera configuration and most recent connection check.
          </DialogDescription>
        </DialogHeader>
        {camera ? (
          <dl className="grid grid-cols-[7rem_1fr] gap-x-3 gap-y-2 text-sm">
            <dt className="text-slate-500">Name</dt>
            <dd className="font-medium text-slate-900">{camera.name}</dd>
            <dt className="text-slate-500">Location</dt>
            <dd className="text-slate-900">{camera.location || "—"}</dd>
            <dt className="text-slate-500">IP</dt>
            <dd className="text-slate-900">{camera.ip}</dd>
            <dt className="text-slate-500">Port</dt>
            <dd className="text-slate-900">{camera.port}</dd>
            <dt className="text-slate-500">Username</dt>
            <dd className="text-slate-900">{camera.username || "—"}</dd>
            <dt className="text-slate-500">Password</dt>
            <dd className="text-slate-400">••••••••</dd>
            <dt className="text-slate-500">RTSP path</dt>
            <dd className="break-all font-mono text-xs text-slate-700">{camera.rtsp_path}</dd>
            <dt className="text-slate-500">RTSP URL</dt>
            <dd className="break-all font-mono text-xs text-slate-700">{camera.rtsp_url_preview}</dd>
            <dt className="text-slate-500">Status</dt>
            <dd><StatusBadge status={camera.connection_status} /></dd>
            {camera.last_check_message ? (
              <>
                <dt className="text-slate-500">Last check</dt>
                <dd className="text-xs text-slate-600">{camera.last_check_message}</dd>
              </>
            ) : null}
            <dt className="text-slate-500">Face ingest</dt>
            <dd className="text-xs text-slate-700">
              {camera.enable_face_ingest ? "Enabled" : "Disabled (live view only)"}
            </dd>
          </dl>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// Form dialog (RHF + zod)
// ============================================================================

const BRAND_VALUES = ["hikvision", "cp_plus", "dahua", "axis", "generic"] as const;

const smartSchema = z.object({
  name: z.string().trim().min(1, "Camera name is required").max(128),
  location: z.string().trim().min(1, "Location is required").max(256),
  brand: z.enum(BRAND_VALUES),
  type: z.enum(["ENTRY", "EXIT"]),
  ip: z.string().trim().min(1, "Camera IP is required").max(64),
  // Port stays a string in form state — the <Input> writes strings and
  // RHF can't reconcile a zod-transform input/output mismatch. We parse
  // it to a number at submit time.
  port: z
    .string()
    .trim()
    .min(1, "Port is required")
    .refine(
      (v) => /^\d+$/.test(v) && Number(v) >= 1 && Number(v) <= 65535,
      "Port must be 1–65535",
    ),
  username: z.string().trim().min(1, "Username is required").max(128),
  password: z.string().min(0).max(256), // required only on create — see refine in component
  rtsp_path: z.string().trim().min(1).max(256),
});
type SmartValues = z.infer<typeof smartSchema>;

const customSchema = z.object({
  name: z.string().trim().min(1, "Camera name is required").max(128),
  location: z.string().trim().min(1, "Location is required").max(256),
  type: z.enum(["ENTRY", "EXIT"]),
  rtsp_url_custom: z.string().trim().min(1, "RTSP URL is required").max(1024),
});
type CustomValues = z.infer<typeof customSchema>;

type ConnectMode = "smart" | "custom";

function CameraFormDialog({
  open, camera, onOpenChange,
}: { open: boolean; camera: Camera | null; onOpenChange: (open: boolean) => void }) {
  const isEdit = camera !== null;
  const [mode, setMode] = useState<ConnectMode>("smart");
  const [showPassword, setShowPassword] = useState(false);
  // probeResult / checkResult are kept here (not in form state) because
  // they describe out-of-band server state, not form values. Cleared on
  // every connection-relevant edit.
  const [probeResult, setProbeResult] = useState<CameraSmartProbeResponse | null>(null);
  const [customCheck, setCustomCheck] = useState<{ ok: boolean; message: string; latency_ms: number } | null>(null);

  const createMut = useCreateCamera();
  const updateMut = useUpdateCamera();
  const smartProbe = useSmartProbeCamera();
  const singleCheck = useTestCameraConnection();

  const smartForm = useForm<SmartValues>({
    resolver: zodResolver(smartSchema),
    defaultValues: {
      name: "", location: "",
      brand: "hikvision",
      type: "ENTRY",
      ip: "", port: String(DEFAULT_PORT),
      username: "", password: "",
      rtsp_path: DEFAULT_RTSP_PATH,
    },
  });
  const customForm = useForm<CustomValues>({
    resolver: zodResolver(customSchema),
    defaultValues: { name: "", location: "", type: "ENTRY", rtsp_url_custom: "" },
  });

  // Re-seed forms whenever the dialog re-opens or the editing target changes.
  useEffect(() => {
    if (!open) return;
    setProbeResult(null);
    setCustomCheck(null);
    setShowPassword(false);
    setMode("smart"); // edit lands on Smart Connect — fields are populated
    if (camera) {
      smartForm.reset({
        name: camera.name,
        location: camera.location,
        brand: inferBrandFromRtspPath(camera.rtsp_path),
        type: camera.type,
        ip: camera.ip,
        port: String(camera.port),
        username: camera.username,
        password: "",
        rtsp_path: camera.rtsp_path,
      });
      customForm.reset({ name: camera.name, location: camera.location, type: camera.type, rtsp_url_custom: "" });
    } else {
      smartForm.reset({
        name: "", location: "",
        brand: "hikvision",
        type: "ENTRY",
        ip: "", port: String(DEFAULT_PORT),
        username: "", password: "",
        rtsp_path: DEFAULT_RTSP_PATH,
      });
      customForm.reset({ name: "", location: "", type: "ENTRY", rtsp_url_custom: "" });
    }
  }, [open, camera, smartForm, customForm]);

  // Watch connection-relevant fields so we can invalidate the probe
  // result the moment the operator edits any of them — stops the form
  // from carrying a stale "Connected" badge across mismatched values.
  const smartIp = smartForm.watch("ip");
  const smartPort = smartForm.watch("port");
  const smartUsername = smartForm.watch("username");
  const smartPassword = smartForm.watch("password");
  const smartBrand = smartForm.watch("brand");
  const smartRtspPath = smartForm.watch("rtsp_path");

  useEffect(() => {
    setProbeResult(null);
  }, [smartIp, smartPort, smartUsername, smartPassword, smartBrand, smartRtspPath]);

  // Brand change seeds the rtsp_path field with that brand's default
  // template (unless the operator already typed a custom path).
  useEffect(() => {
    const dirty = smartForm.formState.dirtyFields;
    if (!dirty.rtsp_path) smartForm.setValue("rtsp_path", BRAND_DEFAULT_PATHS[smartBrand]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [smartBrand]);

  // ------- Smart Connect: probe + save -------
  async function handleSmartTest() {
    const ok = await smartForm.trigger(["ip", "port", "username", "password", "brand"]);
    if (!ok) return;
    if (isEdit && !smartForm.getValues("password")) {
      toast.error("To test the connection, re-enter the password (not stored on the client).");
      return;
    }
    setProbeResult(null);
    const values = smartForm.getValues();
    smartProbe.mutate(
      {
        brand: values.brand,
        ip: values.ip.trim(),
        port: Number(values.port),
        username: values.username.trim(),
        password: values.password,
      },
      {
        onSuccess: (res) => {
          setProbeResult(res);
          if (res.ok && res.success_rtsp_path) {
            // Auto-fill the winning RTSP path so Save persists exactly
            // what the probe verified works.
            smartForm.setValue("rtsp_path", res.success_rtsp_path, { shouldDirty: true });
            toast.success(`Connected (${res.elapsed_ms} ms · template #${(res.success_template_index ?? 0) + 1})`);
          } else {
            toast.error(res.error ?? "Smart probe failed");
          }
        },
        onError: (e) => toast.error(e instanceof Error ? e.message : "Smart probe failed"),
      },
    );
  }

  function handleSmartSubmit(values: SmartValues) {
    const payload: CameraCreatePayload = {
      name: values.name.trim(),
      location: values.location.trim(),
      ip: values.ip.trim(),
      port: Number(values.port),
      username: values.username.trim(),
      password: values.password,
      rtsp_path: values.rtsp_path.trim(),
      enable_face_ingest: true,
      type: values.type,
    };
    if (isEdit && camera) {
      const patch: Partial<CameraCreatePayload> = { ...payload };
      if (!values.password) delete patch.password;
      updateMut.mutate(
        { id: camera.id, patch },
        {
          onSuccess: () => { toast.success("Camera updated"); onOpenChange(false); },
          onError: (e) => toast.error(e instanceof Error ? e.message : "Could not update camera"),
        },
      );
    } else {
      if (!values.password) {
        smartForm.setError("password", { message: "Password is required" });
        return;
      }
      createMut.mutate(payload, {
        onSuccess: () => { toast.success("Camera added"); onOpenChange(false); },
        onError: (e) => toast.error(e instanceof Error ? e.message : "Could not add camera"),
      });
    }
  }

  // ------- Custom Connect: parse, test, save -------
  async function handleCustomTest() {
    const ok = await customForm.trigger("rtsp_url_custom");
    if (!ok) return;
    const parsed = parseRtspUrl(customForm.getValues("rtsp_url_custom"));
    if (!parsed.ok) {
      customForm.setError("rtsp_url_custom", { message: parsed.reason });
      return;
    }
    setCustomCheck(null);
    singleCheck.mutate(parsed.parts, {
      onSuccess: (r) => {
        setCustomCheck(r);
        if (r.ok) toast.success(`Connected (${r.latency_ms} ms)`);
        else toast.error(r.message);
      },
      onError: (e) => toast.error(e instanceof Error ? e.message : "Probe failed"),
    });
  }

  function handleCustomSubmit(values: CustomValues) {
    const parsed = parseRtspUrl(values.rtsp_url_custom);
    if (!parsed.ok) {
      customForm.setError("rtsp_url_custom", { message: parsed.reason });
      return;
    }
    const payload: CameraCreatePayload = {
      name: values.name.trim(),
      location: values.location.trim(),
      ip: parsed.parts.ip,
      port: parsed.parts.port,
      username: parsed.parts.username,
      password: parsed.parts.password,
      rtsp_path: parsed.parts.rtsp_path,
      enable_face_ingest: true,
      type: values.type,
    };
    if (isEdit && camera) {
      updateMut.mutate({ id: camera.id, patch: payload }, {
        onSuccess: () => { toast.success("Camera updated"); onOpenChange(false); },
        onError: (e) => toast.error(e instanceof Error ? e.message : "Could not update camera"),
      });
    } else {
      createMut.mutate(payload, {
        onSuccess: () => { toast.success("Camera added"); onOpenChange(false); },
        onError: (e) => toast.error(e instanceof Error ? e.message : "Could not add camera"),
      });
    }
  }

  const submitting = createMut.isPending || updateMut.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl rounded-2xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit camera" : "Add camera"}</DialogTitle>
          {isEdit ? null : (
            <DialogDescription>
              Pick your camera's brand and we'll try every known RTSP template until one returns a frame.
            </DialogDescription>
          )}
        </DialogHeader>

        <div
          role="tablist"
          aria-label="Connection method"
          className="inline-flex w-full rounded-xl border border-slate-200 bg-slate-50 p-1 text-sm font-medium"
        >
          {(["smart", "custom"] as const).map((m) => (
            <button
              key={m}
              type="button"
              role="tab"
              aria-selected={mode === m}
              onClick={() => setMode(m)}
              className={cn(
                "flex-1 rounded-lg px-3 py-1.5 transition-colors inline-flex items-center justify-center gap-1.5",
                mode === m ? "bg-white text-[#2f8f7b] shadow-sm" : "text-slate-600 hover:text-slate-900",
              )}
            >
              {m === "smart" ? <Sparkles className="h-3.5 w-3.5" /> : null}
              {m === "smart" ? "Smart Connect" : "Custom RTSP URL"}
            </button>
          ))}
        </div>

        {mode === "smart" ? (
          <form onSubmit={smartForm.handleSubmit(handleSmartSubmit)} className="space-y-4" noValidate>
            <Field label="Camera brand" required error={smartForm.formState.errors.brand?.message}>
              <Controller
                control={smartForm.control}
                name="brand"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={(v) => field.onChange(v as CameraBrand)}>
                    <SelectTrigger><SelectValue placeholder="Select a brand" /></SelectTrigger>
                    <SelectContent>
                      {(Object.keys(BRAND_LABELS) as CameraBrand[]).map((b) => (
                        <SelectItem key={b} value={b}>{BRAND_LABELS[b]}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </Field>

            <Field label="Attendance use case" required error={smartForm.formState.errors.type?.message}>
              <Controller
                control={smartForm.control}
                name="type"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={(v) => field.onChange(v as CameraType)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ENTRY">Person Entry</SelectItem>
                      <SelectItem value="EXIT">Person Exit</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </Field>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <Field label="Camera name" required error={smartForm.formState.errors.name?.message}>
                <Input placeholder="Reception" {...smartForm.register("name")} />
              </Field>
              <Field label="Location" required error={smartForm.formState.errors.location?.message}>
                <Input placeholder="Floor 1 - Lobby" {...smartForm.register("location")} />
              </Field>
              <Field label="Camera IP" required error={smartForm.formState.errors.ip?.message}>
                <Input placeholder="192.168.1.100" {...smartForm.register("ip")} />
              </Field>
              <Field label="Port" required error={smartForm.formState.errors.port?.message}>
                <Input type="number" inputMode="numeric" placeholder="554" {...smartForm.register("port")} />
              </Field>
              <Field label="Username" required error={smartForm.formState.errors.username?.message}>
                <Input autoComplete="off" {...smartForm.register("username")} />
              </Field>
              <Field
                label="Password"
                required={!isEdit}
                error={smartForm.formState.errors.password?.message}
              >
                <div className="relative">
                  <Input
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    className="pr-9"
                    {...smartForm.register("password")}
                  />
                  <button
                    type="button"
                    className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-slate-400 hover:text-slate-600"
                    onClick={() => setShowPassword((p) => !p)}
                    tabIndex={-1}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </Field>
              <Field label="RTSP URL" className="sm:col-span-2">
                <Input
                  value={buildRtspUrlDisplay({
                    username: smartUsername, ip: smartIp, port: String(smartPort), rtsp_path: smartRtspPath,
                  })}
                  readOnly aria-readonly="true" tabIndex={-1}
                  className="cursor-default bg-slate-50 font-mono text-xs"
                />
              </Field>
            </div>

            {/* Test button + audit panel */}
            <div className="flex flex-wrap items-center justify-between gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleSmartTest}
                disabled={smartProbe.isPending || submitting}
                className="rounded-xl"
              >
                {smartProbe.isPending ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <TestTube2 className="mr-1.5 h-4 w-4" />}
                Test connection
              </Button>
              {probeResult ? (
                <span className="text-[11px] text-slate-500">
                  {probeResult.attempts.length} URL{probeResult.attempts.length === 1 ? "" : "s"} tried · {probeResult.elapsed_ms} ms
                </span>
              ) : null}
            </div>
            {probeResult ? <ProbeResultPanel result={probeResult} /> : null}

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={submitting}>
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={submitting}
                className="rounded-xl bg-gradient-to-r from-[#4aa590] to-[#2f8f7b] px-5 text-white hover:from-[#3f9382] hover:to-[#256f60]"
              >
                {submitting ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : null}
                {isEdit ? "Save changes" : "Add camera"}
              </Button>
            </DialogFooter>
          </form>
        ) : (
          <form onSubmit={customForm.handleSubmit(handleCustomSubmit)} className="space-y-4" noValidate>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <Field label="Camera name" required error={customForm.formState.errors.name?.message}>
                <Input placeholder="Reception" {...customForm.register("name")} />
              </Field>
              <Field label="Location" required error={customForm.formState.errors.location?.message}>
                <Input placeholder="Floor 1 - Lobby" {...customForm.register("location")} />
              </Field>
            </div>
            <Field label="Attendance use case" required error={customForm.formState.errors.type?.message}>
              <Controller
                control={customForm.control}
                name="type"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={(v) => field.onChange(v as CameraType)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ENTRY">Person Entry</SelectItem>
                      <SelectItem value="EXIT">Person Exit</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </Field>
            <Field label="RTSP URL" required error={customForm.formState.errors.rtsp_url_custom?.message}>
              <div className="flex gap-2">
                <Input
                  placeholder="rtsp://user:password@192.168.1.100:554/Streaming/Channels/101"
                  className="font-mono text-xs"
                  autoComplete="off"
                  spellCheck={false}
                  {...customForm.register("rtsp_url_custom")}
                  onChange={(e) => {
                    customForm.register("rtsp_url_custom").onChange(e);
                    setCustomCheck(null);
                  }}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleCustomTest}
                  disabled={singleCheck.isPending || submitting}
                  className="rounded-xl"
                >
                  {singleCheck.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <TestTube2 className="h-4 w-4" />}
                  Test
                </Button>
              </div>
              <p className="mt-1 text-[11px] text-slate-500">
                Paste the full URL including credentials; we'll parse host, port, and path on save.
              </p>
            </Field>
            {customCheck ? <CustomCheckPanel result={customCheck} /> : null}

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={submitting}>
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={submitting}
                className="rounded-xl bg-gradient-to-r from-[#4aa590] to-[#2f8f7b] px-5 text-white hover:from-[#3f9382] hover:to-[#256f60]"
              >
                {submitting ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : null}
                {isEdit ? "Save changes" : "Add camera"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ----- Probe result panels -------------------------------------------------

function ProbeResultPanel({ result }: { result: CameraSmartProbeResponse }) {
  return (
    <div
      className={cn(
        "space-y-2 rounded-xl border p-3 text-xs",
        result.ok
          ? "border-emerald-200 bg-emerald-50 text-emerald-800"
          : "border-rose-200 bg-rose-50 text-rose-700",
      )}
    >
      <div className="flex items-start gap-2">
        {result.ok ? (
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
        ) : (
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
        )}
        <div className="space-y-0.5">
          {result.ok ? (
            <>
              <p className="font-medium">
                Connected — template #{(result.success_template_index ?? 0) + 1} worked
              </p>
              <p className="opacity-80">
                {result.width != null && result.height != null
                  ? <>Resolution: {result.width}×{result.height} · </>
                  : null}
                Path: <code className="font-mono">{result.success_rtsp_path}</code>
              </p>
            </>
          ) : (
            <>
              <p className="font-medium">Could not connect</p>
              <p className="opacity-80">{result.error ?? "No template returned a frame."}</p>
            </>
          )}
        </div>
      </div>
      {result.attempts.length > 0 ? (
        <details className="ml-6 cursor-pointer" open={!result.ok}>
          <summary className="text-[11px] opacity-80">
            {result.ok ? "Show attempts" : `Show all ${result.attempts.length} attempts`}
          </summary>
          <ul className="mt-1 space-y-1.5">
            {result.attempts.map((a) => (
              <li key={a.template_index} className="space-y-0.5">
                <div className="flex items-center gap-1.5">
                  {a.ok ? (
                    <CheckCircle2 className="h-3 w-3 shrink-0 text-emerald-600" />
                  ) : (
                    <XCircle className="h-3 w-3 shrink-0 text-rose-500/80" />
                  )}
                  <code className="break-all font-mono text-[10px] opacity-80">{a.rtsp_url_masked}</code>
                  <span className="ml-auto whitespace-nowrap text-[10px] opacity-60">{a.elapsed_ms} ms</span>
                </div>
                {!a.ok && a.error ? (
                  <p className="ml-5 text-[10px] opacity-75">{a.error}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </div>
  );
}

function CustomCheckPanel({ result }: { result: { ok: boolean; message: string; latency_ms: number } }) {
  return (
    <div
      className={cn(
        "flex items-start gap-2 rounded-xl border p-3 text-xs",
        result.ok
          ? "border-emerald-200 bg-emerald-50 text-emerald-800"
          : "border-rose-200 bg-rose-50 text-rose-700",
      )}
    >
      {result.ok ? (
        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
      ) : (
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
      )}
      <div className="space-y-0.5">
        <p className="font-medium">{result.ok ? "Stream reachable" : "Probe failed"}</p>
        <p className="opacity-80">
          {result.message} {result.ok ? `· ${result.latency_ms} ms` : null}
        </p>
      </div>
    </div>
  );
}

// ----- Tiny Field wrapper --------------------------------------------------

function Field({
  label, required, error, className, children,
}: {
  label: string;
  required?: boolean;
  error?: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <Label className="text-slate-700">
        {label}
        {required ? <span className="ml-0.5 text-rose-500">*</span> : null}
      </Label>
      {children}
      {error ? <p className="text-[11px] text-rose-600">{error}</p> : null}
    </div>
  );
}
