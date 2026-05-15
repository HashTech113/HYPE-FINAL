from __future__ import annotations

import gc
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field

import numpy as np

from app.core.constants import CameraType
from app.core.logger import get_logger
from app.db.session import session_scope
from app.services.attendance_service import AttendanceService
from app.services.cooldown_service import CooldownService
from app.services.embedding_cache import EmbeddingCache
from app.services.event_queue import get_pool
from app.services.face_service import DetectedFace, FaceService
from app.services.recognition_service import MatchResult, RecognitionService
from app.services.settings_service import get_settings_service
from app.services.training_service import TrainingService
from app.services.unknown_capture_service import UnknownCaptureService
from app.utils.time_utils import now_utc
from app.workers.rtsp_reader import RTSPReader

log = get_logger(__name__)

# Floor on the detection interval. Operators tune the cadence via the
# `camera_fps` setting (read fresh on every detector tick), but at high
# camera_fps values we still don't want to spin the GIL re-acquiring
# the FaceService lock with no useful work — 0.05s caps detection at
# 20 fps even if camera_fps is set absurdly high.
_DETECTION_INTERVAL_FLOOR_SECONDS: float = 0.05

# How long (seconds) to keep the last non-empty bounding-box overlay on
# screen after the detector stops finding faces.  Without this, boxes
# vanish on the very next tick where motion blur / angle shift causes a
# missed detection — making them flash too fast to see.
_DETECTION_HOLD_SECONDS: float = 1.5

# Per-worker JPEG cache size. Cache key = (seq, annotated, max_width, quality).
# Big enough to hold ~1 second of seq history (12.8 fps × 2 variants =
# ~26 entries) so polling clients staggered up to a second apart still
# share encoded bytes instead of each triggering a fresh encode.
# 32 entries × ~50 KB JPEG ≈ 1.6 MB per camera × 4 cameras = 6.4 MB total.
_PREVIEW_CACHE_MAX_ENTRIES: int = 32
# How many seqs of history to keep when the reader publishes a new
# frame. Was 1 (drop everything older than current-1) which thrashed
# the cache at 12.8 fps. Keeping the last 16 means polling clients
# fetching slightly stale seqs still hit cache.
_PREVIEW_CACHE_KEEP_SEQS: int = 16

# Periodic GC inside the worker. Defends against slow OpenCV / numpy ref
# cycles that the gen-2 collector takes a long time to spot. Runs once per
# minute on a per-worker timer; trivially cheap.
_GC_INTERVAL_SECONDS: float = 60.0


@dataclass
class WorkerStats:
    processed_frames: int = 0
    events_generated: int = 0
    auto_enrollments: int = 0
    unknown_captures: int = 0
    unknown_skipped: int = 0
    # Reader-loop heartbeat. Stays fresh whenever cv2.read() returns,
    # which it can do even when subsequent recognition deadlocks. NOT a
    # complete liveness signal on its own.
    last_heartbeat: float = field(default_factory=time.monotonic)
    # Detector-loop heartbeat. Updated at the top of every detector
    # iteration. The camera_manager health loop watches this — if it
    # stops advancing while the reader heartbeat is still ticking, the
    # detector is deadlocked (typically on the FaceService lock) and
    # the worker needs a restart even though "the camera is fine".
    last_detector_tick: float = field(default_factory=time.monotonic)
    last_error: str | None = None


@dataclass(frozen=True)
class FrameDetection:
    """One face detected in the most recent frame, with its match result.

    Used by the live preview endpoint to render bounding boxes + labels on
    top of the frame. Populated each tick alongside `_latest_frame`.
    """

    bbox: tuple[int, int, int, int]
    label: str  # employee name when matched; "Unknown" otherwise
    score: float  # cosine similarity (0..1) — best score even when unmatched
    matched: bool  # True iff `score >= face_match_threshold`


