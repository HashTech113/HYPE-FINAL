import { useEffect, useState } from "react";
import { Loader2, Save, ScanFace } from "lucide-react";

import {
  getRecognitionConfig,
  patchRecognitionConfig,
  type RecognitionConfig,
} from "@/api/dashboardApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatTime12 } from "@/lib/dateFormat";

/** Admin-only panel for the live-tunable recognition thresholds. Saves to
 *  PATCH /api/admin/settings/recognition; the camera worker picks the
 *  new values up on its next inference pass (≤5s, no restart).
 */
export function RecognitionSettingsPanel() {
  const [config, setConfig] = useState<RecognitionConfig | null>(null);
  const [draft, setDraft] = useState<RecognitionConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getRecognitionConfig()
      .then((cfg) => {
        if (cancelled) return;
        setConfig(cfg);
        setDraft(cfg);
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const dirty =
    config !== null &&
    draft !== null &&
    (Object.keys(config) as (keyof RecognitionConfig)[]).some(
      (k) => config[k] !== draft[k],
    );

  async function handleSave() {
    if (!draft || !config) return;
    setSaving(true);
    setError(null);
    try {
      // Send only the changed fields so a partial save doesn't reset
      // unrelated keys the admin didn't touch.
      const patch: Partial<RecognitionConfig> = {};
      for (const k of Object.keys(draft) as (keyof RecognitionConfig)[]) {
        if (draft[k] !== config[k]) (patch as Record<string, unknown>)[k] = draft[k];
      }
      const next = await patchRecognitionConfig(patch);
      setConfig(next);
      setDraft(next);
      setSavedAt(formatTime12(new Date()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex h-32 items-center justify-center text-sm text-slate-500">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        Loading recognition settings…
      </div>
    );
  }

  if (!draft) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {error ?? "Failed to load settings."}
      </div>
    );
  }

  return (
    <div className="flex max-w-3xl flex-col gap-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
        <ScanFace className="h-4 w-4 text-primary" />
        Recognition thresholds
      </div>
      <p className="text-xs text-slate-500">
        Tune the face-recognition pipeline without restarting the workers — changes apply
        within ~5 seconds.
      </p>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Field
          label="Face match threshold"
          hint="Cosine similarity floor (0 – 1). Higher = stricter; fewer matches but fewer mismatches."
        >
          <Input
            type="number"
            step="0.01"
            min={0}
            max={1}
            value={draft.face_match_threshold}
            onChange={(e) => setDraft({ ...draft, face_match_threshold: clamp01(e.target.value) })}
          />
        </Field>

        <Field
          label="Face detector quality floor"
          hint="Minimum detector score (0 – 1). Drops blurry / low-confidence detections before recognition."
        >
          <Input
            type="number"
            step="0.01"
            min={0}
            max={1}
            value={draft.face_min_quality}
            onChange={(e) => setDraft({ ...draft, face_min_quality: clamp01(e.target.value) })}
          />
        </Field>

        <Field
          label="Min face size for recognition (px)"
          hint="Faces whose shortest bbox edge is below this are not matched. 0 disables the filter."
        >
          <Input
            type="number"
            min={0}
            max={4096}
            step={5}
            value={draft.recognize_min_face_size_px}
            onChange={(e) =>
              setDraft({
                ...draft,
                recognize_min_face_size_px: clampInt(e.target.value, 0, 4096),
              })
            }
          />
        </Field>

        <Field
          label="Detection rate (FPS)"
          hint="How often each camera worker runs face detection. Higher = faster recognition, more CPU/GPU load."
        >
          <Input
            type="number"
            min={1}
            max={60}
            step={1}
            value={draft.camera_fps}
            onChange={(e) =>
              setDraft({ ...draft, camera_fps: clampInt(e.target.value, 1, 60) })
            }
          />
        </Field>

        <Field
          label="Per-employee cooldown (seconds)"
          hint="Minimum gap between attendance events for the same person. Stops a face lingering in front of the camera from creating duplicate rows."
        >
          <Input
            type="number"
            min={0}
            max={3600}
            step={1}
            value={draft.cooldown_seconds}
            onChange={(e) =>
              setDraft({ ...draft, cooldown_seconds: clampInt(e.target.value, 0, 3600) })
            }
          />
        </Field>
      </div>

      {error ? (
        <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {error}
        </div>
      ) : null}

      <div className="flex items-center justify-end gap-2 pt-2">
        {savedAt ? (
          <span className="text-xs text-emerald-600">Saved at {savedAt}</span>
        ) : null}
        <Button type="button" disabled={saving || !dirty} onClick={handleSave}>
          {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
          Save
        </Button>
      </div>
    </div>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <Label className="text-xs font-semibold text-slate-700">{label}</Label>
      {children}
      {hint ? <p className="text-[11px] text-slate-500">{hint}</p> : null}
    </div>
  );
}

function clamp01(raw: string): number {
  const n = Number(raw);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

function clampInt(raw: string, lo: number, hi: number): number {
  const n = parseInt(raw, 10);
  if (!Number.isFinite(n)) return lo;
  return Math.max(lo, Math.min(hi, n));
}
