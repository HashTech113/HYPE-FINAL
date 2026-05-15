import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const SHIFT_TIME_PATTERN = /^([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d$/;

export type ShiftTimingPickerProps = {
  /** Stored as `HH:mm-HH:mm` (24-hour). */
  value: string;
  onChange: (next: string) => void;
  startLabel?: string;
  endLabel?: string;
};

export function isValidShift(value: string) {
  if (!SHIFT_TIME_PATTERN.test(value)) return false;
  const [start, end] = value.split("-");
  const [sh, sm] = start.split(":").map(Number);
  const [eh, em] = end.split(":").map(Number);
  return sh * 60 + sm < eh * 60 + em;
}

export function normalizeShift(value: string) {
  return (value || "").replace(/\s+/g, "");
}

function to12Hour(time24: string) {
  // Accept either ``H:mm`` or ``HH:mm`` so legacy rows missing a leading
  // zero on the hour still render in 12-hour, not as ``--:--``.
  const m = (time24 || "").trim().match(/^(\d{1,2}):(\d{2})(?::\d{2})?$/);
  if (!m) return "--:--";
  const hour = Number(m[1]);
  const minute = m[2];
  if (Number.isNaN(hour) || hour < 0 || hour > 23) return "--:--";
  const suffix = hour >= 12 ? "PM" : "AM";
  const hour12 = hour % 12 || 12;
  return `${String(hour12).padStart(2, "0")}:${minute} ${suffix}`;
}

export function formatShiftTo12Hour(value: string) {
  const normalized = normalizeShift(value);
  if (!normalized || !normalized.includes("-")) return "";
  // Lenient split-and-format: handles ``HH:mm-HH:mm`` (canonical),
  // ``H:mm-HH:mm`` (legacy no-leading-zero), and ``HH:mm:ss-HH:mm:ss``
  // (rare seconds variant). We deliberately do NOT fall back to the raw
  // 24-hour string — operators must never see 24-hour in display contexts.
  const [startRaw, endRaw] = normalized.split("-");
  const start12 = to12Hour(startRaw);
  const end12 = to12Hour(endRaw);
  if (start12 === "--:--" && end12 === "--:--") return "";
  return `${start12} - ${end12}`;
}

export function ShiftTimingPicker({
  value,
  onChange,
  startLabel = "Start Time",
  endLabel = "End Time",
}: ShiftTimingPickerProps) {
  const normalized = normalizeShift(value);
  const [startRaw, endRaw] = normalized.includes("-") ? normalized.split("-") : ["", ""];
  const start = /^\d{2}:\d{2}$/.test(startRaw) ? startRaw : "";
  const end = /^\d{2}:\d{2}$/.test(endRaw) ? endRaw : "";

  const parse24To12 = (time24: string): { hour: string; minute: string; period: "AM" | "PM" } => {
    const match = time24.match(/^([01]\d|2[0-3]):([0-5]\d)$/);
    if (!match) return { hour: "12", minute: "00", period: "AM" };
    const hour24 = Number(match[1]);
    const minute = match[2];
    const period: "AM" | "PM" = hour24 >= 12 ? "PM" : "AM";
    const hour12 = hour24 % 12 || 12;
    return { hour: String(hour12).padStart(2, "0"), minute, period };
  };

  const to24Hour = (hour12: string, minute: string, period: "AM" | "PM"): string => {
    const h = Number(hour12);
    if (Number.isNaN(h) || h < 1 || h > 12) return "00:00";
    const normalizedHour = period === "AM" ? (h === 12 ? 0 : h) : (h === 12 ? 12 : h + 12);
    return `${String(normalizedHour).padStart(2, "0")}:${minute}`;
  };

  const startParts = parse24To12(start || "00:00");
  const endParts = parse24To12(end || "00:00");
  const [startInput, setStartInput] = useState(`${startParts.hour}:${startParts.minute}`);
  const [endInput, setEndInput] = useState(`${endParts.hour}:${endParts.minute}`);

  const sanitizeTime12 = (raw: string): string => {
    const digits = raw.replace(/\D/g, "").slice(0, 4);
    if (digits.length === 0) return "";
    if (digits.length <= 2) return digits;
    return `${digits.slice(0, 2)}:${digits.slice(2, 4)}`;
  };

  const normalizeTypedTime12 = (raw: string): string | null => {
    const match = raw.trim().match(/^(\d{1,2})(?::?([0-5]\d))$/);
    if (!match) return null;
    const h = Number(match[1]);
    const m = match[2];
    if (Number.isNaN(h) || h < 1 || h > 12) return null;
    return `${String(h).padStart(2, "0")}:${m}`;
  };

  const updateShift = (nextStart: string, nextEnd: string) => {
    onChange(`${nextStart || "00:00"}-${nextEnd || "00:00"}`);
  };

  useEffect(() => {
    setStartInput(`${startParts.hour}:${startParts.minute}`);
  }, [startParts.hour, startParts.minute]);

  useEffect(() => {
    setEndInput(`${endParts.hour}:${endParts.minute}`);
  }, [endParts.hour, endParts.minute]);

  const valid = isValidShift(`${start}-${end}`);
  const showInvalid = Boolean(start && end) && !valid;

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label className="text-xs font-medium text-slate-600">{startLabel}</Label>
          <div className="grid grid-cols-[1fr_auto] gap-2">
            <Input
              className="h-10 rounded-md border border-input bg-background px-2 text-sm"
              value={startInput}
              placeholder="hh:mm"
              onChange={(event) =>
                setStartInput(sanitizeTime12(event.target.value))
              }
              onBlur={(event) => {
                const normalized = normalizeTypedTime12(event.target.value);
                if (!normalized) return;
                updateShift(
                  to24Hour(normalized.split(":")[0], normalized.split(":")[1], startParts.period),
                  end || "00:00",
                );
              }}
            />
            <select
              className="h-10 rounded-md border border-input bg-background px-2 text-sm"
              value={startParts.period}
              onChange={(event) =>
                updateShift(
                  to24Hour(startParts.hour, startParts.minute, event.target.value as "AM" | "PM"),
                  end || "00:00",
                )
              }
            >
              <option value="AM">AM</option>
              <option value="PM">PM</option>
            </select>
          </div>
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs font-medium text-slate-600">{endLabel}</Label>
          <div className="grid grid-cols-[1fr_auto] gap-2">
            <Input
              className="h-10 rounded-md border border-input bg-background px-2 text-sm"
              value={endInput}
              placeholder="hh:mm"
              onChange={(event) =>
                setEndInput(sanitizeTime12(event.target.value))
              }
              onBlur={(event) => {
                const normalized = normalizeTypedTime12(event.target.value);
                if (!normalized) return;
                updateShift(
                  start || "00:00",
                  to24Hour(normalized.split(":")[0], normalized.split(":")[1], endParts.period),
                );
              }}
            />
            <select
              className="h-10 rounded-md border border-input bg-background px-2 text-sm"
              value={endParts.period}
              onChange={(event) =>
                updateShift(
                  start || "00:00",
                  to24Hour(endParts.hour, endParts.minute, event.target.value as "AM" | "PM"),
                )
              }
            >
              <option value="AM">AM</option>
              <option value="PM">PM</option>
            </select>
          </div>
        </div>
      </div>
      {showInvalid ? (
        <p className="text-xs text-destructive">End time must be after start time.</p>
      ) : null}
    </div>
  );
}
