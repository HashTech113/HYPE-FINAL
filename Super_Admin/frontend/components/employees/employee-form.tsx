"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ImagePlus, Loader2, Trash2, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { employeesApi } from "@/lib/api/employees";
import type { Employee, EmployeeCreate, EmployeeUpdate } from "@/lib/types/employee";
import { cn } from "@/lib/utils";

// --- Zod schema -----------------------------------------------------------
//
// All visible fields go through this schema. `image` is intentionally not
// present — image upload is a separate side-channel (POST multipart) so a
// 5 MB JPEG never bloats the JSON form payload, and so the upload error
// path can be surfaced independently of field-validation errors.
//
// `salary_package` is kept as a string in the form layer (HTML number
// inputs return strings) and converted to a normalized decimal string
// in the submit handler. We never use JS `number` for money.
const _timeRegex = /^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/;

const formSchema = z
  .object({
    company: z.string().trim().min(1, "Company is required").max(128),
    designation: z.string().trim().min(1, "Role is required").max(128),
    name: z.string().trim().min(1, "Name is required").max(128),
    email: z
      .string()
      .trim()
      .max(128)
      .optional()
      .or(z.literal(""))
      .transform((v) => (v ? v : undefined))
      .refine(
        (v) => v === undefined || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v),
        "Invalid email",
      ),
    phone: z.string().trim().max(32).optional().or(z.literal("")),
    department: z.string().trim().max(128).optional().or(z.literal("")),
    dob: z.string().optional().or(z.literal("")),
    join_date: z.string().optional().or(z.literal("")),
    salary_package: z
      .string()
      .trim()
      .optional()
      .or(z.literal(""))
      .refine(
        (v) => !v || /^\d+(\.\d{1,2})?$/.test(v),
        "Enter a valid amount (max 2 decimals)",
      ),
    // HTML <input type="time"> always returns 24-hour "HH:mm". We also
    // accept "HH:mm:ss" for round-trip safety with the backend.
    shift_start: z
      .string()
      .optional()
      .or(z.literal(""))
      .refine((v) => !v || _timeRegex.test(v), "Invalid time"),
    shift_end: z
      .string()
      .optional()
      .or(z.literal(""))
      .refine((v) => !v || _timeRegex.test(v), "Invalid time"),
    is_active: z.boolean(),
  })
  .refine(
    // Either both shift endpoints are set, or neither.
    (v) => (!!v.shift_start && !!v.shift_end) || (!v.shift_start && !v.shift_end),
    {
      message: "Set both shift start and end, or leave both empty",
      path: ["shift_end"],
    },
  );

type FormValues = z.infer<typeof formSchema>;

interface BaseProps {
  submitting: boolean;
  onCancel: () => void;
}

interface CreateProps extends BaseProps {
  mode: "create";
  onSubmit: (values: EmployeeCreate) => void;
  initial?: undefined;
}
interface EditProps extends BaseProps {
  mode: "edit";
  onSubmit: (values: EmployeeUpdate) => void;
  initial: Employee;
}

type Props = CreateProps | EditProps;

function toUndef(v: string | undefined | null): string | undefined {
  return v && v.length > 0 ? v : undefined;
}

// "HH:mm" or "HH:mm:ss" → "HH:mm:ss" (so the server gets a consistent
// format and we don't have to teach the API to parse two flavors).
function normalizeTime(v: string | undefined): string | undefined {
  const u = toUndef(v);
  if (!u) return undefined;
  return u.length === 5 ? `${u}:00` : u;
}

// "HH:mm:ss" or "HH:mm" coming from the server → "HH:mm" so an
// <input type="time"> displays it correctly.
function trimTimeForInput(v: string | null | undefined): string {
  if (!v) return "";
  return v.slice(0, 5);
}

// "50000.00" / null → form-friendly string. We don't reformat with
// thousands separators because <input type="number"> rejects them.
function salaryToInput(v: string | null | undefined): string {
  if (v === null || v === undefined || v === "") return "";
  const n = Number(v);
  return Number.isFinite(n) ? n.toString() : "";
}

