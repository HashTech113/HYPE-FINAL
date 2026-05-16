import { getAuthToken, signOut } from "@/lib/auth";

const FACE_API_BASE =
  (import.meta as unknown as { env?: { VITE_API_BASE_URL?: string } }).env?.VITE_API_BASE_URL ??
  "http://localhost:8001";

/** Backend fetch with Authorization: Bearer attached. On 401 we clear the
 * stale session so the next route guard bounces to /login — otherwise the
 * UI would silently show empty data.
 *
 * In-flight dedup: when multiple components mount at once and each calls
 * the same GET (e.g. several panels all want /api/cameras), we coalesce
 * them into one network request. The kept ``Response`` is internal and
 * EVERY caller (first or coalesced) receives its own ``.clone()`` —
 * never the original. That way one caller calling ``.json()`` can't
 * race with another caller still trying to ``.clone()``: each clone
 * has its own independent body stream. Non-GET requests bypass dedup
 * since they're not idempotent. */
const _inFlight = new Map<string, Promise<Response>>();

async function authFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const token = getAuthToken();
  const headers = new Headers(init.headers ?? {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const method = (init.method ?? "GET").toUpperCase();
  const isDedupable = method === "GET" && !init.body;

  // Dedup key includes auth so a token rotation doesn't reuse an
  // unauthenticated response.
  const dedupKey = isDedupable ? `${method} ${input} ${token ?? "anon"}` : "";

  let fetchPromise = isDedupable ? _inFlight.get(dedupKey) : undefined;
  if (!fetchPromise) {
    fetchPromise = (async () => {
      const response = await fetch(input, { ...init, headers });
      if (response.status === 401) signOut();
      return response;
    })();
    if (isDedupable) {
      _inFlight.set(dedupKey, fetchPromise);
      // Clear when the underlying fetch settles, regardless of how
      // the caller awaits or whether they consume the body.
      fetchPromise.finally(() => {
        if (_inFlight.get(dedupKey) === fetchPromise) {
          _inFlight.delete(dedupKey);
        }
      });
    }
  }

  const shared = await fetchPromise;
  // ALWAYS return a clone — even the first caller. The original
  // ``shared`` Response is kept internally and never exposed, so no
  // caller can consume its body and break another caller's ``clone()``.
  return shared.clone();
}

export type Employee = {
  id: string;
  name: string;
  employeeId: string;
  imageUrl?: string;
  company: string;
  department: string;
  shift: string;
  role: "Admin" | "Employee";
  /** Legacy field — kept on the type for older callers, but the EmployeeForm
   * no longer collects it. Default to empty string when constructing. */
  password?: string;
  dob: string;
  /** Optional on the type for backward compat with old mock data; the
   * EmployeeForm always sends a string (possibly empty). */
  email?: string;
  mobile?: string;
  salaryPackage?: string;
};

export type PresenceRecord = {
  id: string;
  employeeName: string;
  employeeId: string;
  entryTime: string;
  exitTime: string | null;
  totalHours: string;
  status: "Present" | "Late" | "Early Exit" | "Absent";
  date: string;
};

export type HolidayCalendarEntry = {
  id: string;
  date: string;
  day: string;
  name: string;
  type: "Public Holiday" | "Company Holiday" | "Weekly Off";
};

export type Request = {
  id: string;
  employeeName: string;
  employeeId: string;
  type: "Leave (Annual)" | "Leave (Sick)" | "Attendance Correction" | "Shift Change";
  message: string;
  date: string;
  status: "Pending" | "Approved" | "Denied";
};

export type Alert = {
  id: string;
  type: "warning" | "critical" | "info";
  title: string;
  description: string;
  timestamp: string;
  employee?: string;
};

export type AlertRules = {
  lateThreshold: number;
  earlyExitThreshold: number;
  multipleExitsThreshold: number;
  afterHoursStart: string;
  afterHoursEnd: string;
};

export type MovementDatum = {
  day: string;
  primary: number;
  secondary: number;
};

export type OverviewData = {
  summary: {
    totalEmployees: { value: number; change: string };
    presentToday: { value: number; change: string };
    leaveToday: { value: number; change: string };
    lateToday: { value: number; change: string };
  };
  attendanceSegments: Array<{ label: string; value: number; color: string }>;
  pendingRequests: Array<{ title: string; time: string }>;
  charts: {
    spentIn: MovementDatum[];
    spentOut: MovementDatum[];
    averagePresent: MovementDatum[];
    averageAbsent: MovementDatum[];
  };
};

export type DashboardApiResponse = {
  overview: OverviewData;
  employees: Employee[];
  presenceHistory: PresenceRecord[];
  holidayCalendar: HolidayCalendarEntry[];
  requests: Request[];
  alerts: Alert[];
  alertRules: AlertRules;
};

let dashboardDataPromise: Promise<DashboardApiResponse> | null = null;

async function loadDashboardData(): Promise<DashboardApiResponse> {
  if (!dashboardDataPromise) {
    dashboardDataPromise = fetch("/mock-api/dashboard.json").then(async (response) => {
      if (!response.ok) {
        throw new Error(`Failed to load mock dashboard data: ${response.status}`);
      }
      return response.json() as Promise<DashboardApiResponse>;
    });
  }

  return dashboardDataPromise;
}

export async function getOverviewData() {
  const data = await loadDashboardData();
  return data.overview;
}

export async function getEmployees(): Promise<Employee[]> {
  const resp = await authFetch(buildUrl("/api/employees", {}));
  if (!resp.ok) throw new Error(`getEmployees ${resp.status}`);
  const payload = (await resp.json()) as { items: Employee[] };
  return Array.isArray(payload.items) ? payload.items : [];
}

export async function createEmployeeRemote(employee: Employee): Promise<Employee> {
  const resp = await authFetch(buildUrl("/api/employees", {}), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(employee),
  });
  if (!resp.ok) throw new Error(`createEmployee ${resp.status}`);
  return (await resp.json()) as Employee;
}

