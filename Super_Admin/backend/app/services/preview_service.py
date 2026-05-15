"""Draws bounding-box overlays for the live camera preview.

Pure-function module — no DB, no model state, no I/O. Takes the latest
frame from a camera worker and the per-face detections from that same
tick, and produces an annotated JPEG byte stream suitable for the
`/cameras/{id}/preview.jpg` endpoint.

Color convention (BGR — OpenCV native):
  * Green   — face matched a known employee
  * Red     — face was unknown (no match above threshold)
  * White   — label text on top of a filled colored band

Bounding-box geometry:
  InsightFace returns a tight detection rectangle that crops the chin
  and forehead — visually it looks like a "face slice" rather than the
  whole head. We expand the rendered box symmetrically (with a larger
  margin upward to capture hair / forehead) so the overlay actually
  encloses the full visible head. The expansion lives ONLY in this
  rendering module — the raw bbox passed to the snapshot/recognition
  pipeline stays tight, so cropping accuracy is unaffected.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import cv2
import numpy as np

if TYPE_CHECKING:
    from app.workers.camera_worker import FrameDetection


_MATCHED_COLOR: Final[tuple[int, int, int]] = (0, 200, 0)  # BGR — green
_UNKNOWN_COLOR: Final[tuple[int, int, int]] = (0, 0, 220)  # BGR — red
_TEXT_COLOR: Final[tuple[int, int, int]] = (255, 255, 255)
_FONT: Final[int] = cv2.FONT_HERSHEY_SIMPLEX
_FONT_SCALE: Final[float] = 0.55
_FONT_THICKNESS: Final[int] = 1
_BOX_THICKNESS: Final[int] = 2
_LABEL_PAD_X: Final[int] = 6
_LABEL_PAD_Y: Final[int] = 5
_LABEL_GAP_PX: Final[int] = 4  # gap between top of box and bottom of label
_DEFAULT_JPEG_QUALITY: Final[int] = 80

# Bbox expansion factors. The InsightFace detection rectangle is tight
# to the face — it routinely cuts off forehead/hair and chin. Expanding
# asymmetrically (more upward, less below) captures the full head shape
# the way a human would draw it. Tuned visually on buffalo_l outputs.
_EXPAND_TOP: Final[float] = 0.40  # 40% of bbox height above
_EXPAND_BOTTOM: Final[float] = 0.20  # 20% below
_EXPAND_SIDE: Final[float] = 0.18  # 18% on each side


def _expand_bbox(
    x1: int, y1: int, x2: int, y2: int, frame_w: int, frame_h: int
) -> tuple[int, int, int, int]:
    """Return a copy of the bbox grown to cover the full head, clamped
    to the frame. The expansion is asymmetric (more upward) because the
    InsightFace rectangle systematically misses forehead/hair.
    """
    bw = max(1, x2 - x1)
    bh = max(1, y2 - y1)
    nx1 = round(x1 - bw * _EXPAND_SIDE)
    nx2 = round(x2 + bw * _EXPAND_SIDE)
    ny1 = round(y1 - bh * _EXPAND_TOP)
    ny2 = round(y2 + bh * _EXPAND_BOTTOM)
    nx1 = max(0, min(nx1, frame_w - 1))
    nx2 = max(0, min(nx2, frame_w - 1))
    ny1 = max(0, min(ny1, frame_h - 1))
    ny2 = max(0, min(ny2, frame_h - 1))
    return nx1, ny1, nx2, ny2


def annotate_frame(frame: np.ndarray, detections: list[FrameDetection]) -> np.ndarray:
    """Return a copy of `frame` with one labeled rectangle per detection."""
    if frame is None or frame.size == 0:
        return frame
    out = frame.copy()
    h, w = out.shape[:2]
    for det in detections:
        color = _MATCHED_COLOR if det.matched else _UNKNOWN_COLOR
        # Expand the raw face rect to cover the full visible head, then
        # clamp to frame bounds so cv2.rectangle never errors out.
        x1, y1, x2, y2 = _expand_bbox(*det.bbox, frame_w=w, frame_h=h)
        if x2 <= x1 or y2 <= y1:
            continue
        cv2.rectangle(out, (x1, y1), (x2, y2), color, _BOX_THICKNESS)

        label = f"{det.label} {round(det.score * 100)}%" if det.matched else "Unknown"
        (text_w, text_h), baseline = cv2.getTextSize(label, _FONT, _FONT_SCALE, _FONT_THICKNESS)
        band_h = text_h + baseline + _LABEL_PAD_Y * 2
        # Always anchor the label ABOVE the box (with a small visible
        # gap), so the name reads naturally above the head. Only when
        # the head is so close to the top of the frame that there's
        # genuinely no room do we fall back to drawing the label
        # *inside* the top of the box. The pre-fix code would flip to
        # "inside" as soon as a single pixel didn't fit, which made
        # labels jump around for tall faces near the top edge.
        ideal_band_y2 = y1 - _LABEL_GAP_PX
        if ideal_band_y2 - band_h >= 0:
            band_y1 = ideal_band_y2 - band_h
            band_y2 = ideal_band_y2
        else:
            # No room above — clamp to top of frame and overlap into
            # the box. Better than clipping the text.
            band_y1 = 0
            band_y2 = min(h - 1, band_h)
        # Horizontal: left-align with box, but clamp so the band is
        # never wider than the frame and never extends off-screen on
        # narrow right-side faces.
        band_x1 = max(0, min(x1, w - 1))
        band_x2 = min(w - 1, band_x1 + text_w + _LABEL_PAD_X * 2)
        if band_x2 <= band_x1:
            continue
        cv2.rectangle(out, (band_x1, band_y1), (band_x2, band_y2), color, thickness=-1)
        # Text baseline sits inside the band, padded from the bottom.
        text_y = band_y2 - _LABEL_PAD_Y - baseline
        cv2.putText(
            out,
            label,
            (band_x1 + _LABEL_PAD_X, text_y),
            _FONT,
            _FONT_SCALE,
            _TEXT_COLOR,
            _FONT_THICKNESS,
            cv2.LINE_AA,
        )
    return out


def encode_jpeg(
    frame: np.ndarray,
    *,
    quality: int = _DEFAULT_JPEG_QUALITY,
    max_width: int | None = None,
) -> bytes:
    """Encode a BGR frame to JPEG bytes.

    `max_width` (when set) downsizes the frame proportionally before
    encoding. JPEG encoding cost is roughly linear in pixel count, so
    serving 960-wide previews instead of native 1920-wide cuts CPU and
    bandwidth ~4x without visibly hurting a Live tile.
    """
    if max_width is not None and max_width > 0:
        h, w = frame.shape[:2]
        if w > max_width:
            scale = max_width / float(w)
            new_w = max_width
            new_h = max(1, round(h * scale))
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise RuntimeError("Failed to encode preview JPEG")
    return buf.tobytes()
