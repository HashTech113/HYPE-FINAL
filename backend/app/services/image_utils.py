"""Small image helpers used by the unknown-capture pipeline.

Crash-safe JPEG write (encode → tmp → ``os.replace``) and bbox crop with
a configurable pad ratio. Ported from the Super_Admin implementation.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def write_jpeg(path: Path, image: np.ndarray, quality: int = 90) -> None:
    """Atomically write a JPEG to ``path``.

    Encodes in-memory, writes to a sibling ``.tmp`` file, then
    ``os.replace`` swaps it into place. Any reader observing ``path``
    sees either the previous file or the fully-written new file — never
    a half-written one. ``os.replace`` is atomic on POSIX/NTFS when
    source and destination share a filesystem; the sibling path
    constraint is met by construction.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, int(quality)])
    if not ok:
        raise RuntimeError(f"Failed to encode JPEG for {path}")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(buf.tobytes())
    tmp.replace(path)


def crop_bbox(
    image: np.ndarray, bbox: tuple[int, int, int, int], pad: float = 0.2
) -> np.ndarray:
    h, w = image.shape[:2]
    x1, y1, x2, y2 = bbox
    bw = x2 - x1
    bh = y2 - y1
    px = int(bw * pad)
    py = int(bh * pad)
    x1 = max(0, x1 - px)
    y1 = max(0, y1 - py)
    x2 = min(w, x2 + px)
    y2 = min(h, y2 + py)
    return image[y1:y2, x1:x2].copy()
