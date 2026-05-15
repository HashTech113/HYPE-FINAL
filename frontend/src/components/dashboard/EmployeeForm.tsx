import { useCallback, useEffect, useMemo, useState } from "react";
import Cropper, { type Area } from "react-easy-crop";
import { type Employee } from "@/api/dashboardApi";
import { getCurrentCompany } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SearchableSelect, type SearchableSelectOption } from "@/components/ui/searchable-select";
import { useEmployees } from "@/contexts/EmployeesContext";
import { DatePicker } from "@/components/dashboard/DatePicker";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  ShiftTimingPicker,
  isValidShift,
  normalizeShift,
} from "@/components/dashboard/ShiftTimingPicker";

export const COMPANY_OPTIONS = [
  "WAWU",
  "CAP",
  "Owlytics",
  "Grow",
  "Perform100x",
  "Study in Bengaluru",
  "career cafe co",
  "CEO Square",
  "Karu Mitra",
  "Legal Quotient",
  "Startup TV",
] as const;

const ISO_DOB_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const DMY_DOB_PATTERN = /^(\d{2})-(\d{2})-(\d{4})$/;

export function normalizeDob(value: string) {
  const trimmed = (value || "").trim();
  if (ISO_DOB_PATTERN.test(trimmed)) return trimmed;
  const dmyMatch = trimmed.match(DMY_DOB_PATTERN);
  if (!dmyMatch) return trimmed;
  const [, dd, mm, yyyy] = dmyMatch;
  return `${yyyy}-${mm}-${dd}`;
}

export function isValidDob(value: string) {
  const normalized = normalizeDob(value);
  if (!ISO_DOB_PATTERN.test(normalized)) return false;
  const [yyyy, mm, dd] = normalized.split("-").map(Number);
  if (mm < 1 || mm > 12 || dd < 1 || dd > 31) return false;
  const date = new Date(Date.UTC(yyyy, mm - 1, dd));
  return (
    date.getUTCFullYear() === yyyy &&
    date.getUTCMonth() === mm - 1 &&
    date.getUTCDate() === dd
  );
}

/** Storage is `YYYY-MM-DD`. Display/input format is `DD-MM-YYYY`. */
export function formatDobForDisplay(value: string): string {
  const normalized = normalizeDob(value);
  if (!ISO_DOB_PATTERN.test(normalized)) return "";
  const [yyyy, mm, dd] = normalized.split("-");
  return `${dd}-${mm}-${yyyy}`;
}

function parseDobFromDisplay(display: string): string {
  const trimmed = (display || "").trim();
  const match = trimmed.match(DMY_DOB_PATTERN);
  if (!match) return trimmed;
  const [, dd, mm, yyyy] = match;
  return `${yyyy}-${mm}-${dd}`;
}

