from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import cv2
import numpy as np

from app.config import get_settings
from app.core.constants import EventType
from app.core.logger import get_logger
from app.utils.image_utils import write_jpeg
from app.utils.time_utils import to_local

log = get_logger(__name__)

_JPEG_QUALITY = 85
# Snapshot crop strategy — "head & shoulders, face zoomed".
#
# Tight padding around the face bbox: just enough top clearance to see
# hair, just enough bottom clearance to see neck/upper shoulders, and
# light side padding. Result: the face dominates the middle of the
# frame (clearly identifiable, "zoomed in" feel) without being so
# tight you can't tell who it is in a crowd of similar haircuts.
_PAD_TOP = 0.55  # × face height — clears the top of the hair
_PAD_BOTTOM = 0.90  # × face height — down to neck / collar level
_PAD_SIDE = 0.55  # × face width  — light shoulder margin
# Cap output width so a 1080p mainstream feed cropping a small face
# doesn't blow up into a multi-MB JPEG.
_SNAPSHOT_MAX_WIDTH = 720
# Visual style for the face highlight + name label, drawn after the
# crop so they stay at sensible relative sizes.
_BBOX_COLOR = (0, 200, 0)  # BGR — green
_BBOX_THICKNESS = 2
_LABEL_BG = (0, 200, 0)
_LABEL_FG = (255, 255, 255)
_LABEL_FONT = cv2.FONT_HERSHEY_SIMPLEX
_LABEL_SCALE = 0.55
_LABEL_THICKNESS = 1
_LABEL_PAD_X = 6
_LABEL_PAD_Y = 4


@dataclass
class StorageStats:
    root: str
    total_files: int
    total_bytes: int
    oldest_date: str | None
    newest_date: str | None


@dataclass
class PurgeResult:
    removed_files: int
    removed_bytes: int
    removed_dirs: int


