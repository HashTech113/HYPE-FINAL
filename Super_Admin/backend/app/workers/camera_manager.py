from __future__ import annotations

import threading
from datetime import UTC, datetime

from app.config import get_settings
from app.core.exceptions import NotFoundError
from app.core.logger import get_logger
from app.db.session import session_scope
from app.repositories.camera_repo import CameraRepository
from app.services.cooldown_service import get_cooldown_service
from app.services.embedding_cache import EmbeddingCache
from app.services.face_service import FaceService
from app.workers.camera_worker import CameraWorker

log = get_logger(__name__)


class CameraManager:
    def __init__(
        self,
        *,
        face_service: FaceService,
        embedding_cache: EmbeddingCache,
    ) -> None:
        self._lock = threading.Lock()
        self._workers: dict[int, CameraWorker] = {}
        self._face_service = face_service
        self._embedding_cache = embedding_cache
        self._cooldown = get_cooldown_service()
        self._health_thread: threading.Thread | None = None
        self._stop_health = threading.Event()

    def _build_worker(self, camera) -> CameraWorker:  # type: ignore[no-untyped-def]
        # Singleton FaceService. Per-camera instances were tried but
        # 4 × buffalo_l still OOMs the 4 GB GTX 1050 Ti even after
        # restricting modules to detection + recognition (DML allocates
        # transient working memory per session that puts us over the
        # edge on the 4th instance). The module restriction itself
        # delivers the biggest speedup — each frame now runs through
        # 2 ONNX sessions instead of 5.
        return CameraWorker(
            camera_id=camera.id,
            camera_name=camera.name,
            rtsp_url=camera.rtsp_url,
            camera_type=camera.camera_type,
            face_service=self._face_service,
            embedding_cache=self._embedding_cache,
            cooldown_service=self._cooldown,
        )

    def start_all(self) -> None:
        with session_scope() as db:
            cameras = CameraRepository(db).list_active()

        with self._lock:
            for cam in cameras:
                if cam.id in self._workers and self._workers[cam.id].is_alive():
                    continue
                worker = self._build_worker(cam)
                worker.start()
                self._workers[cam.id] = worker
                log.info("Started worker for camera id=%s name=%s", cam.id, cam.name)

        if self._health_thread is None or not self._health_thread.is_alive():
            self._stop_health.clear()
            self._health_thread = threading.Thread(
                target=self._health_loop, name="camera-health", daemon=True
            )
            self._health_thread.start()

    def stop_all(self) -> None:
        self._stop_health.set()
        with self._lock:
            workers = list(self._workers.values())
            self._workers.clear()
        for w in workers:
            w.stop()
        for w in workers:
            w.join(timeout=5.0)
        if self._health_thread is not None:
            self._health_thread.join(timeout=2.0)
            self._health_thread = None
        log.info("All camera workers stopped")

    def restart(self, camera_id: int) -> None:
        with session_scope() as db:
            cam = CameraRepository(db).get(camera_id)
            if cam is None:
                raise NotFoundError(f"Camera {camera_id} not found")
            cam_snapshot = (cam.id, cam.name, cam.rtsp_url, cam.camera_type, cam.is_active)

        with self._lock:
            existing = self._workers.pop(camera_id, None)
        if existing is not None:
            existing.stop()
            existing.join(timeout=5.0)

        if not cam_snapshot[4]:
            log.info("Camera id=%s is inactive; not restarting", camera_id)
            return

        class _Shim:
            def __init__(self, data):
                self.id, self.name, self.rtsp_url, self.camera_type, self.is_active = data

        worker = self._build_worker(_Shim(cam_snapshot))
        worker.start()
        with self._lock:
            self._workers[camera_id] = worker
        log.info("Restarted worker for camera id=%s", camera_id)

    def get_latest_frame(self, camera_id: int, *, max_age_seconds: float = 5.0):
        with self._lock:
            worker = self._workers.get(camera_id)
        if worker is None or not worker.is_running:
            return None
        return worker.get_latest_frame(max_age_seconds=max_age_seconds)

    def get_preview_jpeg(
        self,
        camera_id: int,
        *,
        annotated: bool,
        max_age_seconds: float,
        quality: int = 80,
        max_width: int | None = None,
    ) -> bytes | None:
        """Fetch the latest frame from a camera worker, optionally draw
        bounding boxes for the most recent detections, and return JPEG
        bytes. Returns None if the camera has no recent frame.

        Uses the worker's per-(seq, annotated, max_width, quality) JPEG
        cache so concurrent viewers don't re-encode the same frame.
        """
        with self._lock:
            worker = self._workers.get(camera_id)
        if worker is None or not worker.is_running:
            return None

        snapshot = worker.get_latest_preview(max_age_seconds=max_age_seconds)
        if snapshot is None:
            return None

        from app.config import get_settings
        from app.services.preview_service import annotate_frame, encode_jpeg

        frame, detections, seq = snapshot
        effective_max_width = (
            int(max_width) if max_width is not None else int(get_settings().PREVIEW_MAX_WIDTH)
        )

        cache_key = (seq, bool(annotated), effective_max_width, int(quality))
        # Single-flight encoding. With 4 polling clients staggered every
        # ~20 ms hitting /preview.jpg, the previous lock-then-release
        # pattern let multiple cache misses for the SAME seq trigger
        # independent cv2.imencode calls — that was the felt "stutter
        # during recognition" because annotation+encode is the single
        # most expensive thing on the request path. Holding the lock
        # through encode means concurrent same-key requests collapse
        # into one encode and get the cached result; a request for a
        # *different* key (e.g. another camera) is on a different
        # worker._jpeg_cache_lock and runs in parallel.
        from app.workers.camera_worker import _PREVIEW_CACHE_MAX_ENTRIES

        with worker._jpeg_cache_lock:
            cached = worker._jpeg_cache.get(cache_key)
            if cached is not None:
                worker._jpeg_cache.move_to_end(cache_key)
                return cached
            # Cache miss — encode here under the lock so subsequent
            # waiters get the cache hit immediately when we release.
            if annotated and detections:
                frame = annotate_frame(frame, detections)
            jpeg = encode_jpeg(frame, quality=quality, max_width=effective_max_width)
            worker._jpeg_cache[cache_key] = jpeg
            worker._jpeg_cache.move_to_end(cache_key)
            while len(worker._jpeg_cache) > _PREVIEW_CACHE_MAX_ENTRIES:
                worker._jpeg_cache.popitem(last=False)
        return jpeg

    def wait_preview_jpeg(
        self,
        camera_id: int,
        *,
        last_seen_seq: int,
        annotated: bool,
        quality: int,
        max_width: int | None = None,
        max_wait_seconds: float = 1.0,
        max_age_seconds: float = 10.0,
    ) -> tuple[bytes, int] | None:
        """Block until the camera produces a frame newer than `last_seen_seq`,
        encode it (cache-aware), and return `(jpeg_bytes, new_seq)`. Returns
        None on timeout or stale buffer (camera disconnected). Used by the
        MJPEG streaming endpoint to push exactly one JPEG per fresh frame.
        """
        with self._lock:
            worker = self._workers.get(camera_id)
        if worker is None or not worker.is_running:
            return None

        from app.config import get_settings

        effective_max_width = (
            int(max_width) if max_width is not None else int(get_settings().PREVIEW_MAX_WIDTH)
        )
        return worker.encode_preview_jpeg(
            last_seen_seq=last_seen_seq,
            annotated=annotated,
            quality=quality,
            max_width=effective_max_width,
            max_wait_seconds=max_wait_seconds,
            max_age_seconds=max_age_seconds,
        )

    def status(self) -> list[dict]:
        out: list[dict] = []
        with self._lock:
            workers = dict(self._workers)
        for cam_id, w in workers.items():
            out.append(
                {
                    "camera_id": cam_id,
                    "camera_name": w.camera_name,
                    "is_running": w.is_running,
                    "last_heartbeat_age_seconds": w.last_heartbeat_age_seconds,
                    "last_frame_age_seconds": w.last_frame_age_seconds,
                    "last_detector_tick_age_seconds": w.last_detector_tick_age_seconds,
                    "processed_frames": w.stats.processed_frames,
                    "events_generated": w.stats.events_generated,
                    "auto_enrollments": w.stats.auto_enrollments,
                    "unknown_captures": w.stats.unknown_captures,
                    "unknown_skipped": w.stats.unknown_skipped,
                    "last_error": w.stats.last_error,
                    "last_heartbeat": datetime.now(tz=UTC),
                }
            )
        return out

    # How long a detector tick can stall before we consider the worker
    # deadlocked and force a restart. Longer than the worst-case
    # InsightFace inference (a few hundred ms) plus DB write (low
    # seconds) plus a generous safety margin. If real inference ever
    # legitimately exceeds this, raise the constant rather than
    # disable the watchdog — the watchdog is the only protection
    # against detector deadlock on the FaceService lock.
    _DETECTOR_STALL_TIMEOUT_SECONDS: float = 60.0

    def _health_loop(self) -> None:
        settings = get_settings()
        while not self._stop_health.wait(settings.CAMERA_HEALTH_INTERVAL_SECONDS):
            try:
                with self._lock:
                    items = list(self._workers.items())
                for cam_id, worker in items:
                    if not worker.is_alive():
                        log.warning("Worker for camera id=%s died; restarting", cam_id)
                        self.restart(cam_id)
                        continue

                    # Reader heartbeat — covers the case where the
                    # whole worker thread is wedged (detector + reader
                    # both stuck).
                    reader_age = worker.last_heartbeat_age_seconds
                    if reader_age > settings.CAMERA_HEARTBEAT_TIMEOUT_SECONDS:
                        log.warning(
                            "Worker for camera id=%s stale (reader_age=%.1fs); restarting",
                            cam_id,
                            reader_age,
                        )
                        self.restart(cam_id)
                        continue

                    # Detector heartbeat — catches the "alive but
                    # stuck" pattern where the reader keeps publishing
                    # frames (so reader_age stays low) but the
                    # detector is deadlocked on FaceService /
                    # embedding cache / DB. Without this branch the
                    # camera looks healthy from the outside while
                    # silently producing zero attendance events.
                    detector_age = worker.last_detector_tick_age_seconds
                    if detector_age > self._DETECTOR_STALL_TIMEOUT_SECONDS:
                        log.warning(
                            "Worker for camera id=%s detector stalled "
                            "(detector_age=%.1fs, reader_age=%.1fs); restarting",
                            cam_id,
                            detector_age,
                            reader_age,
                        )
                        self.restart(cam_id)
            except Exception:
                log.exception("Camera health loop error")
