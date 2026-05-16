"""One-off: cap each employee's embeddings at MAX_EMBEDDINGS_PER_EMPLOYEE.

Background: the per-employee cap used to be enforced only in the React
panel (counted visible images). After Train, the post-train cleanup
clears ``image_data`` and the panel hides cleared rows, so the visible
count "resets" to 0 — admins could then upload another 6, train, repeat.
A handful of employees collected dozens of redundant embeddings that
way before the backend cap (services/face_training.py) landed.

This script keeps the TOP-K embeddings per employee by quality_score
(``quality_score DESC, id DESC`` — tie-break on the most recent row)
and deletes the rest. Touches nothing else: face_images stubs, profile
photos, attendance_logs, snapshot_logs, and unknown_face_captures are
untouched. Embedding cache is invalidated for affected employees so
recognition picks up the leaner set without a process restart.

Usage (from backend/):
    python -m scripts.prune_excess_embeddings           # dry run (default)
    python -m scripts.prune_excess_embeddings --apply   # actually delete
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.db import session_scope  # noqa: E402
from app.models import Employee, FaceEmbedding  # noqa: E402
from app.services.embedding_cache import get_embedding_cache  # noqa: E402
from app.services.face_training import MAX_EMBEDDINGS_PER_EMPLOYEE  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("prune_excess_embeddings")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete rows. Default is a dry run that prints what would change.",
    )
    args = parser.parse_args()

    keep = MAX_EMBEDDINGS_PER_EMPLOYEE
    affected: list[tuple[str, str, int, int]] = []  # (emp_id, name, before, kept)
    delete_ids: list[int] = []

    with session_scope() as session:
        # One pass: pull every employee with > MAX embeddings, ordered
        # by quality so the keep/delete split is just a list slice.
        emp_rows = session.execute(
            select(Employee.id, Employee.name)
        ).all()
        for emp_id, emp_name in emp_rows:
            rows = session.execute(
                select(FaceEmbedding.id, FaceEmbedding.quality_score)
                .where(FaceEmbedding.employee_id == emp_id)
                .order_by(
                    FaceEmbedding.quality_score.desc(),
                    FaceEmbedding.id.desc(),
                )
            ).all()
            if len(rows) <= keep:
                continue
            kept = rows[:keep]
            dropped = rows[keep:]
            affected.append((str(emp_id), str(emp_name or ""), len(rows), len(kept)))
            delete_ids.extend(int(r[0]) for r in dropped)
            log.info(
                "  %-30s before=%-3d keep=%-3d drop=%-3d  "
                "kept_quality=[%.3f .. %.3f]  dropped_quality=[%.3f .. %.3f]",
                (emp_name or emp_id)[:30],
                len(rows), len(kept), len(dropped),
                float(kept[0][1]), float(kept[-1][1]),
                float(dropped[0][1]), float(dropped[-1][1]),
            )

    if not affected:
        log.info("nothing to do — every employee is already within the cap of %d", keep)
        return 0

    log.info(
        "%d employee(s) over cap; %d embedding row(s) would be deleted",
        len(affected), len(delete_ids),
    )

    if not args.apply:
        log.info("DRY RUN — re-run with --apply to execute the deletes")
        return 0

    # Re-open a write session to do the actual deletes. Doing it in
    # batches via id IN (...) so a single SQLite query handles the lot.
    with session_scope() as session:
        stmt = select(FaceEmbedding).where(FaceEmbedding.id.in_(delete_ids))
        rows = session.execute(stmt).scalars().all()
        for r in rows:
            session.delete(r)
        deleted = len(rows)

    log.info("deleted %d embedding row(s)", deleted)

    # Refresh the in-memory cache for every affected employee so the
    # next /api/recognition/identify call sees the leaner set.
    cache = get_embedding_cache()
    for emp_id, _name, _before, _kept in affected:
        try:
            cache.reload_employee(emp_id)
        except Exception:
            log.exception("cache refresh failed for emp_id=%s", emp_id)
    log.info("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
