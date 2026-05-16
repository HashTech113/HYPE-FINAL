// Thin wire layer for the /api/unknowns endpoints.
//
// Why a self-contained file (not reusing dashboardApi's authFetch):
// keeps the unknowns feature drop-in / drop-out without touching the
// existing dashboard API helper. The Bearer-token + 401 handling is
// short enough that duplicating it is cheaper than exporting internals
// from dashboardApi.ts and risking unrelated callers depending on them.

import { getAuthToken, signOut } from "@/lib/auth";
import type {
  PromoteErrorDetail,
  PromoteResponse,
  PromoteToExistingPayload,
  PromoteToNewPayload,
  PurgeRequest,
  PurgeResponse,
  UnknownCluster,
  UnknownClusterDetail,
  UnknownClusterListResponse,
  UnknownClusterStatus,
} from "@/lib/types/unknowns";

/** Typed error raised by promote* helpers when the backend returns a
 *  structured 4xx detail. Lets the dialog branch on ``code`` without
 *  regex-matching the message. */
export class PromoteError extends Error {
  readonly detail: PromoteErrorDetail;
  readonly status: number;
  constructor(detail: PromoteErrorDetail, status: number) {
    super(detail.message);
    this.name = "PromoteError";
    this.detail = detail;
    this.status = status;
  }
}

const API_BASE =
  (import.meta as unknown as { env?: { VITE_API_BASE_URL?: string } }).env?.VITE_API_BASE_URL ??
  "http://localhost:8000";

function buildUrl(
  path: string,
  params: Record<string, string | number | undefined> = {},
): string {
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === "") continue;
    search.set(k, String(v));
  }
  const qs = search.toString();
  return `${API_BASE}${path}${qs ? `?${qs}` : ""}`;
}

async function authFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const token = getAuthToken();
  const headers = new Headers(init.headers ?? {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const resp = await fetch(input, { ...init, headers });
  if (resp.status === 401) signOut();
  return resp;
}

async function expectJson<T>(resp: Response, label: string): Promise<T> {
  if (!resp.ok) {
    const body = await resp.text().catch(() => "");
    throw new Error(`${label} failed (${resp.status}): ${body.slice(0, 200)}`);
  }
  return (await resp.json()) as T;
}

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

export type ListClustersParams = {
  status?: UnknownClusterStatus;
  label?: string;
  limit?: number;
  offset?: number;
};

export async function listClusters(
  params: ListClustersParams = {},
): Promise<UnknownClusterListResponse> {
  const resp = await authFetch(
    buildUrl("/api/unknowns/clusters", {
      status: params.status,
      label: params.label,
      limit: params.limit,
      offset: params.offset,
    }),
  );
  return expectJson<UnknownClusterListResponse>(resp, "listClusters");
}

export async function getCluster(clusterId: number): Promise<UnknownClusterDetail> {
  const resp = await authFetch(buildUrl(`/api/unknowns/clusters/${clusterId}`));
  return expectJson<UnknownClusterDetail>(resp, "getCluster");
}

/** Fetch one capture image as a Blob — the endpoint is auth'd so a plain
 *  ``<img src=…>`` won't carry the JWT. Caller is responsible for the
 *  resulting ``URL.createObjectURL`` lifetime (the hook does the cleanup). */
export async function getCaptureImageBlob(captureId: number): Promise<Blob> {
  const resp = await authFetch(buildUrl(`/api/unknowns/captures/${captureId}/image`));
  if (!resp.ok) {
    throw new Error(`getCaptureImageBlob failed (${resp.status})`);
  }
  return resp.blob();
}

export async function deleteCapture(captureId: number): Promise<void> {
  const resp = await authFetch(buildUrl(`/api/unknowns/captures/${captureId}`), {
    method: "DELETE",
  });
  if (!resp.ok && resp.status !== 404 && resp.status !== 204) {
    const body = await resp.text().catch(() => "");
    throw new Error(`deleteCapture failed (${resp.status}): ${body.slice(0, 200)}`);
  }
}

export async function setClusterLabel(
  clusterId: number,
  label: string | null,
): Promise<UnknownCluster> {
  const resp = await authFetch(buildUrl(`/api/unknowns/clusters/${clusterId}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label }),
  });
  return expectJson<UnknownCluster>(resp, "setClusterLabel");
}

export async function discardCluster(clusterId: number): Promise<void> {
  const resp = await authFetch(buildUrl(`/api/unknowns/clusters/${clusterId}`), {
    method: "DELETE",
  });
  if (!resp.ok && resp.status !== 404 && resp.status !== 204) {
    const body = await resp.text().catch(() => "");
    throw new Error(`discardCluster failed (${resp.status}): ${body.slice(0, 200)}`);
  }
}

async function parsePromoteError(resp: Response, label: string): Promise<never> {
  let detail: PromoteErrorDetail | string | undefined;
  try {
    const body = (await resp.json()) as { detail?: unknown };
    detail = body?.detail as PromoteErrorDetail | string;
  } catch {
    /* not JSON */
  }
  // Structured detail (object with code) → typed PromoteError so the
  // dialog can branch (at_capacity → ask to Retrain, etc.).
  if (detail && typeof detail === "object" && "code" in detail) {
    throw new PromoteError(detail as PromoteErrorDetail, resp.status);
  }
  const msg = typeof detail === "string" && detail.trim() ? detail : `${label} failed (${resp.status})`;
  throw new Error(msg);
}

export async function promoteToNewEmployee(
  clusterId: number,
  payload: PromoteToNewPayload,
): Promise<PromoteResponse> {
  const resp = await authFetch(
    buildUrl(`/api/unknowns/clusters/${clusterId}/promote/new`),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  if (!resp.ok) return parsePromoteError(resp, "promoteToNewEmployee");
  return (await resp.json()) as PromoteResponse;
}

export async function promoteToExistingEmployee(
  clusterId: number,
  employeeId: string,
  payload: PromoteToExistingPayload = {},
): Promise<PromoteResponse> {
  const resp = await authFetch(
    buildUrl(
      `/api/unknowns/clusters/${clusterId}/promote/existing/${encodeURIComponent(employeeId)}`,
    ),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  if (!resp.ok) return parsePromoteError(resp, "promoteToExistingEmployee");
  return (await resp.json()) as PromoteResponse;
}

export async function purgeUnknowns(req: PurgeRequest = {}): Promise<PurgeResponse> {
  const resp = await authFetch(buildUrl("/api/unknowns/purge"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return expectJson<PurgeResponse>(resp, "purgeUnknowns");
}
