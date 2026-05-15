"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  Sparkles,
  TestTube2,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api/client";
import {
  useCameraProfiles,
  useConnectCamera,
  useCreateCamera,
  useProbeCamera,
  useSmartCreateCamera,
  useUpdateCamera,
} from "@/lib/hooks/use-cameras";
import type {
  Camera,
  CameraConnectAttempt,
  CameraConnectResult,
  CameraCreate,
  CameraProbeResult,
  CameraType,
  CameraUpdate,
} from "@/lib/types/camera";
import { cn } from "@/lib/utils";

const RTSP_REGEX = /^(rtsp|rtsps|http|https):\/\//i;
// Accepts IPv4, IPv6 (bracketed), or DNS hostnames. Permissive on
// purpose — the connection probe is the real authority on validity.
const HOST_REGEX = /^[A-Za-z0-9._:\-\[\]]+$/;

interface CameraFormDialogProps {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  camera: Camera | null;
}

/**
 * Add / Edit camera. The Add flow is a tabbed wizard:
 *
 *   "Smart connect" (default) — pick brand, type IP & creds, hit Test;
 *   the backend tries every URL template the brand profile knows and
 *   stops at the first that returns a frame.
 *
 *   "Custom RTSP URL" — paste a URL; the existing single-URL probe.
 *
 * The Edit flow is single-tab (Custom URL) because PATCH today only
 * accepts the resolved rtsp_url. To re-resolve from credentials, delete
 * and re-add — the smart-connect inputs from the original create are
 * shown as read-only context.
 */