export function EmployeeForm(props: Props) {
  const isCreate = props.mode === "create";

  // --- Form state -------------------------------------------------------
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: isCreate
      ? blankDefaults()
      : initialDefaults(props.initial),
  });

  useEffect(() => {
    if (!isCreate) {
      form.reset(initialDefaults(props.initial));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isCreate ? null : props.initial.id]);

  const errors = form.formState.errors;

  // --- Image side-channel -----------------------------------------------
  // The image lives behind a token-protected endpoint, so we fetch it as
  // a Blob and use an object URL. This also lets us cleanly revoke the
  // URL when the dialog closes / a new image is staged for upload.
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageDirty, setImageDirty] = useState(false); // staged but not yet uploaded
  const [pendingImageFile, setPendingImageFile] = useState<File | null>(null);
  const [imageBusy, setImageBusy] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Load the initial image (edit mode only) once, and clean up on unmount.
  useEffect(() => {
    let revoke: string | null = null;
    if (!isCreate && props.initial.has_image) {
      // Cache-bust on `updated_at` so a fresh upload immediately replaces
      // the stale browser-cached thumbnail.
      employeesApi
        .loadImage(props.initial.id)
        .then((url) => {
          revoke = url;
          setImagePreview(url);
        })
        .catch(() => {
          // 404 / network error — silently drop the avatar; the row
          // already had image_path cleared on the server side, so the
          // next refresh will reflect that.
          setImagePreview(null);
        });
    } else {
      setImagePreview(null);
    }
    return () => {
      if (revoke) URL.revokeObjectURL(revoke);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isCreate ? null : props.initial.id, isCreate ? null : props.initial.updated_at]);

  function onPickFile(file: File | null) {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      toast.error("Please choose an image file");
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      toast.error("Image must be 8 MB or smaller");
      return;
    }
    // Stage locally; actual upload happens on submit (create) or
    // immediately (edit) — see handleSubmit.
    if (imagePreview && imageDirty) URL.revokeObjectURL(imagePreview);
    const url = URL.createObjectURL(file);
    setImagePreview(url);
    setPendingImageFile(file);
    setImageDirty(true);
  }

  async function uploadStagedImage(employeeId: number) {
    if (!pendingImageFile) return;
    setImageBusy(true);
    try {
      await employeesApi.uploadImage(employeeId, pendingImageFile);
      setPendingImageFile(null);
      setImageDirty(false);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Image upload failed");
    } finally {
      setImageBusy(false);
    }
  }

  async function removeImage() {
    if (isCreate) {
      // Just clear local staging.
      if (imagePreview) URL.revokeObjectURL(imagePreview);
      setImagePreview(null);
      setPendingImageFile(null);
      setImageDirty(false);
      return;
    }
    setImageBusy(true);
    try {
      await employeesApi.deleteImage(props.initial.id);
      if (imagePreview) URL.revokeObjectURL(imagePreview);
      setImagePreview(null);
      setPendingImageFile(null);
      setImageDirty(false);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not remove image");
    } finally {
      setImageBusy(false);
    }
  }

  // --- Submit -----------------------------------------------------------
  async function handleSubmit(values: FormValues) {
    const payload = {
      company: values.company.trim(),
      designation: values.designation.trim(),
      name: values.name.trim(),
      dob: toUndef(values.dob),
      email: toUndef(values.email),
      phone: toUndef(values.phone),
      department: toUndef(values.department),
      join_date: toUndef(values.join_date),
      salary_package: toUndef(values.salary_package),
      shift_start: normalizeTime(values.shift_start),
      shift_end: normalizeTime(values.shift_end),
      is_active: values.is_active,
    };

    if (isCreate) {
      // We can't upload an image until the row exists. Hand the
      // payload up; the parent will create, then call back with the
      // new id — but our existing dialog doesn't do that. Compromise:
      // show a tip telling the user to set the photo from the row's
      // edit dialog after creation. Avoids redesigning the dialog
      // wiring for a marginal UX gain.
      if (pendingImageFile) {
        toast.info("Save the new employee first, then attach a photo by editing the row.");
      }
      (props.onSubmit as (v: EmployeeCreate) => void)(payload);
    } else {
      (props.onSubmit as (v: EmployeeUpdate) => void)(payload);
      if (pendingImageFile) {
        await uploadStagedImage(props.initial.id);
      }
    }
  }

  // --- UI ---------------------------------------------------------------
  return (
    <form
      onSubmit={form.handleSubmit(handleSubmit)}
      className="space-y-5"
      noValidate
    >
      {/* Profile image + employee code (read-only, edit mode only). */}
      <div className="flex items-start gap-4">
        <div className="relative h-24 w-24 shrink-0 overflow-hidden rounded-lg border border-border bg-muted">
          {imagePreview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={imagePreview}
              alt="Profile"
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-muted-foreground">
              <User className="h-9 w-9" />
            </div>
          )}
          {imageBusy && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/60">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          )}
        </div>
        <div className="flex flex-col gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="sr-only"
            onChange={(e) => onPickFile(e.target.files?.[0] ?? null)}
          />
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={props.submitting || imageBusy}
            >
              <ImagePlus className="mr-1.5 h-4 w-4" />
              {imagePreview ? "Replace photo" : "Upload photo"}
            </Button>
            {imagePreview && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={removeImage}
                disabled={props.submitting || imageBusy}
              >
                <Trash2 className="mr-1.5 h-4 w-4" />
                Remove
              </Button>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            JPEG / PNG / WEBP / HEIC, up to 8 MB. We re-encode and resize to 1024 px.
          </p>
          {!isCreate && (
            <p className="text-xs text-muted-foreground">
              Employee ID:{" "}
              <span className="font-mono font-medium text-foreground">
                {props.initial.employee_code}
              </span>
            </p>
          )}
        </div>
      </div>

      {/* Identity */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Name" required error={errors.name?.message}>
          <Input
            placeholder="Asha Kumar"
            {...form.register("name")}
            disabled={props.submitting}
          />
        </Field>
        <Field label="Email" error={errors.email?.message}>
          <Input
            type="email"
            placeholder="asha@example.com"
            {...form.register("email")}
            disabled={props.submitting}
          />
        </Field>
        <Field label="Phone" error={errors.phone?.message}>
          <Input
            placeholder="+91 98765 43210"
            {...form.register("phone")}
            disabled={props.submitting}
          />
        </Field>
        <Field label="Date of birth" error={errors.dob?.message}>
          <Input
            type="date"
            {...form.register("dob")}
            disabled={props.submitting}
          />
        </Field>

        {/* Org */}
        <Field label="Company" required error={errors.company?.message}>
          <Input
            placeholder="Acme Pvt Ltd"
            {...form.register("company")}
            disabled={props.submitting}
          />
        </Field>
        <Field label="Role" required error={errors.designation?.message}>
          <Input
            placeholder="Senior Engineer"
            {...form.register("designation")}
            disabled={props.submitting}
          />
        </Field>
        <Field label="Department" error={errors.department?.message}>
          <Input
            placeholder="Engineering"
            {...form.register("department")}
            disabled={props.submitting}
          />
        </Field>
        <Field label="Join date" error={errors.join_date?.message}>
          <Input
            type="date"
            {...form.register("join_date")}
            disabled={props.submitting}
          />
        </Field>

        {/* Compensation + shift */}
        <Field label="Salary package (annual)" error={errors.salary_package?.message}>
          <div className="relative">
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
              ₹
            </span>
            <Input
              type="number"
              inputMode="decimal"
              step="0.01"
              min="0"
              placeholder="900000.00"
              className="pl-7 tabular-nums"
              {...form.register("salary_package")}
              disabled={props.submitting}
            />
          </div>
        </Field>
        <Field
          label="Shift timing"
          error={errors.shift_start?.message ?? errors.shift_end?.message}
        >
          <div className="flex items-center gap-2">
            <Input
              type="time"
              step={60}
              {...form.register("shift_start")}
              disabled={props.submitting}
              aria-label="Shift start"
            />
            <span className="shrink-0 text-sm text-muted-foreground">to</span>
            <Input
              type="time"
              step={60}
              {...form.register("shift_end")}
              disabled={props.submitting}
              aria-label="Shift end"
            />
          </div>
        </Field>

        <Field label="Status">
          <label className="mt-2 flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-input accent-primary"
              {...form.register("is_active")}
              disabled={props.submitting}
            />
            Active
          </label>
        </Field>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button
          type="button"
          variant="outline"
          onClick={props.onCancel}
          disabled={props.submitting || imageBusy}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={props.submitting || imageBusy}>
          {(props.submitting || imageBusy) && (
            <Loader2 className="h-4 w-4 animate-spin" />
          )}
          {isCreate ? "Create employee" : "Save changes"}
        </Button>
      </div>
    </form>
  );
}

// --- Helpers --------------------------------------------------------------

function blankDefaults(): FormValues {
  return {
    company: "",
    designation: "",
    name: "",
    email: "",
    phone: "",
    department: "",
    dob: "",
    join_date: "",
    salary_package: "",
    shift_start: "",
    shift_end: "",
    is_active: true,
  };
}

function initialDefaults(emp: Employee): FormValues {
  return {
    company: emp.company ?? "",
    designation: emp.designation ?? "",
    name: emp.name,
    email: emp.email ?? "",
    phone: emp.phone ?? "",
    department: emp.department ?? "",
    dob: emp.dob ?? "",
    join_date: emp.join_date ?? "",
    salary_package: salaryToInput(emp.salary_package),
    shift_start: trimTimeForInput(emp.shift_start),
    shift_end: trimTimeForInput(emp.shift_end),
    is_active: emp.is_active,
  };
}

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
      <Label className={cn(required && "after:ml-0.5 after:text-destructive after:content-['*']")}>
        {label}
      </Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
