import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createCamera,
  deleteCamera,
  listCameraHealth,
  listCameras,
  recheckCamera,
  smartProbeCamera,
  testCameraConnection,
  updateCamera,
  type Camera,
  type CameraCheckPayload,
  type CameraCreatePayload,
  type CameraHealth,
  type CameraSmartProbePayload,
  type CameraUpdatePayload,
} from "@/api/dashboardApi";

/** React Query key factory for the cameras feature. Co-located so any
 * mutation can invalidate the right scope without copy-pasting strings. */
export const cameraKeys = {
  all: ["cameras"] as const,
  list: ["cameras", "list"] as const,
  health: ["cameras", "health"] as const,
};

export function useCameras() {
  return useQuery<Camera[]>({
    queryKey: cameraKeys.list,
    queryFn: () => listCameras(),
  });
}

/** Poll the per-worker health endpoint. ``refetchMs`` defaults to 5 s —
 * matches the Super_Admin reference cadence and is fast enough to make
 * "Live" / "Stalled" badges feel responsive without hammering the API.
 *
 * ``refetchIntervalInBackground: false`` (the React Query default) means
 * the poll pauses when the browser tab is hidden — saving backend CPU
 * and freeing browser connection slots so navigating back to the page
 * feels snappy. */
export function useCamerasHealth(refetchMs: number | false = 5_000) {
  return useQuery<CameraHealth[]>({
    queryKey: cameraKeys.health,
    queryFn: () => listCameraHealth(),
    refetchInterval: refetchMs === false ? undefined : refetchMs,
    refetchIntervalInBackground: false,
  });
}

export function useCreateCamera() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CameraCreatePayload) => createCamera(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: cameraKeys.all });
    },
  });
}

export function useUpdateCamera() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: CameraUpdatePayload }) =>
      updateCamera(id, patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: cameraKeys.all });
    },
  });
}

export function useDeleteCamera() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteCamera(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: cameraKeys.all });
    },
  });
}

export function useRecheckCamera() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => recheckCamera(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: cameraKeys.all });
    },
  });
}

/** Single-URL pre-save check — same shape as before, wrapped so the form
 * can keep its async state in a mutation instead of ad-hoc useState. */
export function useTestCameraConnection() {
  return useMutation({
    mutationFn: (payload: CameraCheckPayload) => testCameraConnection(payload),
  });
}

/** Multi-template smart probe. The mutation's result carries the winning
 * ``success_rtsp_path`` (when ok) plus a per-attempt audit trail the
 * form renders in a collapsible panel. */
export function useSmartProbeCamera() {
  return useMutation({
    mutationFn: (payload: CameraSmartProbePayload) => smartProbeCamera(payload),
  });
}