export async function updateEmployeeRemote(id: string, patch: Partial<Employee>): Promise<Employee> {
  const resp = await authFetch(buildUrl(`/api/employees/${encodeURIComponent(id)}`, {}), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!resp.ok) throw new Error(`updateEmployee ${resp.status}`);
  return (await resp.json()) as Employee;
}

export async function deleteEmployeeRemote(id: string): Promise<void> {
  const resp = await authFetch(buildUrl(`/api/employees/${encodeURIComponent(id)}`, {}), {
    method: "DELETE",
  });
  if (!resp.ok && resp.status !== 404) throw new Error(`deleteEmployee ${resp.status}`);
}

export type Company = {
  id: number;
  name: string;
  employeeCount: number;
  hasUsers: boolean;
  // Optional HR account info — present when this company has an HR user
  // linked. ``hrUserId`` is the target for the reset-password / rename
  // actions on the Edit Companies row.
  hrUserId?: string | null;
  hrUsername?: string | null;
  hrUserActive?: boolean | null;
};

async function readErrorDetail(resp: Response, fallback: string): Promise<string> {
  try {
    const body = (await resp.json()) as { detail?: unknown };
    if (typeof body?.detail === "string" && body.detail.trim()) return body.detail;
  } catch {
    // not JSON — fall through to the generic message
  }
  return `${fallback} (${resp.status})`;
}

export async function getCompanies(): Promise<Company[]> {
  const resp = await authFetch(buildUrl("/api/companies", {}));
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "getCompanies"));
  const data = (await resp.json()) as { items: Company[] };
  return data.items ?? [];
}

export async function renameCompany(id: number, name: string): Promise<Company> {
  const resp = await authFetch(buildUrl(`/api/companies/${id}`, {}), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "renameCompany"));
  return (await resp.json()) as Company;
}

export async function deleteCompany(id: number): Promise<void> {
  const resp = await authFetch(buildUrl(`/api/companies/${id}`, {}), {
    method: "DELETE",
  });
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "deleteCompany"));
}

export type FaceImage = {
  id: number;
  employeeId: string;
  label: string;
  imageUrl: string;
  createdBy?: string | null;
  createdAt: string;
  embeddingId?: number | null;
  embeddingError?: string | null;
  qualityScore?: number | null;
};

/** Per-employee training-set summary returned alongside the image list
 * (and after enroll / full-retrain). Drives the inline "Already
 * Trained / Partially Trained / Not Trained" status block at the top
 * of the Face Training panel — based on actual embeddings, NOT
 * face_image rows (which can be stale stubs after the post-train
 * image_data cleanup). */
export type FaceTrainingStatus = {
  employeeId: string;
  embeddingsCount: number;
  minRequired: number;
  maxRecommended: number;
  status: "untrained" | "partial" | "trained" | "over_cap";
  atCapacity: boolean;
};

export type FaceImagesResult = {
  items: FaceImage[];
  training: FaceTrainingStatus;
};

export async function getFaceImages(employeeId: string): Promise<FaceImagesResult> {
  const resp = await authFetch(
    buildUrl(`/api/employees/${encodeURIComponent(employeeId)}/face-images`, {}),
  );
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "getFaceImages"));
  const data = (await resp.json()) as { items: FaceImage[]; training: FaceTrainingStatus };
  return { items: data.items ?? [], training: data.training };
}

/** Backend 409 response body when an upload's face matches an
 * already-trained employee. The UI surfaces this to the admin so they
 * can choose to retrain (sets ``force=true`` on the next attempt) or
 * skip. ``sameEmployee`` distinguishes "this face is already trained
 * for this person" from "you've selected the wrong employee". */
export type DuplicateFaceDetail = {
  matchedEmployeeId: string;
  matchedName: string;
  score: number;
  sameEmployee: boolean;
  message: string;
};

export class DuplicateFaceError extends Error {
  readonly detail: DuplicateFaceDetail;
  constructor(detail: DuplicateFaceDetail) {
    super(detail.message);
    this.name = "DuplicateFaceError";
    this.detail = detail;
  }
}