export function CameraFormDialog({
  open,
  onOpenChange,
  camera,
}: CameraFormDialogProps) {
  const isEdit = camera !== null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit camera" : "Add camera"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update the camera's settings. The worker restarts automatically when you save."
              : "Pick your camera's brand and we'll figure out the right RTSP URL for you. If your brand isn't listed, paste a URL on the Custom tab."}
          </DialogDescription>
        </DialogHeader>

        {isEdit ? (
          <CustomUrlForm
            camera={camera}
            onClose={() => onOpenChange(false)}
          />
        ) : (
          <Tabs defaultValue="smart" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="smart" className="gap-1.5">
                <Sparkles className="h-3.5 w-3.5" />
                Smart connect
              </TabsTrigger>
              <TabsTrigger value="custom">Custom RTSP URL</TabsTrigger>
            </TabsList>

            <TabsContent value="smart" className="pt-3">
              <SmartConnectForm onClose={() => onOpenChange(false)} />
            </TabsContent>

            <TabsContent value="custom" className="pt-3">
              <CustomUrlForm camera={null} onClose={() => onOpenChange(false)} />
            </TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
}

// =========================================================================
// Smart-connect tab
// =========================================================================

const smartSchema = z.object({
  brand: z.string().min(1, "Pick a camera brand"),
  host: z
    .string()
    .trim()
    .min(1, "IP or hostname is required")
    .max(255)
    .refine((v) => HOST_REGEX.test(v), "Invalid IP / hostname"),
  port: z
    .string()
    .trim()
    .optional()
    .or(z.literal(""))
    .refine(
      (v) => !v || (/^\d+$/.test(v) && Number(v) >= 1 && Number(v) <= 65535),
      "Port must be 1–65535",
    ),
  username: z.string().trim().max(128).optional().or(z.literal("")),
  password: z.string().max(256).optional().or(z.literal("")),
  channel: z.string().trim().max(16).optional().or(z.literal("")),
  stream: z.string().min(1).max(16),
  // Persist-only fields:
  name: z.string().trim().min(1, "Name is required").max(128),
  camera_type: z.enum(["ENTRY", "EXIT"]),
  location: z.string().trim().max(256).optional().or(z.literal("")),
  description: z.string().trim().max(1024).optional().or(z.literal("")),
  is_active: z.boolean(),
});

type SmartValues = z.infer<typeof smartSchema>;

function SmartConnectForm({ onClose }: { onClose: () => void }) {
  const profilesQ = useCameraProfiles();
  const probe = useConnectCamera();
  const save = useSmartCreateCamera();
  const submitting = save.isPending;

  const [testResult, setTestResult] = useState<CameraConnectResult | null>(null);

  const form = useForm<SmartValues>({
    resolver: zodResolver(smartSchema),
    defaultValues: {
      brand: "",
      host: "",
      port: "",
      username: "",
      password: "",
      channel: "",
      stream: "main",
      name: "",
      camera_type: "ENTRY",
      location: "",
      description: "",
      is_active: true,
    },
  });

  const errors = form.formState.errors;
  const selectedBrand = form.watch("brand");
  const profile = useMemo(
    () => profilesQ.data?.find((p) => p.id === selectedBrand) ?? null,
    [profilesQ.data, selectedBrand],
  );

  // When the brand changes, prefill defaults that are brand-specific —
  // but only if the user hasn't already typed a custom value. This is
  // why we check `dirtyFields` rather than overwriting unconditionally.
  useEffect(() => {
    if (!profile) return;
    const dirty = form.formState.dirtyFields;
    if (!dirty.port) form.setValue("port", String(profile.default_port));
    if (!dirty.username) form.setValue("username", profile.default_username);
    if (!dirty.channel) form.setValue("channel", profile.default_channel);
    // Stream defaults to the first variant the brand exposes.
    if (!dirty.stream && profile.streams.length > 0) {
      form.setValue("stream", profile.streams[0].id);
    }
    setTestResult(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile?.id]);

  function buildConnectPayload(values: SmartValues) {
    return {
      brand: values.brand,
      host: values.host.trim(),
      port: values.port ? Number(values.port) : null,
      username: values.username || null,
      password: values.password || null,
      channel: values.channel || null,
      stream: values.stream,
      per_attempt_timeout_ms: 4000,
    };
  }

  async function handleTest() {
    const ok = await form.trigger([
      "brand",
      "host",
      "port",
      "username",
      "password",
      "channel",
      "stream",
    ]);
    if (!ok) return;
    setTestResult(null);
    const values = form.getValues();
    probe.mutate(buildConnectPayload(values), {
      onSuccess: (res) => setTestResult(res),
    });
  }

  function handleSubmit(values: SmartValues) {
    setTestResult(null);
    save.mutate(
      {
        ...buildConnectPayload(values),
        name: values.name.trim(),
        camera_type: values.camera_type,
        location: values.location || null,
        description: values.description || null,
        is_active: values.is_active,
      },
      {
        onSuccess: () => onClose(),
        onError: (err) => {
          // Backend returns 422 with the per-attempt audit trail in the
          // body when smart-connect can't find a working URL. Pipe that
          // into the diagnostics panel so the user sees exactly which
          // URL patterns failed and why — instead of just a toast.
          if (err instanceof ApiError && err.status === 422 && err.data) {
            // FastAPI HTTPException wraps our payload under `detail`,
            // while AppError-style responses put it at the top level.
            // Accept either shape.
            type ErrShape = {
              attempts?: CameraConnectAttempt[];
              message?: string;
            };
            const body = err.data as { detail?: ErrShape } & ErrShape;
            const detail: ErrShape = body?.detail ?? body;
            setTestResult({
              ok: false,
              profile_id: values.brand,
              success_url: null,
              success_template_index: null,
              width: null,
              height: null,
              elapsed_ms: 0,
              attempts: detail?.attempts ?? [],
              error: detail?.message ?? "Could not connect",
            });
          }
        },
      },
    );
  }

  return (
    <form
      onSubmit={form.handleSubmit(handleSubmit)}
      className="space-y-4"
      noValidate
    >
      {/* --- Brand picker ------------------------------------------------ */}
      <Field label="Camera brand" required error={errors.brand?.message}>
        <Select
          value={selectedBrand}
          onValueChange={(v) =>
            form.setValue("brand", v, { shouldDirty: true, shouldValidate: true })
          }
          disabled={profilesQ.isLoading || submitting}
        >
          <SelectTrigger>
            <SelectValue placeholder={profilesQ.isLoading ? "Loading…" : "Choose your camera's brand"} />
          </SelectTrigger>
          <SelectContent className="max-h-72">
            {profilesQ.data?.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {profile?.notes && (
          <p className="mt-1 text-xs text-muted-foreground">{profile.notes}</p>
        )}
      </Field>

      {/* --- Connection fields ------------------------------------------- */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="IP or hostname" required error={errors.host?.message}>
          <Input
            placeholder="192.168.1.100"
            {...form.register("host")}
            disabled={submitting}
            onChange={(e) => {
              form.register("host").onChange(e);
              setTestResult(null);
            }}
          />
        </Field>
        <Field label="Port" error={errors.port?.message}>
          <Input
            inputMode="numeric"
            placeholder={profile ? String(profile.default_port) : "554"}
            {...form.register("port")}
            disabled={submitting}
          />
        </Field>
        <Field label="Username" error={errors.username?.message}>
          <Input
            placeholder={profile ? profile.default_username : "admin"}
            autoComplete="off"
            {...form.register("username")}
            disabled={submitting}
            onChange={(e) => {
              form.register("username").onChange(e);
              setTestResult(null);
            }}
          />
        </Field>
        <Field label="Password" error={errors.password?.message}>
          <Input
            type="password"
            autoComplete="new-password"
            {...form.register("password")}
            disabled={submitting}
            onChange={(e) => {
              form.register("password").onChange(e);
              setTestResult(null);
            }}
          />
        </Field>
        <Field label="Channel" error={errors.channel?.message}>
          <Input
            placeholder={profile ? profile.default_channel : "1"}
            {...form.register("channel")}
            disabled={submitting}
          />
        </Field>
        <Field label="Stream quality" error={errors.stream?.message}>
          <Select
            value={form.watch("stream")}
            onValueChange={(v) =>
              form.setValue("stream", v, { shouldDirty: true })
            }
            disabled={!profile || submitting}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(profile?.streams ?? [
                { id: "main", label: "Main" },
                { id: "sub", label: "Sub" },
              ]).map((s) => (
                <SelectItem key={s.id} value={s.id}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Field>
      </div>

      {/* --- Test button + diagnostics ------------------------------------ */}
      <div className="flex items-center justify-between">
        <Button
          type="button"
          variant="outline"
          onClick={handleTest}
          disabled={probe.isPending || submitting}
        >
          {probe.isPending ? (
            <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
          ) : (
            <TestTube2 className="mr-1.5 h-4 w-4" />
          )}
          Test connection
        </Button>
        {testResult && (
          <span className="text-xs text-muted-foreground">
            {testResult.attempts.length} URL{testResult.attempts.length === 1 ? "" : "s"} tried •{" "}
            {testResult.elapsed_ms} ms total
          </span>
        )}
      </div>

      {testResult && <ConnectResultPanel result={testResult} />}

      {/* --- Identity ----------------------------------------------------- */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Camera name" required error={errors.name?.message}>
          <Input
            placeholder="Main Entry"
            {...form.register("name")}
            disabled={submitting}
          />
        </Field>
        <Field label="Type" required error={errors.camera_type?.message}>
          <Select
            value={form.watch("camera_type")}
            onValueChange={(v) =>
              form.setValue("camera_type", v as CameraType, {
                shouldDirty: true,
              })
            }
          >
            <SelectTrigger disabled={submitting}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ENTRY">ENTRY (incoming)</SelectItem>
              <SelectItem value="EXIT">EXIT (outgoing)</SelectItem>
            </SelectContent>
          </Select>
        </Field>
        <Field label="Location">
          <Input
            placeholder="Front door, ground floor"
            {...form.register("location")}
            disabled={submitting}
          />
        </Field>
        <Field label="Status">
          <label className="mt-2 flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-input accent-primary"
              {...form.register("is_active")}
              disabled={submitting}
            />
            Active (worker will start when saved)
          </label>
        </Field>
      </div>
      <Field label="Description">
        <Textarea
          placeholder="Optional notes — angle, mounting, model, etc."
          rows={2}
          {...form.register("description")}
          disabled={submitting}
        />
      </Field>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
          Cancel
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
          Connect & Save
        </Button>
      </div>
    </form>
  );
}

function ConnectResultPanel({ result }: { result: CameraConnectResult }) {
  return (
    <div
      className={cn(
        "space-y-2 rounded-md border p-3 text-xs",
        result.ok
          ? "border-green-500/30 bg-green-500/10 text-green-700 dark:text-green-300"
          : "border-destructive/40 bg-destructive/10 text-destructive",
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
              <p>
                Resolution: {result.width}×{result.height}
                {result.success_url && (
                  <>
                    <br />
                    URL: <code className="font-mono">{result.success_url}</code>
                  </>
                )}
              </p>
            </>
          ) : (
            <>
              <p className="font-medium">Could not connect</p>
              <p>{result.error ?? "Unknown error"}</p>
            </>
          )}
        </div>
      </div>
      {/* Per-attempt audit trail. Hidden in success unless the user wants it. */}
      <details className="ml-6 cursor-pointer">
        <summary className="text-xs opacity-80">
          {result.ok ? "Show attempts" : `View all ${result.attempts.length} attempts`}
        </summary>
        <ul className="mt-1 space-y-0.5">
          {result.attempts.map((a) => (
            <li key={a.template_index} className="flex items-center gap-1.5">
              {a.ok ? (
                <CheckCircle2 className="h-3 w-3 shrink-0 text-green-500" />
              ) : (
                <XCircle className="h-3 w-3 shrink-0 text-destructive opacity-70" />
              )}
              <code className="break-all font-mono text-[10px] opacity-80">{a.url}</code>
              <span className="ml-auto whitespace-nowrap text-[10px] opacity-60">
                {a.elapsed_ms} ms
              </span>
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}

// =========================================================================
// Custom RTSP URL tab (= legacy Add and the only Edit form)
// =========================================================================

const customSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(128),
  rtsp_url: z
    .string()
    .trim()
    .min(1, "RTSP URL is required")
    .max(1024)
    .refine(
      (v) => RTSP_REGEX.test(v),
      "Must start with rtsp://, rtsps://, http:// or https://",
    ),
  camera_type: z.enum(["ENTRY", "EXIT"]),
  location: z.string().trim().max(256).optional().or(z.literal("")),
  description: z.string().trim().max(1024).optional().or(z.literal("")),
  is_active: z.boolean(),
});

type CustomValues = z.infer<typeof customSchema>;

function toUndef(v: string | undefined): string | undefined {
  return v && v.length > 0 ? v : undefined;
}

function CustomUrlForm({
  camera,
  onClose,
}: {
  camera: Camera | null;
  onClose: () => void;
}) {
  const isEdit = camera !== null;
  const create = useCreateCamera();
  const update = useUpdateCamera();
  const probe = useProbeCamera();
  const submitting = create.isPending || update.isPending;

  const [probeResult, setProbeResult] = useState<CameraProbeResult | null>(null);

  const form = useForm<CustomValues>({
    resolver: zodResolver(customSchema),
    defaultValues: camera
      ? {
          name: camera.name,
          rtsp_url: camera.rtsp_url,
          camera_type: camera.camera_type,
          location: camera.location ?? "",
          description: camera.description ?? "",
          is_active: camera.is_active,
        }
      : {
          name: "",
          rtsp_url: "",
          camera_type: "ENTRY",
          location: "",
          description: "",
          is_active: true,
        },
  });

  const errors = form.formState.errors;

  function handleProbe() {
    setProbeResult(null);
    const url = form.getValues("rtsp_url").trim();
    if (!url || !RTSP_REGEX.test(url)) {
      form.setError("rtsp_url", { message: "Enter a valid URL first" });
      return;
    }
    probe.mutate(
      { rtsp_url: url, timeout_ms: 8000 },
      { onSuccess: (res) => setProbeResult(res) },
    );
  }

  function handleSubmit(values: CustomValues) {
    const payload = {
      name: values.name.trim(),
      rtsp_url: values.rtsp_url.trim(),
      camera_type: values.camera_type,
      location: toUndef(values.location) ?? null,
      description: toUndef(values.description) ?? null,
      is_active: values.is_active,
    };
    if (isEdit && camera) {
      update.mutate(
        { id: camera.id, payload: payload as CameraUpdate },
        { onSuccess: () => onClose() },
      );
    } else {
      create.mutate(payload as CameraCreate, { onSuccess: () => onClose() });
    }
  }

  return (
    <form
      onSubmit={form.handleSubmit(handleSubmit)}
      className="space-y-4"
      noValidate
    >
      {isEdit && camera?.brand && (
        <div className="rounded-md border border-border bg-muted/40 p-3 text-xs">
          <p className="font-medium">Originally connected via Smart Connect</p>
          <p className="mt-0.5 text-muted-foreground">
            Brand: <span className="font-mono">{camera.brand}</span>
            {camera.host && (
              <>
                {" • "}Host: <span className="font-mono">{camera.host}</span>
              </>
            )}
            {camera.port && (
              <>
                {" • "}Port: <span className="font-mono">{camera.port}</span>
              </>
            )}
            {camera.stream && (
              <>
                {" • "}Stream: <span className="font-mono">{camera.stream}</span>
              </>
            )}
          </p>
          <p className="mt-1 text-muted-foreground">
            To re-resolve from new credentials, delete this camera and re-add via Smart Connect.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Name" required error={errors.name?.message}>
          <Input
            placeholder="Main Entry"
            autoFocus
            {...form.register("name")}
            disabled={submitting}
          />
        </Field>
        <Field label="Type" required error={errors.camera_type?.message}>
          <Select
            value={form.watch("camera_type")}
            onValueChange={(v) =>
              form.setValue("camera_type", v as CameraType, { shouldDirty: true })
            }
          >
            <SelectTrigger disabled={submitting}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ENTRY">ENTRY (incoming)</SelectItem>
              <SelectItem value="EXIT">EXIT (outgoing)</SelectItem>
            </SelectContent>
          </Select>
        </Field>
      </div>

      <Field label="RTSP URL" required error={errors.rtsp_url?.message}>
        <div className="flex gap-2">
          <Input
            placeholder="rtsp://admin:Admin%40123@192.168.1.101:554/cam/realmonitor?channel=1&subtype=1"
            {...form.register("rtsp_url")}
            disabled={submitting}
            onChange={(e) => {
              form.register("rtsp_url").onChange(e);
              setProbeResult(null);
            }}
            className="font-mono text-xs"
          />
          <Button
            type="button"
            variant="outline"
            onClick={handleProbe}
            disabled={probe.isPending || submitting}
          >
            {probe.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <TestTube2 className="h-4 w-4" />
            )}
            Test
          </Button>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          Tip: if the password contains <code>@</code>, replace it with <code>%40</code>.
        </p>
      </Field>

      {probeResult && (
        <div
          className={cn(
            "flex items-start gap-2 rounded-md border p-3 text-xs",
            probeResult.ok
              ? "border-green-500/30 bg-green-500/10 text-green-700 dark:text-green-300"
              : "border-destructive/40 bg-destructive/10 text-destructive",
          )}
        >
          {probeResult.ok ? (
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
          ) : (
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          )}
          <div className="space-y-0.5">
            {probeResult.ok ? (
              <>
                <p className="font-medium">Stream reachable</p>
                <p>
                  Resolution: {probeResult.width}×{probeResult.height} • Connect time:{" "}
                  {probeResult.elapsed_ms} ms
                </p>
              </>
            ) : (
              <>
                <p className="font-medium">Probe failed</p>
                <p>{probeResult.error ?? "Unknown error"}</p>
              </>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Location">
          <Input
            placeholder="Front door, ground floor"
            {...form.register("location")}
            disabled={submitting}
          />
        </Field>
        <Field label="Status">
          <label className="mt-2 flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-input accent-primary"
              {...form.register("is_active")}
              disabled={submitting}
            />
            Active (worker will start when saved)
          </label>
        </Field>
      </div>

      <Field label="Description">
        <Textarea
          placeholder="Optional notes — angle, mounting, model, etc."
          rows={2}
          {...form.register("description")}
          disabled={submitting}
        />
      </Field>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
          Cancel
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
          {isEdit ? "Save changes" : "Add camera"}
        </Button>
      </div>
    </form>
  );
}

// =========================================================================

function Field({
  label,
  required,
  error,
  children,
}: {
  label: string;
  required?: boolean;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label
        className={cn(
          required && "after:ml-0.5 after:text-destructive after:content-['*']",
        )}
      >
        {label}
      </Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