class SnapshotService:
    """Event-based snapshot persistence.

    Layout: {SNAPSHOT_DIR}/YYYY-MM-DD/{employee_id}/{HHMMSS}_{EVENT}_{uuid}.jpg
    """

    def save_event_snapshot(
        self,
        *,
        employee_id: int,
        event_type: EventType,
        frame_bgr: np.ndarray,
        bbox: tuple[int, int, int, int] | None,
        captured_at: datetime,
        label: str | None = None,
    ) -> str:
        """Persist a head-to-chest crop with the recognized face's bbox
        and (when given) a name label. Returns the absolute path.

        Storage layout:
          {SNAPSHOT_DIR}/YYYY-MM-DD/{employee_id}/{HHMMSS}_{EVENT}_{uuid}.jpg
        """
        settings = get_settings()
        local_ts = to_local(captured_at)
        date_dir = local_ts.strftime("%Y-%m-%d")
        dir_path = Path(settings.SNAPSHOT_DIR) / date_dir / str(employee_id)

        image = self._render_snapshot(frame_bgr, bbox, label)

        filename = f"{local_ts.strftime('%H%M%S')}_{event_type.value}_{uuid.uuid4().hex[:8]}.jpg"
        full_path = dir_path / filename
        write_jpeg(full_path, image, quality=_JPEG_QUALITY)

        log.debug(
            "Snapshot saved path=%s event=%s emp=%s size=%dx%d",
            full_path,
            event_type.value,
            employee_id,
            image.shape[1],
            image.shape[0],
        )
        return str(full_path)

    @staticmethod
    def _render_snapshot(
        frame_bgr: np.ndarray,
        bbox: tuple[int, int, int, int] | None,
        label: str | None,
    ) -> np.ndarray:
        """Crop a head-to-chest window centered on the face bbox, downscale
        if needed, then draw the face bbox plus an optional name label.

        Asymmetric padding (more below than above) frames the subject from
        the top of the head down to roughly chest level — far more useful
        for HR verification than a tight forehead crop or a faraway full
        scene. If no bbox is given (manual events) we fall back to the
        full frame at the same width cap.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return frame_bgr

        h, w = frame_bgr.shape[:2]

        if bbox is None:
            cropped = frame_bgr
            crop_offset = (0, 0)
        else:
            x1, y1, x2, y2 = bbox
            bw = max(1, x2 - x1)
            bh = max(1, y2 - y1)
            top_px = int(bh * _PAD_TOP)
            bottom_px = int(bh * _PAD_BOTTOM)
            side_px = int(bw * _PAD_SIDE)
            cx1 = max(0, x1 - side_px)
            cy1 = max(0, y1 - top_px)
            cx2 = min(w, x2 + side_px)
            cy2 = min(h, y2 + bottom_px)
            cropped = frame_bgr[cy1:cy2, cx1:cx2]
            if cropped.size == 0:
                cropped = frame_bgr
                crop_offset = (0, 0)
            else:
                crop_offset = (cx1, cy1)

        ch, cw = cropped.shape[:2]
        scale = 1.0
        if cw > _SNAPSHOT_MAX_WIDTH:
            scale = _SNAPSHOT_MAX_WIDTH / float(cw)
            new_w = _SNAPSHOT_MAX_WIDTH
            new_h = max(1, round(ch * scale))
            image = cv2.resize(cropped, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            image = cropped.copy()

        if bbox is not None:
            ox, oy = crop_offset
            x1, y1, x2, y2 = bbox
            # Translate bbox into crop-local space, then scale into the
            # resized image so the rectangle still wraps the actual face.
            rx1 = round((x1 - ox) * scale)
            ry1 = round((y1 - oy) * scale)
            rx2 = round((x2 - ox) * scale)
            ry2 = round((y2 - oy) * scale)
            ih, iw = image.shape[:2]
            rx1 = max(0, min(iw - 1, rx1))
            ry1 = max(0, min(ih - 1, ry1))
            rx2 = max(0, min(iw - 1, rx2))
            ry2 = max(0, min(ih - 1, ry2))
            if rx2 > rx1 and ry2 > ry1:
                cv2.rectangle(image, (rx1, ry1), (rx2, ry2), _BBOX_COLOR, _BBOX_THICKNESS)
                if label:
                    SnapshotService._draw_label(image, rx1, ry1, rx2, label)
        return image

    @staticmethod
    def _draw_label(
        image: np.ndarray,
        rx1: int,
        ry1: int,
        rx2: int,
        text: str,
    ) -> None:
        """Draw a filled label band with white text directly above the
        bbox. If the bbox is at the top edge, place the band INSIDE the
        bbox along its top instead so the label is never clipped.
        """
        (tw, th), baseline = cv2.getTextSize(text, _LABEL_FONT, _LABEL_SCALE, _LABEL_THICKNESS)
        ih, iw = image.shape[:2]
        band_h = th + baseline + _LABEL_PAD_Y * 2
        band_w = min(iw - rx1, max(rx2 - rx1, tw + _LABEL_PAD_X * 2))
        if ry1 - band_h >= 0:
            band_y1 = ry1 - band_h
            band_y2 = ry1
        else:
            band_y1 = ry1
            band_y2 = min(ih - 1, ry1 + band_h)
        band_x1 = rx1
        band_x2 = min(iw - 1, rx1 + band_w)
        cv2.rectangle(
            image,
            (band_x1, band_y1),
            (band_x2, band_y2),
            _LABEL_BG,
            thickness=-1,
        )
        text_x = band_x1 + _LABEL_PAD_X
        text_y = band_y2 - _LABEL_PAD_Y - baseline + th
        cv2.putText(
            image,
            text,
            (text_x, text_y),
            _LABEL_FONT,
            _LABEL_SCALE,
            _LABEL_FG,
            _LABEL_THICKNESS,
            cv2.LINE_AA,
        )

    # ------------------------------------------------------------------
    # Retention / stats
    # ------------------------------------------------------------------

    def storage_stats(self) -> StorageStats:
        settings = get_settings()
        root = Path(settings.SNAPSHOT_DIR)
        if not root.exists():
            return StorageStats(str(root), 0, 0, None, None)

        total_files = 0
        total_bytes = 0
        dates: set[str] = set()
        for date_dir in root.iterdir():
            if not date_dir.is_dir():
                continue
            # Accept both new layout (YYYY-MM-DD) and legacy (YYYY)
            if self._parse_date_dir(date_dir.name) is not None:
                dates.add(date_dir.name)
            for p in date_dir.rglob("*.jpg"):
                try:
                    total_files += 1
                    total_bytes += p.stat().st_size
                except OSError:
                    continue

        sorted_dates = sorted(dates)
        return StorageStats(
            root=str(root),
            total_files=total_files,
            total_bytes=total_bytes,
            oldest_date=sorted_dates[0] if sorted_dates else None,
            newest_date=sorted_dates[-1] if sorted_dates else None,
        )

    def purge_before(self, cutoff: date) -> PurgeResult:
        """Delete snapshot files dated before `cutoff` (exclusive).

        Walks `{SNAPSHOT_DIR}/YYYY-MM-DD/` directories and removes any whose
        parsed date is < cutoff. Returns counts of what was removed. Files
        whose directory name does not match the layout are left untouched.
        """
        settings = get_settings()
        root = Path(settings.SNAPSHOT_DIR)
        if not root.exists():
            return PurgeResult(0, 0, 0)

        removed_files = 0
        removed_bytes = 0
        removed_dirs = 0

        for date_dir in root.iterdir():
            if not date_dir.is_dir():
                continue
            parsed = self._parse_date_dir(date_dir.name)
            if parsed is None or parsed >= cutoff:
                continue
            for p in date_dir.rglob("*"):
                if p.is_file():
                    try:
                        size = p.stat().st_size
                        p.unlink()
                        removed_files += 1
                        removed_bytes += size
                    except OSError as exc:
                        log.warning("Failed to remove %s: %s", p, exc)
            try:
                shutil.rmtree(date_dir, ignore_errors=True)
                removed_dirs += 1
            except OSError as exc:
                log.warning("Failed to rmdir %s: %s", date_dir, exc)

        log.info(
            "Purged snapshots before %s: %d files (%d bytes), %d dirs",
            cutoff,
            removed_files,
            removed_bytes,
            removed_dirs,
        )
        return PurgeResult(
            removed_files=removed_files,
            removed_bytes=removed_bytes,
            removed_dirs=removed_dirs,
        )

    @staticmethod
    def _parse_date_dir(name: str) -> date | None:
        try:
            return date.fromisoformat(name)
        except ValueError:
            return None