function formatDobInput(raw: string): string {
  const digitsOnly = (raw || "").replace(/\D/g, "").slice(0, 8);
  const dd = digitsOnly.slice(0, 2);
  const mm = digitsOnly.slice(2, 4);
  const yyyy = digitsOnly.slice(4, 8);
  if (digitsOnly.length <= 2) return dd;
  if (digitsOnly.length <= 4) return `${dd}-${mm}`;
  return `${dd}-${mm}-${yyyy}`;
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function isValidEmail(value: string): boolean {
  return EMAIL_PATTERN.test(value.trim());
}

/** Accept any leading "+", then strip non-digits. Keep at most 12 digits
 * (country code 1–3 + 10-digit number). Auto-format as "+91 XXXXX XXXXX"
 * for the common Indian case; otherwise insert a space after the country
 * code and a space halfway through the subscriber digits. */
function formatMobileInput(raw: string): string {
  const trimmed = (raw || "").trim();
  if (!trimmed) return "";
  const digitsOnly = trimmed.replace(/\D/g, "").slice(0, 12);
  if (!digitsOnly) return "";

  // Default to +91 if the user typed only the 10-digit local number.
  if (digitsOnly.length <= 10) {
    const first = digitsOnly.slice(0, 5);
    const second = digitsOnly.slice(5, 10);
    if (digitsOnly.length <= 5) return `+91 ${first}`;
    return `+91 ${first} ${second}`;
  }

  const countryLen = digitsOnly.length - 10;
  const country = digitsOnly.slice(0, countryLen);
  const local = digitsOnly.slice(countryLen);
  const first = local.slice(0, 5);
  const second = local.slice(5, 10);
  return `+${country} ${first}${second ? ` ${second}` : ""}`;
}

function isValidMobile(value: string): boolean {
  const digits = (value || "").replace(/\D/g, "");
  // Allow 10-digit (local) up to 12-digit (country code + 10) phone numbers.
  return digits.length >= 10 && digits.length <= 12;
}

/** Default initial value for the Mobile Number input — pre-fills "+91 " so
 * the user only types the local number and never has to figure out the
 * country code. Existing rows show whatever's stored; only blank values
 * get the prefix. */
const MOBILE_PLACEHOLDER_PREFIX = "+91 ";
function initialMobileValue(stored: string | undefined): string {
  return stored && stored.trim() ? stored : MOBILE_PLACEHOLDER_PREFIX;
}

/** What to actually persist when the user submits. If they left the field
 * as just the "+91 " prefix (or any value with fewer than 3 raw digits —
 * i.e. only a country code), treat it as "no mobile entered" so the row
 * is saved as an empty string instead of a bogus "+91" entry. */
function mobileValueForSave(value: string): string {
  const trimmed = (value || "").trim();
  if (!trimmed) return "";
  const digits = trimmed.replace(/\D/g, "");
  if (digits.length < 3) return "";
  return trimmed;
}

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

type EmployeeFormProps = {
  employee: Employee;
  onSave: (employee: Employee) => void;
  onCancel?: () => void;
  saveLabel?: string;
  showCancel?: boolean;
};

export function EmployeeForm({
  employee,
  onSave,
  onCancel,
  saveLabel = "Save Changes",
  showCancel = false,
}: EmployeeFormProps) {
  // HR users are scoped to one company; their employees should always belong
  // to that company. Lock the field rather than show a dropdown.
  const scopedCompany = getCurrentCompany();
  const { employees: roster } = useEmployees();
  const [draft, setDraft] = useState<Employee>({
    ...employee,
    dob: normalizeDob(employee.dob),
    shift: normalizeShift(employee.shift),
    email: employee.email ?? "",
    mobile: initialMobileValue(employee.mobile),
    salaryPackage: employee.salaryPackage ?? "",
    company: employee.company || scopedCompany || employee.company,
  });
  const [cropSource, setCropSource] = useState<string | null>(null);
  const [cropPosition, setCropPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [cropZoom, setCropZoom] = useState<number>(1);
  const [croppedArea, setCroppedArea] = useState<Area | null>(null);
  const [cropSaving, setCropSaving] = useState<boolean>(false);

  const openCropper = useCallback((src: string) => {
    setCropSource(src);
    setCropPosition({ x: 0, y: 0 });
    setCropZoom(1);
    setCroppedArea(null);
  }, []);

  const closeCropper = useCallback(() => {
    setCropSource(null);
    setCroppedArea(null);
    setCropSaving(false);
  }, []);

  const onCropComplete = useCallback((_: Area, pixels: Area) => {
    setCroppedArea(pixels);
  }, []);

  const handleCropSave = useCallback(async () => {
    if (!cropSource || !croppedArea) return;
    try {
      setCropSaving(true);
      const dataUrl = await getCroppedDataUrl(cropSource, croppedArea);
      setDraft((prev) => ({ ...prev, imageUrl: dataUrl }));
      closeCropper();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "Failed to crop image");
      setCropSaving(false);
    }
  }, [cropSource, croppedArea, closeCropper]);

  useEffect(() => {
    setDraft({
      ...employee,
      dob: normalizeDob(employee.dob),
      shift: normalizeShift(employee.shift),
      email: employee.email ?? "",
      mobile: initialMobileValue(employee.mobile),
      salaryPackage: employee.salaryPackage ?? "",
      company: employee.company || scopedCompany || employee.company,
    });
  }, [employee, scopedCompany]);

  // Suggest companies that already exist in the roster (so admins can pick
  // one without typo risk) plus the legacy curated list. The form still
  // accepts brand-new company names via the SearchableSelect's creatable
  // mode — the backend auto-creates the row in the `companies` table on
  // first use of a new name (services/employees.py → get_or_create_company_id).
  const companySuggestions: SearchableSelectOption[] = useMemo(() => {
    const seen = new Set<string>();
    const out: SearchableSelectOption[] = [];
    const push = (raw: string) => {
      const value = (raw || "").trim();
      if (!value) return;
      const key = value.toLowerCase();
      if (seen.has(key)) return;
      seen.add(key);
      out.push({ value, label: value });
    };
    for (const emp of roster) push(emp.company);
    for (const name of COMPANY_OPTIONS) push(name);
    if (draft.company) push(draft.company);
    out.sort((a, b) => a.label.localeCompare(b.label));
    return out;
  }, [roster, draft.company]);

  const handleSave = () => {
    if (!draft.name.trim()) {
      window.alert("Full Name is required.");
      return;
    }
    if (!draft.employeeId.trim()) {
      window.alert("Employee ID is required.");
      return;
    }
    // DOB is optional. Only enforce a format check when the user entered/kept
    // a value — when editing an employee the backend roster doesn't store DOB
    // (not in the schema), so `draft.dob` is often empty and should save fine.
    // DatePicker always emits strict YYYY-MM-DD (or "" on partial selection),
    // so there's no longer any DD-MM-YYYY handling here.
    const normalizedDob = normalizeDob(draft.dob);
    if (normalizedDob && !isValidDob(normalizedDob)) {
      window.alert("Please select a valid Date of Birth (Month / Day / Year).");
      return;
    }
    if (!isValidShift(draft.shift)) {
      window.alert("Shift Timing is invalid — pick a start and end time, with end after start.");
      return;
    }
    const trimmedEmail = (draft.email ?? "").trim();
    if (trimmedEmail && !isValidEmail(trimmedEmail)) {
      window.alert("Please enter a valid Email ID (e.g., name@example.com).");
      return;
    }
    // mobileValueForSave returns "" when the user left the field as just
    // the "+91 " prefix (no real subscriber digits) — that way blank
    // mobiles round-trip as empty strings, not as the bogus "+91".
    const mobileForSave = mobileValueForSave(draft.mobile ?? "");
    if (mobileForSave && !isValidMobile(mobileForSave)) {
      window.alert("Please enter a valid Mobile Number (10-digit local or with country code).");
      return;
    }
    onSave({
      ...draft,
      dob: normalizedDob,
      shift: normalizeShift(draft.shift),
      email: trimmedEmail,
      mobile: mobileForSave,
    });
  };

  const handleImageFileChange = (file: File | null) => {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      window.alert("Please choose a valid image file.");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const value = typeof reader.result === "string" ? reader.result : "";
      if (value) openCropper(value);
    };
    reader.onerror = () => {
      window.alert("Failed to read the selected image.");
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Full Name</Label>
          <Input value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
        </div>
        <div className="space-y-2">
          <Label>Employee ID</Label>
          <Input value={draft.employeeId} onChange={(e) => setDraft({ ...draft, employeeId: e.target.value })} />
        </div>
        <div className="col-span-2 space-y-2">
          <Label>Employee Image</Label>
          <div className="flex items-center gap-3">
            <Input
              type="file"
              accept="image/*"
              className="min-w-0 flex-1"
              onChange={(e) => handleImageFileChange(e.target.files?.[0] ?? null)}
            />
            {draft.imageUrl ? (
              <>
                <button
                  type="button"
                  onClick={() => draft.imageUrl && openCropper(draft.imageUrl)}
                  className="h-14 w-14 shrink-0 overflow-hidden rounded-md border border-slate-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                  title="Crop image"
                >
                  <img
                    src={draft.imageUrl}
                    alt={`${draft.name || "Employee"} profile`}
                    className="h-full w-full object-cover"
                  />
                </button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="shrink-0"
                  onClick={() => setDraft((prev) => ({ ...prev, imageUrl: "" }))}
                >
                  Remove
                </Button>
              </>
            ) : (
              <div className="h-14 w-14 shrink-0 rounded-md border border-dashed border-slate-300 bg-slate-50" />
            )}
          </div>
        </div>
        <div className="space-y-2">
          <Label>Email ID</Label>
          <Input
            type="email"
            inputMode="email"
            autoComplete="email"
            value={draft.email ?? ""}
            placeholder="name@example.com"
            onChange={(e) => setDraft({ ...draft, email: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label>Mobile Number</Label>
          <Input
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            value={draft.mobile ?? ""}
            placeholder="+91"
            // Don't reformat on every keystroke — that breaks backspace
            // (the country-code inference treated the digit being deleted
            // as part of the prefix and produced garbled "+9 19876…"
            // strings). Format once on blur instead, so editing in the
            // middle of the value works naturally.
            onChange={(e) => setDraft({ ...draft, mobile: e.target.value })}
            onBlur={(e) =>
              setDraft({ ...draft, mobile: formatMobileInput(e.target.value) })
            }
          />
        </div>
        <div className="space-y-2">
          <Label>Company</Label>
          {scopedCompany ? (
            // HR is locked to their own company; show the value as a disabled
            // input so it's visually obvious it can't be changed.
            <Input value={draft.company} disabled />
          ) : (
            <SearchableSelect
              value={draft.company}
              options={companySuggestions}
              creatable
              placeholder="Select a company or type a new one"
              createLabel={(q) => `Add new company "${q}"`}
              onValueChange={(value) => setDraft({ ...draft, company: value })}
            />
          )}
        </div>
        <div className="space-y-2">
          <Label>Employee Role</Label>
          <Input
            value={draft.department}
            placeholder="e.g., Software Engineer"
            onChange={(e) => setDraft({ ...draft, department: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label>Date of Birth</Label>
          <DatePicker
            value={normalizeDob(draft.dob)}
            onChange={(next) => setDraft({ ...draft, dob: normalizeDob(next) })}
            minYear={1900}
            maxYear={2100}
            className="w-full"
          />
        </div>
        <div className="space-y-2">
          <Label>Salary Package</Label>
          <Input
            value={draft.salaryPackage ?? ""}
            placeholder="e.g., 50000"
            onChange={(e) => setDraft({ ...draft, salaryPackage: e.target.value })}
          />
        </div>
        <div className="col-span-2 space-y-2">
          <Label>Shift Timing</Label>
          <ShiftTimingPicker
            value={draft.shift}
            onChange={(nextShift) => setDraft({ ...draft, shift: nextShift })}
          />
        </div>
      </div>
      <div className="flex justify-end gap-2 pt-2">
        {showCancel && onCancel ? (
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        ) : null}
        <Button onClick={handleSave}>{saveLabel}</Button>
      </div>

      <Dialog
        open={cropSource !== null}
        onOpenChange={(open) => {
          if (!open) closeCropper();
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Crop Image</DialogTitle>
          </DialogHeader>
          {cropSource ? (
            <div className="space-y-3">
              <div className="relative h-64 w-full overflow-hidden rounded-lg bg-slate-900">
                <Cropper
                  image={cropSource}
                  crop={cropPosition}
                  zoom={cropZoom}
                  aspect={1}
                  cropShape="round"
                  showGrid={false}
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
              </div>
            </div>
          ) : null}
          <DialogFooter>
            <Button variant="outline" onClick={closeCropper} disabled={cropSaving}>
              Cancel
            </Button>
            <Button onClick={handleCropSave} disabled={!croppedArea || cropSaving}>
              {cropSaving ? "Saving…" : "Save Crop"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