class CameraWorker(threading.Thread):
    def __init__(
        self,
        *,
        camera_id: int,
        camera_name: str,
        rtsp_url: str,
        camera_type: CameraType,
        face_service: FaceService,
        embedding_cache: EmbeddingCache,
        cooldown_service: CooldownService,
    ) -> None:
        super().__init__(name=f"cam-{camera_id}-{camera_name}", daemon=True)
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.camera_type = camera_type
        self.face_service = face_service
        self.embedding_cache = embedding_cache
        self.cooldown = cooldown_service
        self.recognition = RecognitionService(embedding_cache)
        self.reader = RTSPReader(rtsp_url, name=camera_name)
        self._stop_event = threading.Event()
        self.stats = WorkerStats()

        # Single Condition guards the latest-frame buffer + sequence and
        # also wakes both the detector and any number of MJPEG producers
        # the instant a new frame is published. A Condition (vs a single
        # Event) lets every waiter wake on each notify_all and re-check
        # the seq independently — no consumer can starve another by
        # `clear()`-ing a shared Event.
        self._frame_cv = threading.Condition()
        self._latest_frame: np.ndarray | None = None
        self._latest_frame_at: float = 0.0
        self._latest_frame_seq: int = 0  # incremented on every reader update
        self._latest_detections: list[FrameDetection] = []
        self._last_nonempty_detections: list[FrameDetection] = []
        self._last_nonempty_det_at: float = 0.0
        # Detector wake signal — kept as an Event so the detector can also
        # be poked by the worker shutdown path without holding the cv.
        self._frame_event = threading.Event()
        self._detector_thread: threading.Thread | None = None

        # LRU JPEG cache. Encoding the same frame for N concurrent MJPEG
        # viewers used to cost N×imencode; cache key (seq, annotated,
        # max_width, quality) means each variant is encoded at most once
        # per fresh frame and shared by reference to all subscribers.
        self._jpeg_cache_lock = threading.Lock()
        self._jpeg_cache: OrderedDict[tuple[int, bool, int, int], bytes] = OrderedDict()
        self._last_gc_at: float = time.monotonic()

    @property
    def is_running(self) -> bool:
        return self.is_alive() and not self._stop_event.is_set()

    @property
    def last_heartbeat_age_seconds(self) -> float:
        """Time since the worker's loop body last ran. Stays low whenever
        the worker isn't deadlocked — even if every RTSP read is silently
        failing. NOT a reliable 'camera is streaming' signal — use
        `last_frame_age_seconds` for that.
        """
        return max(0.0, time.monotonic() - self.stats.last_heartbeat)

    @property
    def last_detector_tick_age_seconds(self) -> float:
        """Time since the detector loop last completed an iteration —
        whether or not it produced an event. Stays low while inference
        is running normally; grows without bound if the detector
        deadlocks on a shared lock (FaceService, embedding cache mutex,
        etc.). Health loop watches this: a high detector-tick age with
        a fresh reader heartbeat is the unambiguous "alive but stuck"
        signature that justifies a worker restart.
        """
        return max(0.0, time.monotonic() - self.stats.last_detector_tick)

    @property
    def last_frame_age_seconds(self) -> float | None:
        """Time since the most recent frame was successfully read from
        the RTSP stream. `None` until the very first frame arrives. When
        this grows past a few seconds, the camera is not actually
        streaming — show 'Reconnecting' / 'Stale', not 'Live'.
        """
        with self._frame_cv:
            if self._latest_frame is None or self._latest_frame_at <= 0.0:
                return None
            return max(0.0, time.monotonic() - self._latest_frame_at)

    def stop(self) -> None:
        self._stop_event.set()
        self._frame_event.set()  # wake detector so it can exit
        # Wake any blocked MJPEG producers so they can return None and
        # exit their loops cleanly instead of waiting out their timeout.
        with self._frame_cv:
            self._frame_cv.notify_all()
        self.reader.stop()

    def _set_latest_frame(
        self,
        frame: np.ndarray,
        detections: list[FrameDetection] | None = None,
    ) -> None:
        """Replace both frame and detections. Used when detection ran for this
        frame (so the boxes are exactly synced to it). Stores the frame by
        reference; `RTSPReader.read()` already returned a fresh copy and we
        never mutate it in place.
        """
        with self._frame_cv:
            self._latest_frame = frame
            self._latest_frame_at = time.monotonic()
            self._latest_detections = list(detections or [])
            self._latest_frame_seq += 1
            self._frame_cv.notify_all()
        self._invalidate_jpeg_cache_keep(self._latest_frame_seq)
        self._frame_event.set()

    def _set_latest_frame_only(self, frame: np.ndarray) -> None:
        """Update just the frame (preserve last detections) — fast path
        used to keep the live preview at the camera's read rate even when
        face detection is rate-limited to a lower cadence.

        Detections from up to ~_DETECTION_INTERVAL_SECONDS ago are still
        drawn on the new frame. Box positions visibly lag the face by the
        detection interval; this is the standard trade-off real CCTV
        previews make and is much better than a stuttering feed.

        The frame is stored by reference (no copy) since `RTSPReader.read()`
        already returned a fresh ndarray; doubling that copy used to be the
        single largest memcpy cost on the hot path.
        """
        with self._frame_cv:
            self._latest_frame = frame
            self._latest_frame_at = time.monotonic()
            self._latest_frame_seq += 1
            new_seq = self._latest_frame_seq
            self._frame_cv.notify_all()
        self._invalidate_jpeg_cache_keep(new_seq)
        self._frame_event.set()

    def _take_frame_for_detection(self, last_seen_seq: int) -> tuple[np.ndarray, int] | None:
        """Detector helper: return the freshest frame if it's newer than
        the seq the detector last processed, else None. Always returns
        the absolute latest — older frames are skipped, never queued, so
        the detector never falls behind the reader.

        We DO copy here because the detector mutates working buffers
        (face crops, embedding inputs) and may hold onto the frame while
        the reader publishes a new one.
        """
        with self._frame_cv:
            if self._latest_frame is None:
                return None
            if self._latest_frame_seq <= last_seen_seq:
                return None
            return self._latest_frame.copy(), self._latest_frame_seq

    def _set_latest_detections(self, detections: list[FrameDetection]) -> None:
        """Update only the detections list — paired with `_set_latest_frame_only`
        when detection runs at a slower cadence than frame reads.

        When the detector finds no faces on the current tick but had faces
        recently, the previous boxes are held on screen for up to
        ``_DETECTION_HOLD_SECONDS`` so the overlay doesn't flash on/off
        with each intermittent missed detection (motion blur, angle shift).
        """
        now = time.monotonic()
        if detections:
            self._last_nonempty_detections = list(detections)
            self._last_nonempty_det_at = now
            effective = detections
        elif (now - self._last_nonempty_det_at) < _DETECTION_HOLD_SECONDS:
            # Hold the previous boxes a little longer.
            effective = self._last_nonempty_detections
        else:
            effective = []
            self._last_nonempty_detections = []
        with self._frame_cv:
            self._latest_detections = list(effective)
            self._latest_frame_seq += 1
            new_seq = self._latest_frame_seq
            self._frame_cv.notify_all()
        # Detections refresh changes the rendered overlay; existing JPEGs
        # for older seqs are still valid, but the new seq must be re-rendered.
        self._invalidate_jpeg_cache_keep(new_seq)

    def get_latest_frame(self, *, max_age_seconds: float = 5.0) -> np.ndarray | None:
        with self._frame_cv:
            if self._latest_frame is None:
                return None
            if time.monotonic() - self._latest_frame_at > max_age_seconds:
                return None
            return self._latest_frame.copy()

    def get_latest_preview(
        self, *, max_age_seconds: float = 10.0
    ) -> tuple[np.ndarray, list[FrameDetection], int] | None:
        """Latest frame + per-face detections + seq for rendering an
        annotated preview. Returns None if there's no frame yet or it's
        too stale.
        """
        with self._frame_cv:
            if self._latest_frame is None:
                return None
            if time.monotonic() - self._latest_frame_at > max_age_seconds:
                return None
            return (
                self._latest_frame.copy(),
                list(self._latest_detections),
                self._latest_frame_seq,
            )

    def wait_for_preview(
        self,
        *,
        last_seen_seq: int,
        max_wait_seconds: float = 1.0,
        max_age_seconds: float = 10.0,
    ) -> tuple[np.ndarray, list[FrameDetection], int] | None:
        """Block (Condition.wait — no polling) until the buffer holds a
        frame newer than `last_seen_seq`, then return
        `(frame, detections, new_seq)`. Returns None on timeout or when the
        latest frame is older than `max_age_seconds` (camera disconnected).

        Multi-consumer safe: any number of MJPEG producers can wait
        concurrently; each one wakes on the next published frame and
        independently re-checks `seq`. There is no shared Event to clear.
        """
        deadline = time.monotonic() + max_wait_seconds
        with self._frame_cv:
            while self._latest_frame is None or self._latest_frame_seq <= last_seen_seq:
                if self._stop_event.is_set():
                    return None
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                self._frame_cv.wait(timeout=remaining)
            if time.monotonic() - self._latest_frame_at > max_age_seconds:
                return None
            return (
                self._latest_frame.copy(),
                list(self._latest_detections),
                self._latest_frame_seq,
            )

    def encode_preview_jpeg(
        self,
        *,
        last_seen_seq: int,
        annotated: bool,
        quality: int,
        max_width: int,
        max_wait_seconds: float = 2.0,
        max_age_seconds: float = 10.0,
    ) -> tuple[bytes, int] | None:
        """Cache-aware preview encoder.

        Waits for a frame newer than `last_seen_seq`, then returns
        `(jpeg_bytes, new_seq)`. The encoded bytes are kept in a small
        per-worker LRU keyed by (seq, annotated, max_width, quality), so
        N concurrent MJPEG viewers of the same camera collapse to a
        single imencode call per fresh frame.
        """
        # Lazy import — keeps cv2 cost off the hot lifespan-startup path.
        from app.services.preview_service import annotate_frame, encode_jpeg

        snapshot = self.wait_for_preview(
            last_seen_seq=last_seen_seq,
            max_wait_seconds=max_wait_seconds,
            max_age_seconds=max_age_seconds,
        )
        if snapshot is None:
            return None
        frame, detections, new_seq = snapshot

        cache_key = (new_seq, bool(annotated), int(max_width), int(quality))
        with self._jpeg_cache_lock:
            cached = self._jpeg_cache.get(cache_key)
            if cached is not None:
                self._jpeg_cache.move_to_end(cache_key)
                return cached, new_seq

        if annotated and detections:
            frame = annotate_frame(frame, detections)
        jpeg = encode_jpeg(frame, quality=quality, max_width=max_width)

        with self._jpeg_cache_lock:
            self._jpeg_cache[cache_key] = jpeg
            self._jpeg_cache.move_to_end(cache_key)
            while len(self._jpeg_cache) > _PREVIEW_CACHE_MAX_ENTRIES:
                self._jpeg_cache.popitem(last=False)
        return jpeg, new_seq

    def _invalidate_jpeg_cache_keep(self, current_seq: int) -> None:
        """Drop cached JPEGs older than `current_seq - _PREVIEW_CACHE_KEEP_SEQS`.

        Keeping a window (vs only the previous seq) is what lets multiple
        polling clients arriving at staggered times all hit cache instead
        of each triggering an independent cv2.imencode. The LRU cap in
        `_PREVIEW_CACHE_MAX_ENTRIES` still bounds total memory.
        """
        cutoff = current_seq - _PREVIEW_CACHE_KEEP_SEQS
        with self._jpeg_cache_lock:
            stale = [key for key in self._jpeg_cache if key[0] < cutoff]
            for key in stale:
                self._jpeg_cache.pop(key, None)

    def run(self) -> None:
        """Reader thread (the CameraWorker thread itself).

        Reads RTSP frames at `camera_fps` and writes them to the buffer.
        Heavy work (face detection / recognition / attendance / unknown
        capture) lives in a sibling detector thread so the preview keeps
        updating even when inference is busy.
        """
        next_deadline = time.monotonic()
        log.info(
            "[%s] worker starting (type=%s)",
            self.camera_name,
            self.camera_type.value,
        )

        # Spawn the sibling detector thread. It pulls the latest frame
        # from the buffer at its own pace (rate-limited by
        # _DETECTION_INTERVAL_SECONDS) so reads never block on inference.
        self._detector_thread = threading.Thread(
            target=self._detector_loop,
            name=f"{self.name}-detect",
            daemon=True,
        )
        self._detector_thread.start()

        while not self._stop_event.is_set():
            now = time.monotonic()
            if now < next_deadline:
                self._stop_event.wait(min(0.05, next_deadline - now))
                continue
            min_interval = 1.0 / max(1, get_settings_service().get().camera_fps)
            next_deadline = now + min_interval

            try:
                frame = self.reader.read()
                self.stats.last_heartbeat = time.monotonic()
                if frame is None:
                    continue
                self._set_latest_frame_only(frame)
                self.stats.processed_frames += 1
                # Cheap once-a-minute GC pass — drops OpenCV / numpy
                # ref cycles before they accumulate into a slow leak.
                if time.monotonic() - self._last_gc_at > _GC_INTERVAL_SECONDS:
                    self._last_gc_at = time.monotonic()
                    gc.collect()
            except Exception as exc:
                self.stats.last_error = str(exc)
                log.exception("[%s] reader loop error", self.camera_name)
                self._stop_event.wait(1.0)

        # Wait for the detector to finish its in-flight tick so we don't
        # leave a pending DB transaction or InsightFace call mid-flight.
        if self._detector_thread is not None:
            self._detector_thread.join(timeout=5.0)
        self.reader.stop()
        log.info("[%s] worker stopped", self.camera_name)

    def _detector_loop(self) -> None:
        """Detection / recognition / attendance / unknown-capture loop.

        Decoupled from the reader so the live preview keeps updating at
        full `camera_fps` even while inference is busy. Always grabs the
        absolute newest frame from the buffer — never queues — so it
        can't fall behind the camera.
        """
        last_detection_at = 0.0
        last_seen_seq = 0
        while not self._stop_event.is_set():
            # Wake either when the reader signals a new frame or after a
            # short timeout so we still reach the rate-limit branch
            # promptly when frames stop arriving.
            self._frame_event.wait(timeout=0.05)
            self._frame_event.clear()
            if self._stop_event.is_set():
                break

            # Detector liveness heartbeat — must be stamped BEFORE any
            # blocking call (FaceService lock, embedding cache lock).
            # If a downstream call deadlocks, this stops advancing and
            # the camera_manager health loop kicks the worker.
            self.stats.last_detector_tick = time.monotonic()

            # Detection cadence: live-tunable from the settings table.
            # `camera_fps` defines the target detection rate; we floor
            # at _DETECTION_INTERVAL_FLOOR_SECONDS to prevent a
            # misconfiguration from melting the GPU. Reading settings
            # every tick is cheap (in-memory snapshot).
            target_fps = max(1, get_settings_service().get().camera_fps)
            interval = max(_DETECTION_INTERVAL_FLOOR_SECONDS, 1.0 / target_fps)

            now = time.monotonic()
            if (now - last_detection_at) < interval:
                continue

            taken = self._take_frame_for_detection(last_seen_seq)
            if taken is None:
                continue
            frame, last_seen_seq = taken
            last_detection_at = now

            try:
                faces = self.face_service.detect(frame)

                # Apply the runtime-tunable "close-face only" gate before
                # spending time on recognition or attendance. Faces below
                # this minimum bbox edge are kept off the recognition path
                # entirely — too small to reliably match an embedding.
                min_size = max(
                    0,
                    int(get_settings_service().get().recognize_min_face_size_px),
                )
                if min_size > 0:
                    faces = [
                        f
                        for f in faces
                        if min(f.bbox[2] - f.bbox[0], f.bbox[3] - f.bbox[1]) >= min_size
                    ]

                results: list[tuple[DetectedFace, MatchResult]] = []
                detections: list[FrameDetection] = []
                # Build the id->name dict once per detection batch so
                # each face is an O(1) lookup instead of an O(N) scan.
                name_map = self.embedding_cache.id_to_name_map()
                for face in faces:
                    match = self.recognition.match(face.embedding)
                    results.append((face, match))
                    detections.append(self._face_to_detection(face, match, name_map))

                self._set_latest_detections(detections)
                # Explicit GIL yield. Inference itself releases the GIL,
                # but the surrounding numpy/Python work in this loop holds
                # it. Yielding here lets the reader thread publish a fresh
                # frame and the polling-request workers serve cached JPEGs
                # before we run the next detection batch — keeps the live
                # tile smooth even at the moment of recognition.
                time.sleep(0)
                if not faces:
                    continue

                log.info(
                    "[%s] detected %d face(s) — %s",
                    self.camera_name,
                    len(faces),
                    ", ".join(f"{d.label}({d.score:.2f})" for d in detections),
                )

                # Hand the slow follow-up work (snapshot encode, DB write,
                # daily rollup, realtime publish, auto-enroll) to background
                # pools. The detector loop returns to its next-frame wait
                # in microseconds instead of blocking for 100–200 ms per
                # recognition. Recognized-employee events and unknown-face
                # captures use SEPARATE pools so a flood of unknowns (many
                # unenrolled people on camera) cannot starve attendance
                # writes — each pool has its own queue and worker threads.
                attendance_pool = get_pool("attendance")
                unknown_pool = get_pool("unknown_capture")
                # Take ONE snapshot of the frame for the whole batch of
                # faces detected in this tick. We deep-copy so the
                # background queue workers never race with the reader
                # thread overwriting the buffer in `frame` — without
                # this, a slow snapshot encode could capture the wrong
                # person's pixels (we've all seen "I clocked in but the
                # snapshot is the next person who walked past").
                frame_snapshot = frame.copy()
                for face, match in results:
                    if match.employee_id is None:
                        face_local = face
                        unknown_pool.submit(
                            lambda f=face_local, fr=frame_snapshot: self._do_capture_unknown(
                                face=f, frame=fr
                            )
                        )
                        continue
                    if not self.cooldown.allow(match.employee_id):
                        continue
                    # Snapshot all the per-face state into locals so the
                    # closure captures THIS face, not the loop's last face.
                    # Pass the full DetectedFace through so auto-enroll
                    # can reuse its embedding instead of re-detecting
                    # (which would block the detector on the FaceService
                    # lock and stall the live preview).
                    emp_id = match.employee_id
                    score = match.score
                    bbox = face.bbox
                    detected_face = face
                    at = now_utc()
                    submitted = attendance_pool.submit(
                        lambda eid=emp_id, sc=score, bb=bbox, fr=frame_snapshot, t=at, df=detected_face: (
                            self._do_attendance_event(
                                employee_id=eid,
                                score=sc,
                                bbox=bb,
                                frame_bgr=fr,
                                at_time=t,
                                detected_face=df,
                            )
                        )
                    )
                    if not submitted:
                        # Attendance pool full — let the cooldown re-allow so
                        # the next frame can re-attempt instead of silently
                        # dropping this person's event forever.
                        self.cooldown.reset(emp_id)
            except Exception as exc:
                self.stats.last_error = str(exc)
                log.exception("[%s] detector loop error", self.camera_name)
                self._stop_event.wait(0.5)

    def _face_to_detection(
        self,
        face: DetectedFace,
        match: MatchResult,
        name_map: dict[int, str],
    ) -> FrameDetection:
        """Pair a detected face with its recognition result for the
        preview overlay. Caller passes a pre-built employee_id -> name
        dict so we do exactly one O(1) lookup per face instead of
        scanning the cache snapshot per face.
        """
        if match.employee_id is None:
            return FrameDetection(
                bbox=face.bbox,
                label="Unknown",
                score=float(match.score),
                matched=False,
            )
        return FrameDetection(
            bbox=face.bbox,
            label=name_map.get(match.employee_id, "Employee"),
            score=float(match.score),
            matched=True,
        )

    def _do_attendance_event(
        self,
        *,
        employee_id: int,
        score: float,
        bbox: tuple[int, int, int, int],
        frame_bgr: np.ndarray,
        at_time,
        detected_face: DetectedFace,
    ) -> None:
        """Background-queue job: open DB session, write the event, save the
        snapshot, recompute daily rollup, publish realtime, maybe auto-
        enroll. Runs OFF the detector hot path so the live preview never
        stalls during recognition.

        `detected_face` is the recognition-time face object — passed
        through so auto-enroll can reuse its embedding without taking
        the FaceService lock again.
        """
        try:
            with session_scope() as db:
                service = AttendanceService(db)
                outcome = service.process_auto_event(
                    employee_id=employee_id,
                    camera_id=self.camera_id,
                    camera_type=self.camera_type,
                    confidence=score,
                    frame_bgr=frame_bgr,
                    bbox=bbox,
                    at_time=at_time,
                )
            if outcome.created:
                self.stats.events_generated += 1
                # Auto-enroll runs in its own pool so a slow FaceService
                # call (TrainingService can re-detect/embed) never delays
                # the next attendance write in the attendance pool.
                get_pool("auto_enroll").submit(
                    lambda eid=employee_id, fr=frame_bgr, sc=score, df=detected_face: (
                        self._do_auto_enroll(eid, fr, sc, df)
                    )
                )
            else:
                # Reset cooldown so the next frame can re-attempt
                # instead of suppressing this person until the cooldown
                # naturally expires.
                self.cooldown.reset(employee_id)
                log.debug(
                    "[%s] event skipped emp=%s reason=%s",
                    self.camera_name,
                    employee_id,
                    outcome.reason,
                )
        except Exception as exc:
            self.cooldown.reset(employee_id)
            self.stats.last_error = f"attendance: {exc}"
            log.exception("[%s] attendance pipeline error", self.camera_name)

    def _do_capture_unknown(self, *, face, frame: np.ndarray) -> None:
        """Background-queue job: persist an unknown-face capture if the
        pipeline is enabled. Cheap kill-switch check first to avoid
        opening a DB session on every unrecognized face when the feature
        is off (the typical state). Errors never propagate.
        """
        if not get_settings_service().get().unknown_capture_enabled:
            return
        try:
            with session_scope() as db:
                outcome = UnknownCaptureService(db).maybe_capture(
                    face=face,
                    frame_bgr=frame,
                    camera_id=self.camera_id,
                    captured_at=now_utc(),
                )
            if outcome.accepted:
                self.stats.unknown_captures += 1
                log.info(
                    "[%s] unknown captured cluster_id=%s new=%s",
                    self.camera_name,
                    outcome.cluster_id,
                    outcome.cluster_was_new,
                )
            else:
                self.stats.unknown_skipped += 1
                log.info(
                    "[%s] unknown skipped reason=%s",
                    self.camera_name,
                    outcome.reason,
                )
        except Exception:
            self.stats.last_error = "unknown_capture_pipeline"
            log.exception("[%s] unknown capture pipeline error", self.camera_name)

    def _do_auto_enroll(
        self,
        employee_id: int,
        frame: np.ndarray,
        match_score: float,
        detected_face: DetectedFace,
    ) -> None:
        """Background-queue helper: opportunistically add a fresh
        embedding from the live frame when the recognition score is
        high enough that we trust it. Submitted to its own `auto_enroll`
        pool from `_do_attendance_event` so a slow embedding refresh
        doesn't block the next attendance write.

        `detected_face` is the live-recognition face — passed in so
        TrainingService can reuse its embedding and skip the redundant
        InsightFace inference that would otherwise contend with the
        camera worker's detector thread.
        """
        s = get_settings_service().get()
        if not s.auto_update_enabled or match_score < s.auto_update_threshold:
            return
        try:
            with session_scope() as db:
                added = TrainingService(
                    db, self.face_service, self.embedding_cache
                ).auto_enroll_from_frame(
                    employee_id=employee_id,
                    frame_bgr=frame,
                    match_score=match_score,
                    precomputed_face=detected_face,
                )
            if added:
                self.stats.auto_enrollments += 1
        except Exception:
            log.exception("[%s] auto-enroll raised unexpectedly", self.camera_name)