/** 409 when the per-employee embedding cap is reached. Frontend offers
 * "Replace Weakest" or "Full Retrain" instead of silently appending. */
export type AtCapacityDetail = {
  embeddingsCount: number;
  maxRecommended: number;
  message: string;
};

export class AtCapacityError extends Error {
  readonly detail: AtCapacityDetail;
  constructor(detail: AtCapacityDetail) {
    super(detail.message);
    this.name = "AtCapacityError";
    this.detail = detail;
  }
}

/** 409 returned by mode=replace_weakest when the new image's quality
 * is lower than the worst already-stored embedding — backend refuses
 * to silently overwrite a better photo with a worse one. */
export class QualityLowerError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "QualityLowerError";
  }
}

/** 422 when the uploaded image fails the training quality gate (no
 * face / multiple faces / too small / detector score too low). Has a
 * uniform user-facing message; the specific reason lives in server
 * logs. */
export class BadImageError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "BadImageError";
  }
}

export async function addFaceImage(
  employeeId: string,
  image: string,
  label = "",
  options: { force?: boolean; mode?: "add" | "replace_weakest" } = {},
): Promise<FaceImage> {
  // ``force=true`` is sent only after the admin confirms a duplicate-
  // face warning. ``mode=replace_weakest`` is sent only after the admin
  // confirms a "this employee is already trained — retrain?" prompt.
  // Both are absent on first attempt so the safe defaults stay in
  // charge of the happy path.
  const query: Record<string, string> = {};
  if (options.force) query.force = "true";
  if (options.mode && options.mode !== "add") query.mode = options.mode;
  const resp = await authFetch(
    buildUrl(`/api/employees/${encodeURIComponent(employeeId)}/face-images`, query),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image, label }),
    },
  );
  // Structured error parsing — backend returns one of:
  //   422 bad_image       → BadImageError
  //   409 duplicate_face  → DuplicateFaceError
  //   409 at_capacity     → AtCapacityError
  //   409 quality_lower   → QualityLowerError
  if (resp.status === 422 || resp.status === 409) {
    let body: { detail?: Record<string, unknown> } | null = null;
    try { body = (await resp.json()) as { detail?: Record<string, unknown> }; } catch { /* not JSON */ }
    const d = body?.detail as Record<string, unknown> | undefined;
    const code = typeof d?.code === "string" ? d.code : "";
    const message = typeof d?.message === "string" ? d.message : "";
    if (resp.status === 422 && code === "bad_image") {
      throw new BadImageError(message || "Image not suitable for training.");
    }
    if (code === "duplicate_face") {
      throw new DuplicateFaceError({
        matchedEmployeeId: String(d?.matched_employee_id ?? ""),
        matchedName: String(d?.matched_name ?? ""),
        score: typeof d?.score === "number" ? d.score : 0,
        sameEmployee: Boolean(d?.same_employee),
        message: message || "This face is already trained.",
      });
    }
    if (code === "at_capacity") {
      throw new AtCapacityError({
        embeddingsCount: typeof d?.embeddings_count === "number" ? d.embeddings_count : 0,
        maxRecommended: typeof d?.max_recommended === "number" ? d.max_recommended : 6,
        message: message || "This employee is already trained.",
      });
    }
    if (code === "quality_lower") {
      throw new QualityLowerError(
        message || "Image quality is lower than the existing trained faces.",
      );
    }
  }
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "addFaceImage"));
  return (await resp.json()) as FaceImage;
}

export async function deleteFaceImage(id: number): Promise<void> {
  const resp = await authFetch(buildUrl(`/api/face-images/${id}`, {}), {
    method: "DELETE",
  });
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "deleteFaceImage"));
}

export type FaceEnrollSummary = {
  employeeId: string;
  accepted: number;
  rejected: number;
  total: number;
  items: FaceImage[];
  training: FaceTrainingStatus;
};

export async function enrollFaceImages(employeeId: string): Promise<FaceEnrollSummary> {
  const resp = await authFetch(
    buildUrl(`/api/employees/${encodeURIComponent(employeeId)}/face-images/enroll`, {}),
    { method: "POST" },
  );
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "enrollFaceImages"));
  return (await resp.json()) as FaceEnrollSummary;
}

export type FullRetrainSummary = {
  employeeId: string;
  deletedEmbeddings: number;
  accepted: number;
  rejected: number;
  items: FaceImage[];
  training: FaceTrainingStatus;
};

/** Replace EVERY embedding for one employee with a fresh batch.
 * Backend validates the entire batch up front; if any image fails the
 * quality gate the whole call is rejected (so partial retrains can't
 * leave the employee in a worse state than before). */
