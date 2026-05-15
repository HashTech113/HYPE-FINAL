// Thin wire layer for the /api/unknowns endpoints.
//
// Why a self-contained file (not reusing dashboardApi's authFetch):
// keeps the unknowns feature drop-in / drop-out without touching the
// existing dashboard API helper. The Bearer-token + 401 handling is
// short enough that duplicating it is cheaper than exporting internals
// from dashboardApi.ts and risking unrelated callers depending on them.

import { getAuthToken, signOut } from "@/lib/auth";
import type {
  PromoteResponse,
  PromoteToNewPayload,
  PurgeRequest,
  PurgeResponse,
  UnknownCluster,
  UnknownClusterDetail,
  UnknownClusterListResponse,
  UnknownClusterStatus,
} from "@/lib/types/unknowns";

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
  return expectJson<PromoteResponse>(resp, "promoteToNewEmployee");
}

export async function promoteToExistingEmployee(
  clusterId: number,
  employeeId: string,
): Promise<PromoteResponse> {
  const resp = await authFetch(
    buildUrl(
      `/api/unknowns/clusters/${clusterId}/promote/existing/${encodeURIComponent(employeeId)}`,
    ),
    { method: "POST" },
  );
  return expectJson<PromoteResponse>(resp, "promoteToExistingEmployee");
}

export async function purgeUnknowns(req: PurgeRequest = {}): Promise<PurgeResponse> {
  const resp = await authFetch(buildUrl("/api/unknowns/purge"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return expectJson<PurgeResponse>(resp, "purgeUnknowns");
}
