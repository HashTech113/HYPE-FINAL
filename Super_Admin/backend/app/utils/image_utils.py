from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def decode_image_bytes(data: bytes) -> np.ndarray | None:
    arr = np.frombuffer(data, dtype=np.uint8)
    if arr.size == 0:
        return None
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def write_jpeg(path: Path, image: np.ndarray, quality: int = 90) -> None:
    """Atomically write a JPEG to `path`.

    Encodes to bytes first, writes to a sibling `.tmp` path, then
    `os.replace`-swaps it into place. This guarantees that any reader
    seeing `path` sees a fully-written file — never a half-written
    one. A crash mid-write leaves only the `.tmp`, which the next
    write reuses (overwrite) and the cleanup pass eventually removes.

    Why it matters: snapshot files are referenced by attendance event
    rows. Without atomic write, a process crash after `path.write_bytes`
    started but before it completed would leave a truncated JPEG that
    the dashboard tries to render — corrupted thumbnail, no useful
    error.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, int(quality)])
    if not ok:
        raise RuntimeError(f"Failed to encode JPEG for {path}")
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(buf.tobytes())
    # os.replace is atomic on POSIX and on NTFS (Windows) for files on
    # the same filesystem — `path.parent` always equals `tmp.parent`,
    # so the constraint is met. Standard pattern for crash-safe writes.
    tmp.replace(path)


def crop_bbox(image: np.ndarray, bbox: tuple[int, int, int, int], pad: float = 0.2) -> np.ndarray:
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