export async function fullRetrainFaceImages(
  employeeId: string,
  images: { image: string; label?: string }[],
): Promise<FullRetrainSummary> {
  const resp = await authFetch(
    buildUrl(`/api/employees/${encodeURIComponent(employeeId)}/face-images/full-retrain`, {}),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        images: images.map((i) => ({ image: i.image, label: i.label ?? "" })),
      }),
    },
  );
  if (resp.status === 422) {
    let body: { detail?: Record<string, unknown> } | null = null;
    try { body = (await resp.json()) as { detail?: Record<string, unknown> }; } catch { /* not JSON */ }
    const d = body?.detail as Record<string, unknown> | undefined;
    const code = typeof d?.code === "string" ? d.code : "";
    const message = typeof d?.message === "string" ? d.message : "";
    if (code === "bad_image") {
      throw new BadImageError(message || "Image not suitable for training.");
    }
    if (code === "too_few_images" || code === "too_many_images") {
      throw new Error(message);
    }
  }
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "fullRetrainFaceImages"));
  return (await resp.json()) as FullRetrainSummary;
}

export type CaptureFromCameraPayload = {
  cameraId: string;
  label?: string;
  maxFrameAgeSeconds?: number;
};

export async function captureFaceFromCamera(
  employeeId: string,
  payload: CaptureFromCameraPayload,
): Promise<FaceImage> {
  const resp = await authFetch(
    buildUrl(`/api/employees/${encodeURIComponent(employeeId)}/face-images/capture`, {}),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "captureFaceFromCamera"));
  return (await resp.json()) as FaceImage;
}

export type AdminUser = {
  id: string;
  username: string;
  role: "admin" | "hr";
  company: string;
  displayName: string;
  isActive: boolean;
};

export type AdminUserCreate = {
  username: string;
  role: "admin" | "hr";
  company: string;
  displayName: string;
  password?: string;
};

export type AdminUserUpdate = Partial<{
  username: string;
  role: "admin" | "hr";
  company: string;
  displayName: string;
  isActive: boolean;
}>;

export async function getAdminUsers(): Promise<AdminUser[]> {
  const resp = await authFetch(buildUrl("/api/admin/users", {}));
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "getAdminUsers"));
  const data = (await resp.json()) as { items: AdminUser[] };
  return data.items ?? [];
}

export async function createAdminUser(
  payload: AdminUserCreate,
): Promise<AdminUser & { generatedPassword: string | null }> {
  const resp = await authFetch(buildUrl("/api/admin/users", {}), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "createAdminUser"));
  return (await resp.json()) as AdminUser & { generatedPassword: string | null };
}

export async function updateAdminUser(
  id: string,
  patch: AdminUserUpdate,
): Promise<AdminUser> {
  const resp = await authFetch(buildUrl(`/api/admin/users/${encodeURIComponent(id)}`, {}), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "updateAdminUser"));
  return (await resp.json()) as AdminUser;
}

export async function resetAdminUserPassword(
  id: string,
  password: string,
): Promise<AdminUser> {
  const resp = await authFetch(
    buildUrl(`/api/admin/users/${encodeURIComponent(id)}/reset-password`, {}),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    },
  );
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "resetAdminUserPassword"));
  return (await resp.json()) as AdminUser;
}

export type SnapshotStats = {
  tables: Record<string, { rows: number; rowsWithImage: number; approxBytes: number }>;
  totalRows: number;
  totalRowsWithImage: number;
  totalBytes: number;
  oldestImageTimestamp: string | null;
};

export async function getSnapshotStats(): Promise<SnapshotStats> {
  const resp = await authFetch(buildUrl("/api/admin/snapshots/stats", {}));
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "getSnapshotStats"));
  return (await resp.json()) as SnapshotStats;
}

export async function purgeSnapshotsBefore(beforeDate: string): Promise<{
  status: string;
  before_date: string;
  cleared: Record<string, number>;
}> {
  const resp = await authFetch(
    buildUrl("/api/admin/snapshots/purge", { before_date: beforeDate }),
    { method: "DELETE" },
  );
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "purgeSnapshotsBefore"));
  return await resp.json();
}

export type ReportKind = "summary" | "range" | "daily";

/** Download an attendance report as .xlsx. Triggers the browser save dialog
 * by streaming the bytes through a temporary anchor click. */
