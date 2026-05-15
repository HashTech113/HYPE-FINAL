"""Face-quality assessment used by the unknown-capture pipeline.

Pure-function module. No DB, no model state. Operates on a single
detected face (BGR frame + bbox + 5-point landmarks + detector
confidence) and returns a single accept/reject verdict plus the
numeric metrics that fed into it.

Ported from the Super_Admin reference implementation — see
``backend/PROJECT_STRUCTURE.md`` for the high-level rationale of each
metric.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import cv2
import numpy as np

_LAPLACIAN_KERNEL: Final[int] = 3
_FACE_CROP_PAD_RATIO: Final[float] = 0.10
_FRONTAL_EYE_MOUTH_RATIO: Final[float] = 1.3


@dataclass(frozen=True)
class FaceQualityMetrics:
    width: int
    height: int
    smaller_side: int
    det_score: float
    sharpness: float
    brightness: float
    contrast: float
    yaw_ratio: float
    pitch_ratio: float
    eye_tilt_deg: float


@dataclass(frozen=True)
class QualityThresholds:
    # Admin-tunable
    min_face_size_px: int
    min_det_score: float
    min_sharpness: float
    # Fixed defaults — tuned for real CCTV. Pose/lighting are deliberately
    # permissive: people walking past doorways are rarely perfectly frontal.
    min_brightness: float = 25.0
    max_brightness: float = 235.0
    min_contrast: float = 8.0
    max_yaw_ratio: float = 0.65
    max_pitch_ratio: float = 0.85
    max_eye_tilt_deg: float = 45.0


@dataclass(frozen=True)
class QualityVerdict:
    accepted: bool
    reason: str
    metrics: FaceQualityMetrics


def _crop_face(
    frame_bgr: np.ndarray,
    bbox: tuple[int, int, int, int],
    pad_ratio: float = _FACE_CROP_PAD_RATIO,
) -> np.ndarray:
    if frame_bgr.size == 0:
        return frame_bgr
    h, w = frame_bgr.shape[:2]
    x1, y1, x2, y2 = bbox
    bw = max(1, x2 - x1)
    bh = max(1, y2 - y1)
    pad_x = int(bw * pad_ratio)
    pad_y = int(bh * pad_ratio)
    x1c = max(0, int(x1) - pad_x)
    y1c = max(0, int(y1) - pad_y)
    x2c = min(w, int(x2) + pad_x)
    y2c = min(h, int(y2) + pad_y)
    if x2c <= x1c or y2c <= y1c:
        return frame_bgr[0:0, 0:0]
    return frame_bgr[y1c:y2c, x1c:x2c]


def _laplacian_variance(gray: np.ndarray) -> float:
    if gray.size == 0:
        return 0.0
    return float(cv2.Laplacian(gray, cv2.CV_64F, ksize=_LAPLACIAN_KERNEL).var())


def _luminance_stats(face_bgr: np.ndarray) -> tuple[float, float]:
    if face_bgr.size == 0:
        return 0.0, 0.0
    hsv = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2HSV)
    v = hsv[..., 2].astype(np.float32)
    return float(v.mean()), float(v.std())


def _estimate_yaw_ratio(kps: np.ndarray, face_width: int) -> float:
    if kps is None or kps.shape[0] < 3:
        return 1.0
    if face_width <= 0:
        return 1.0
    le_x = float(kps[0, 0])
    re_x = float(kps[1, 0])
    nose_x = float(kps[2, 0])
    d_left = abs(nose_x - le_x)
    d_right = abs(re_x - nose_x)
    denom = d_left + d_right
    if denom < 1e-6:
        return 1.0
    return float(abs(d_left - d_right) / denom)


def _estimate_pitch_ratio(kps: np.ndarray, face_height: int) -> float:
    if kps is None or kps.shape[0] < 5:
        return 1.0
    if face_height <= 0:
        return 1.0
    eyes_y = (float(kps[0, 1]) + float(kps[1, 1])) * 0.5
    nose_y = float(kps[2, 1])
    mouth_y = (float(kps[3, 1]) + float(kps[4, 1])) * 0.5
    eye_to_nose = max(1.0, nose_y - eyes_y)
    nose_to_mouth = max(1.0, mouth_y - nose_y)
    actual = eye_to_nose / nose_to_mouth
    return float(abs(actual - _FRONTAL_EYE_MOUTH_RATIO) / _FRONTAL_EYE_MOUTH_RATIO)


def _estimate_eye_tilt_deg(kps: np.ndarray) -> float:
    if kps is None or kps.shape[0] < 2:
        return 0.0
    le = kps[0]
    re = kps[1]
    dx = float(re[0] - le[0])
    dy = float(re[1] - le[1])
    if abs(dx) < 1e-6:
        return 90.0
    angle = float(abs(np.degrees(np.arctan2(dy, dx))))
    if angle > 90.0:
        angle = 180.0 - angle
    return angle


def measure(
    *,
    frame_bgr: np.ndarray,
    bbox: tuple[int, int, int, int],
    kps: np.ndarray,
    det_score: float,
) -> FaceQualityMetrics:
    x1, y1, x2, y2 = bbox
    width = max(0, int(x2) - int(x1))
    height = max(0, int(y2) - int(y1))
    smaller = min(width, height)

    crop = _crop_face(frame_bgr, bbox)
    if crop.size > 0:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    else:
        gray = crop

    return FaceQualityMetrics(
        width=width,
        height=height,
        smaller_side=smaller,
        det_score=float(det_score),
        sharpness=_laplacian_variance(gray),
        brightness=_luminance_stats(crop)[0],
        contrast=_luminance_stats(crop)[1],
        yaw_ratio=_estimate_yaw_ratio(kps, width),
        pitch_ratio=_estimate_pitch_ratio(kps, height),
        eye_tilt_deg=_estimate_eye_tilt_deg(kps),
    )


def evaluate(metrics: FaceQualityMetrics, thresholds: QualityThresholds) -> QualityVerdict:
    if metrics.det_score < thresholds.min_det_score:
        return QualityVerdict(False, "low_det_score", metrics)
    if metrics.smaller_side < thresholds.min_face_size_px:
        return QualityVerdict(False, "face_too_small", metrics)
    if metrics.sharpness < thresholds.min_sharpness:
        return QualityVerdict(False, "blurry", metrics)
    if metrics.brightness < thresholds.min_brightness:
        return QualityVerdict(False, "underexposed", metrics)
    if metrics.brightness > thresholds.max_brightness:
        return QualityVerdict(False, "overexposed", metrics)
    if metrics.contrast < thresholds.min_contrast:
        return QualityVerdict(False, "low_contrast", metrics)
    if metrics.yaw_ratio > thresholds.max_yaw_ratio:
        return QualityVerdict(False, "non_frontal", metrics)
    if metrics.pitch_ratio > thresholds.max_pitch_ratio:
        return QualityVerdict(False, "extreme_pitch", metrics)
    if metrics.eye_tilt_deg > thresholds.max_eye_tilt_deg:
        return QualityVerdict(False, "tilted_head", metrics)
    return QualityVerdict(True, "ok", metrics)


def measure_and_evaluate(
    *,
    frame_bgr: np.ndarray,
    bbox: tuple[int, int, int, int],
    kps: np.ndarray,
    det_score: float,
    thresholds: QualityThresholds,
) -> QualityVerdict:
    m = measure(frame_bgr=frame_bgr, bbox=bbox, kps=kps, det_score=det_score)
    return evaluate(m, thresholds)
