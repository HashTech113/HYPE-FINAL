"""image_utils — atomic JPEG write contract.

The atomicity guarantee (write-tmp, replace) is what protects
attendance snapshots from being read half-written by the dashboard.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from app.utils.image_utils import write_jpeg

pytestmark = pytest.mark.unit


def _make_image() -> np.ndarray:
    # 32×32 BGR test pattern; tiny so encode is microseconds.
    return np.full((32, 32, 3), 128, dtype=np.uint8)


def test_write_jpeg_creates_parents(tmp_path: Path) -> None:
    """The function should create missing parent directories.
    Otherwise the snapshot service has to mkdir before every write."""
    target = tmp_path / "deep" / "nested" / "dirs" / "out.jpg"
    write_jpeg(target, _make_image())
    assert target.exists() and target.stat().st_size > 0


def test_write_jpeg_atomic_no_tmp_file_left_behind(tmp_path: Path) -> None:
    """After a successful write, the .tmp must NOT exist — if it does,
    the swap didn't happen (or happened wrong) and a future write
    could trip over it."""
    target = tmp_path / "out.jpg"
    write_jpeg(target, _make_image())
    assert target.exists()
    # No leftover .tmp anywhere in the directory.
    leftover = list(tmp_path.glob("*.tmp"))
    assert leftover == [], f"unexpected .tmp leftovers: {leftover}"


def test_write_jpeg_overwrites_existing_atomically(tmp_path: Path) -> None:
    """Writing twice must replace, not append/error. Image content
    must change between writes."""
    target = tmp_path / "out.jpg"
    write_jpeg(target, np.zeros((16, 16, 3), dtype=np.uint8))
    first_size = target.stat().st_size

    write_jpeg(target, np.full((128, 128, 3), 200, dtype=np.uint8))
    second_size = target.stat().st_size

    # Bigger image → bigger file (loose check; could in theory tie).
    assert second_size != first_size


def test_write_jpeg_quality_arg_changes_output_size(tmp_path: Path) -> None:
    """Quality arg actually plumbs through to cv2 — protects against a
    refactor that drops the argument silently."""
    a = tmp_path / "a.jpg"
    b = tmp_path / "b.jpg"
    img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    write_jpeg(a, img, quality=10)
    write_jpeg(b, img, quality=95)
    # Higher quality → larger file (with random data, the gap is
    # always large enough to assert reliably).
    assert b.stat().st_size > a.stat().st_size