export async function downloadAttendanceXlsx(
  kind: ReportKind,
  params: Record<string, string>,
): Promise<void> {
  const path = `/api/reports/${kind}.xlsx`;
  const resp = await authFetch(buildUrl(path, params));
  if (!resp.ok) throw new Error(await readErrorDetail(resp, "downloadAttendanceXlsx"));

  const filename =
    parseFilenameFromContentDisposition(resp.headers.get("content-disposition")) ??
    `attendance-${kind}.xlsx`;

  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function parseFilenameFromContentDisposition(header: string | null): string | null {
  if (!header) return null;
  const match = /filename\*?=(?:UTF-8'')?["']?([^"';]+)["']?/i.exec(header);
  return match ? decodeURIComponent(match[1]) : null;
}

export async function getPresenceHistory() {
  const data = await loadDashboardData();
  return data.presenceHistory;
}

export async function getHolidayCalendar() {
  const data = await loadDashboardData();
  return data.holidayCalendar;
}

export async function getRequests() {
  const data = await loadDashboardData();
  return data.requests;
}

export async function getAlerts() {
  const data = await loadDashboardData();
  return data.alerts;
}

export async function getAlertRules() {
  const data = await loadDashboardData();
  return data.alertRules;
}

export type FaceHistoryItem = {
  id: string;
  name: string;
  entry: string;
  exit: string;
  image_url: string;
};

export type FaceHistoryResponse = {
  count: number;
  total: number;
  limit: number;
  offset: number;
  items: FaceHistoryItem[];
};

export type AttendanceStatus = "Present" | "Late" | "Early Exit" | "Absent";

export type AttendanceShiftConfig = {
  start: string;
  end: string;
  late_grace_min: number;
  early_exit_grace_min: number;
  timezone_offset_minutes: number;
};

export type AttendanceDayItem = {
  name: string;
  date: string;
  entry: string | null;
  exit: string | null;
  entry_iso: string | null;
  exit_iso: string | null;
  total_hours: string;
  total_minutes: number;
  status: AttendanceStatus;
  late_minutes: number;
  early_exit_minutes: number;
  capture_count: number;
  entry_image_url: string | null;
  exit_image_url: string | null;
};

export type AttendanceDayResponse = {
  date: string;
  shift: AttendanceShiftConfig;
  count: number;
  items: AttendanceDayItem[];
};

export async function getFaceHistory(params: {
  start?: string;
  end?: string;
  limit?: number;
  offset?: number;
  latest?: number;
} = {}): Promise<FaceHistoryResponse> {
  const search = new URLSearchParams();
  if (params.start) search.set("start", params.start);
  if (params.end) search.set("end", params.end);
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  if (params.latest !== undefined) search.set("latest", String(params.latest));

  const qs = search.toString();
  const url = `${FACE_API_BASE}/api/faces/history${qs ? `?${qs}` : ""}`;

  const response = await authFetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load face history: ${response.status}`);
  }
  return response.json() as Promise<FaceHistoryResponse>;
}

export async function getDailyAttendance(params: {
  date?: string;
  names?: string;
} = {}): Promise<AttendanceDayResponse> {
  const search = new URLSearchParams();
  if (params.date) search.set("date", params.date);
  if (params.names) search.set("names", params.names);

  const qs = search.toString();
  const url = `${FACE_API_BASE}/api/attendance/daily${qs ? `?${qs}` : ""}`;

  const response = await authFetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load attendance: ${response.status}`);
  }
  return response.json() as Promise<AttendanceDayResponse>;
}

export type SnapshotLogItem = {
  id: number;
  name: string;
  company: string | null;
  timestamp: string;
  image_url: string;
  /** Empty string for legacy single-camera or pre-multi-camera snapshots;
   * populated with the cameras.id once the camera is connected via admin UI. */
  camera_id?: string;
};

export type SnapshotLogResponse = {
  items: SnapshotLogItem[];
};

export type AttendanceBreakInterval = {
  break_out: string;
  break_in: string;
  break_out_iso: string;
  break_in_iso: string;
  duration_seconds: number;
  duration: string;
};

export type AttendanceMovementEvent = {
  event_id: string;
  movement_type: string;
  timestamp: string;
  timestamp_iso: string;
  snapshot_url: string | null;
  snapshot_archived: boolean;
  camera_id?: string | null;
  camera_name?: string | null;
  confidence?: number | null;
};

export type AttendanceStatusFull =
  | "Present"
  | "Late"
  | "Early Exit"
  | "Absent"
  | "WFH"
  | "Paid Leave"
  | "LOP"
  | "Holiday";

export type AttendanceSummaryItem = {
  id: string;
  name: string;
  company: string | null;
  date: string;
  entry_time: string | null;
  exit_time: string | null;
  late_entry_minutes: number;
  late_entry_seconds: number;
  early_exit_minutes: number;
  early_exit_seconds: number;
  status: AttendanceStatusFull;
  total_hours: string;
  total_working_hours?: string;
  total_break_time?: string;
  total_break_seconds?: number;
  break_details?: AttendanceBreakInterval[];
  movement_history?: AttendanceMovementEvent[];
  entry_image_url: string | null;
  exit_image_url: string | null;
  entry_image_archived?: boolean;
  exit_image_archived?: boolean;
  missing_checkout?: boolean;
  is_active?: boolean;
  correction_applied?: boolean;
  paid_leave?: boolean;
  lop?: boolean;
  wfh?: boolean;
};

export type AttendanceSummaryResponse = {
  items: AttendanceSummaryItem[];
};

export type SnapshotQueryParams = {
  limit?: number;
  offset?: number;
  name?: string;
};

export type AttendanceQueryParams = SnapshotQueryParams & {
  start?: string;
  end?: string;
};

function buildUrl(path: string, params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return `${FACE_API_BASE}${path}${qs ? `?${qs}` : ""}`;
}

export async function getAttendanceLogs(params: AttendanceQueryParams = {}): Promise<AttendanceSummaryResponse> {
  const url = buildUrl("/api/attendance", {
    start: params.start,
    end: params.end,
    name: params.name,
    limit: params.limit,
    offset: params.offset,
  });
  const response = await authFetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load attendance: ${response.status}`);
  }
  return response.json() as Promise<AttendanceSummaryResponse>;
}

export async function getSnapshotLogs(params: SnapshotQueryParams = {}): Promise<SnapshotLogResponse> {
  const url = buildUrl("/api/snapshots", {
    name: params.name,
    limit: params.limit,
    offset: params.offset,
  });
  const response = await authFetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load snapshots: ${response.status}`);
  }
  return response.json() as Promise<SnapshotLogResponse>;
}

export type IngestLastSeen = {
  last_seen: string | null;
  seconds_ago: number | null;
  stale: boolean;
  threshold_seconds: number;
};

export async function getIngestLastSeen(): Promise<IngestLastSeen> {
  const response = await authFetch(buildUrl("/api/ingest/last-seen", {}), { cache: "no-store" });
  if (!response.ok) throw new Error(`Failed to load ingest status: ${response.status}`);
  return response.json() as Promise<IngestLastSeen>;
}

// ---- Cameras --------------------------------------------------------------

export type CameraConnectionStatus = "unknown" | "connected" | "failed";
export type CameraType = "ENTRY" | "EXIT";

export type Camera = {
  id: string;
  name: string;
  location: string;
  ip: string;
  port: number;
  username: string;
  rtsp_path: string;
  rtsp_url_preview: string;
  connection_status: CameraConnectionStatus;
  enable_face_ingest: boolean;
  auto_discovery_enabled: boolean;
  type: CameraType;
  last_known_ip: string | null;
  last_discovered_at: string | null;
  last_checked_at: string | null;
  last_check_message: string | null;
  created_at: string;
  updated_at: string;
};

export type CameraListResponse = { items: Camera[] };

export type CameraCheckResponse = {
  ok: boolean;
  message: string;
  latency_ms: number;
};

export type CameraCreatePayload = {
  name: string;
  location: string;
  ip: string;
  port: number;
  username: string;
  password: string;
  rtsp_path: string;
  enable_face_ingest?: boolean;
  auto_discovery_enabled?: boolean;
  type?: CameraType;
};

export type CameraUpdatePayload = Partial<CameraCreatePayload>;

export type CameraCheckPayload = {
  ip: string;
  port: number;
  username: string;
  password: string;
  rtsp_path: string;
};

async function jsonOrThrow<T>(resp: Response, label: string): Promise<T> {
  if (!resp.ok) {
    let detail = "";
    try {
      const body = await resp.json();
      detail = typeof body?.detail === "string" ? `: ${body.detail}` : "";
    } catch {
      // ignore parse failures, fall back to status code only
    }
    throw new Error(`${label} (${resp.status})${detail}`);
  }
  return resp.json() as Promise<T>;
}

export async function listCameras(): Promise<Camera[]> {
  const resp = await authFetch(buildUrl("/api/cameras", {}), { cache: "no-store" });
  const data = await jsonOrThrow<CameraListResponse>(resp, "Failed to load cameras");
  return data.items;
}

export async function createCamera(payload: CameraCreatePayload): Promise<Camera> {
  const resp = await authFetch(buildUrl("/api/cameras", {}), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return jsonOrThrow<Camera>(resp, "Failed to add camera");
}

export async function updateCamera(id: string, patch: CameraUpdatePayload): Promise<Camera> {
  const resp = await authFetch(buildUrl(`/api/cameras/${encodeURIComponent(id)}`, {}), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  return jsonOrThrow<Camera>(resp, "Failed to update camera");
}

export async function deleteCamera(id: string): Promise<void> {
  const resp = await authFetch(buildUrl(`/api/cameras/${encodeURIComponent(id)}`, {}), {
    method: "DELETE",
  });
  if (!resp.ok && resp.status !== 404) {
    throw new Error(`Failed to delete camera (${resp.status})`);
  }
}

export async function testCameraConnection(payload: CameraCheckPayload): Promise<CameraCheckResponse> {
  const resp = await authFetch(buildUrl("/api/cameras/check", {}), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return jsonOrThrow<CameraCheckResponse>(resp, "Connection check failed");
}

export async function recheckCamera(id: string): Promise<CameraCheckResponse> {
  const resp = await authFetch(buildUrl(`/api/cameras/${encodeURIComponent(id)}/check`, {}), {
    method: "POST",
  });
  return jsonOrThrow<CameraCheckResponse>(resp, "Connection check failed");
}

export async function getCameraStreamToken(id: string): Promise<{ token: string; expires_in: number }> {
  const resp = await authFetch(buildUrl(`/api/cameras/${encodeURIComponent(id)}/stream-token`, {}), {
    method: "POST",
  });
  return jsonOrThrow<{ token: string; expires_in: number }>(resp, "Failed to authorize stream");
}

/** Build the MJPEG URL for an <img> tag. The backend reads the token via
 * query string because <img> can't set Authorization. */
export function buildCameraStreamUrl(id: string, token: string): string {
  return `${FACE_API_BASE}/api/cameras/${encodeURIComponent(id)}/stream?token=${encodeURIComponent(token)}`;
}

export type RecognitionWorkerHealth = {
  cameraId: string;
  name: string;
  rtspUrl: string;
  running: boolean;
  connected: boolean;
  framesRead: number;
  facesDetected: number;
  matchesRecorded: number;
  secondsSinceLastFrame?: number | null;
  secondsSinceLastMatch?: number | null;
  lastError?: string | null;
  backoffSeconds: number;
};

// ---- /api/cameras/health (new, public-shape) ------------------------------

/** Live per-camera worker state from /api/cameras/health.
 *
 * The shape here mirrors the backend response 1:1 (snake_case) so the
 * React Query hook can pass it straight through without remapping. Use
 * ``last_frame_age_seconds`` (NOT ``is_running``) as the source of truth
 * for "is the camera actually live": the worker keeps heart-beating its
 * loop even while RTSP reads silently fail. */
export type CameraHealth = {
  id: string;
  name: string;
  is_running: boolean;
  last_frame_age_seconds: number | null;
  last_match_age_seconds: number | null;
  processed_frames: number;
  faces_detected: number;
  matches_recorded: number;
  last_error: string | null;
  backoff_seconds: number;
  enable_face_ingest: boolean;
  connection_status: CameraConnectionStatus;
};

export type CameraHealthListResponse = { items: CameraHealth[] };

export async function listCameraHealth(): Promise<CameraHealth[]> {
  const resp = await authFetch(buildUrl("/api/cameras/health", {}), { cache: "no-store" });
  const body = await jsonOrThrow<CameraHealthListResponse>(resp, "Failed to load camera health");
  return body.items;
}

// ---- /api/cameras/smart-probe ---------------------------------------------

export type CameraBrand = "hikvision" | "cp_plus" | "dahua" | "axis" | "generic";

export type CameraSmartProbePayload = {
  brand: CameraBrand;
  ip: string;
  port: number;
  username: string;
  password: string;
  per_attempt_timeout_s?: number;
};

export type CameraSmartProbeAttempt = {
  template_index: number;
  rtsp_path: string;
  rtsp_url_masked: string;
  ok: boolean;
  elapsed_ms: number;
  width: number | null;
  height: number | null;
  error: string | null;
};

export type CameraSmartProbeResponse = {
  ok: boolean;
  brand: CameraBrand;
  success_template_index: number | null;
  success_rtsp_path: string | null;
  width: number | null;
  height: number | null;
  elapsed_ms: number;
  attempts: CameraSmartProbeAttempt[];
  error: string | null;
};

export async function smartProbeCamera(
  payload: CameraSmartProbePayload,
): Promise<CameraSmartProbeResponse> {
  const resp = await authFetch(buildUrl("/api/cameras/smart-probe", {}), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return jsonOrThrow<CameraSmartProbeResponse>(resp, "Smart probe failed");
}

export type RecognitionWorkersHealthResponse = {
  workers: RecognitionWorkerHealth[];
  enabled: boolean;
};

export async function getRecognitionWorkersHealth(): Promise<RecognitionWorkersHealthResponse> {
  const resp = await authFetch(buildUrl("/api/recognition/workers/health", {}), {
    cache: "no-store",
  });
  return jsonOrThrow<RecognitionWorkersHealthResponse>(resp, "Failed to load worker status");
}

// ---- Attendance corrections (HR/Admin report-level edits) -----------------

export type AttendanceCorrection = {
  name: string;
  date: string;
  entry_iso: string | null;
  exit_iso: string | null;
  total_break_seconds: number | null;
  missing_checkout_resolved: boolean;
  note: string | null;
  status_override: AttendanceStatusFull | null;
  paid_leave: boolean;
  lop: boolean;
  wfh: boolean;
  updated_by: string | null;
  updated_at: string;
};

export type AttendanceCorrectionUpsert = {
  name: string;
  date: string;
  entry_iso?: string | null;
  exit_iso?: string | null;
  total_break_seconds?: number | null;
  missing_checkout_resolved?: boolean;
  note?: string | null;
  status_override?: AttendanceStatusFull | null;
  paid_leave?: boolean | null;
  lop?: boolean | null;
  wfh?: boolean | null;
};

export async function listAttendanceCorrections(params: {
  name?: string;
  start?: string;
  end?: string;
} = {}): Promise<AttendanceCorrection[]> {
  const url = buildUrl("/api/attendance/corrections", {
    name: params.name,
    start: params.start,
    end: params.end,
  });
  const resp = await authFetch(url, { cache: "no-store" });
  const data = await jsonOrThrow<{ items: AttendanceCorrection[] }>(resp, "Failed to load corrections");
  return data.items;
}

/** Window event broadcast after any attendance correction is written, so
 * other open views (Attendance History, Reports) can invalidate their cache
 * and refetch immediately instead of waiting for the next poll tick. */
export const ATTENDANCE_CORRECTION_EVENT = "attendance-dashboard:correction-changed";

function broadcastCorrectionChange(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(ATTENDANCE_CORRECTION_EVENT));
}

export async function upsertAttendanceCorrection(
  payload: AttendanceCorrectionUpsert,
): Promise<AttendanceCorrection> {
  const resp = await authFetch(buildUrl("/api/attendance/corrections", {}), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const out = await jsonOrThrow<AttendanceCorrection>(resp, "Failed to save attendance correction");
  broadcastCorrectionChange();
  return out;
}

export async function deleteAttendanceCorrection(name: string, date: string): Promise<void> {
  const resp = await authFetch(
    buildUrl("/api/attendance/corrections", { name, date }),
    { method: "DELETE" },
  );
  if (!resp.ok && resp.status !== 404) {
    throw new Error(`Failed to clear correction (${resp.status})`);
  }
  broadcastCorrectionChange();
}

// ---------------------------------------------------------------------------
// Attendance state-machine admin endpoints.
// ---------------------------------------------------------------------------

export type AttendanceEventType = "IN" | "OUT" | "BREAK_IN" | "BREAK_OUT";

export type RecomputeDayResponse = {
  employee_id: string;
  date: string;
  status: string;
  in_time: string | null;
  out_time: string | null;
  total_work_seconds: number;
  total_break_seconds: number;
  break_count: number;
  late_minutes: number;
  early_exit_minutes: number;
  is_day_closed: boolean;
};

export async function recomputeAttendanceDay(
  employeeId: string,
  date: string,
): Promise<RecomputeDayResponse> {
  const resp = await authFetch(buildUrl("/api/attendance/recompute", {}), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ employee_id: employeeId, date }),
  });
  return jsonOrThrow<RecomputeDayResponse>(resp, "Failed to recompute day");
}

export type CloseDayResponse = {
  date: string;
  closed: number;
  already_closed: number;
  no_activity: number;
  synthetic_outs: number;
};

export async function closeAttendanceDay(date: string): Promise<CloseDayResponse> {
  const resp = await authFetch(buildUrl("/api/attendance/close-day", {}), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ date }),
  });
  return jsonOrThrow<CloseDayResponse>(resp, "Failed to close day");
}

export type AttendanceEventOut = {
  id: number;
  employee_id: string | null;
  name: string;
  timestamp: string;
  event_type: AttendanceEventType;
  camera_id: string | null;
  score: number | null;
  source: string;
};

export type AttendanceEventsResponse = {
  date: string;
  count: number;
  items: AttendanceEventOut[];
};

export async function listAttendanceEvents(
  date: string,
  employeeId?: string,
): Promise<AttendanceEventsResponse> {
  const resp = await authFetch(
    buildUrl("/api/attendance/events", { date, employee_id: employeeId }),
    { cache: "no-store" },
  );
  return jsonOrThrow<AttendanceEventsResponse>(resp, "Failed to load attendance events");
}

// ---------------------------------------------------------------------------
// Live recognition — structured per-frame detections for the Live View page,
// plus the runtime-tunable thresholds shown on the Settings page.
// ---------------------------------------------------------------------------

export type LiveDetection = {
  bbox: [number, number, number, number];
  name: string;
  employee_id: string | null;
  score: number;
  matched: boolean;
};

export type LiveDetectionsResponse = {
  detections: LiveDetection[];
  captured_at: number | null;
  age_seconds: number | null;
};

export async function getCameraDetections(cameraId: string): Promise<LiveDetectionsResponse> {
  const resp = await authFetch(
    buildUrl(`/api/cameras/${encodeURIComponent(cameraId)}/detections`, {}),
    { cache: "no-store" },
  );
  if (!resp.ok) {
    throw new Error(`getCameraDetections (${resp.status})`);
  }
  return (await resp.json()) as LiveDetectionsResponse;
}

export type RecognitionConfig = {
  face_min_quality: number;
  face_match_threshold: number;
  recognize_min_face_size_px: number;
  camera_fps: number;
  cooldown_seconds: number;
};

export async function getRecognitionConfig(): Promise<RecognitionConfig> {
  const resp = await authFetch(buildUrl("/api/admin/settings/recognition", {}));
  if (!resp.ok) throw new Error(`getRecognitionConfig (${resp.status})`);
  return (await resp.json()) as RecognitionConfig;
}

export async function patchRecognitionConfig(
  patch: Partial<RecognitionConfig>,
): Promise<RecognitionConfig> {
  const resp = await authFetch(buildUrl("/api/admin/settings/recognition", {}), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!resp.ok) {
    const body = await resp.text().catch(() => "");
    throw new Error(`patchRecognitionConfig (${resp.status}) ${body.slice(0, 200)}`);
  }
  return (await resp.json()) as RecognitionConfig;
}
