"""Pure attendance logic — group face captures into per-employee daily records.

Storage layer (snapshots/) gives us UTC entry/exit per face crop.
This module turns that into one row per (name, local_date) with status against
a configured shift, including break detection and a missing-checkout flag.

Time math (per the operations spec):

    first ENTRY    = earliest capture of the day              -> entry_time
    final EXIT     = latest capture of the day                -> exit_time
    break out      = capture immediately before a long gap
    break in       = capture immediately after the same gap
    total break    = sum of break_in - break_out across pairs
    total working  = (final exit - first entry) - total break

A "long gap" is any gap >= ``BREAK_GAP_THRESHOLD_MIN``. The camera fires a
capture every few seconds while a face is in frame, so a gap that long is
the employee being away from the camera (lunch / step-out).

Special cases:
  - Only one capture, target date is today  -> active, hours not finalised
  - Only one capture, target date is older  -> missing_checkout flag
  - Manual correction stored for (name, date) -> overrides the auto values
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_cls, datetime, time, timedelta, timezone
from typing import Iterable, Optional

from ..config import BREAK_GAP_THRESHOLD_MIN
from .snapshots import Snapshot


@dataclass(frozen=True)
class ShiftSettings:
    start: time              # local
    end: time                # local
    late_grace_min: int
    early_exit_grace_min: int
    tz_offset_min: int       # local timezone offset from UTC, in minutes


def parse_hhmm(value: str) -> time:
    hh, mm = value.split(":")
    return time(hour=int(hh), minute=int(mm))


def _local_tz(offset_min: int) -> timezone:
    return timezone(timedelta(minutes=offset_min))


def _to_local(dt: datetime, tz_offset_min: int) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_local_tz(tz_offset_min))


def _format_hours_minutes_seconds(total_seconds: int) -> str:
    if total_seconds <= 0:
        return "—"
    hours = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours}h {mins}m {secs}s"


def _classify(
    entry_local: datetime,
    exit_local: Optional[datetime],
    shift: ShiftSettings,
) -> tuple[str, int, int, int, int]:
    """Returns (status, late_minutes, early_exit_minutes, late_seconds, early_exit_seconds).

    If exit_local is None we still classify entry-side lateness; early-exit
    fields are zero because there is no exit to compare against.

    Late grace handling: entries arriving within ``shift.late_grace_min`` of
    shift start are "on time" — status is Present and late_minutes/seconds
    are reported as 0 (so dashboards / reports that test ``late_minutes>0``
    don't paint within-grace arrivals as late). Once the entry crosses the
    grace cutoff (e.g. 09:45 with a 09:30 shift + 15 min grace) we count
    lateness from THAT cutoff, so the reported value answers "how late after
    the grace window?" rather than "how late since shift start?".
    """
    shift_start = entry_local.replace(
        hour=shift.start.hour, minute=shift.start.minute, second=0, microsecond=0
    )
    raw_late_seconds = max(0, int((entry_local - shift_start).total_seconds()))
    grace_seconds = max(0, shift.late_grace_min) * 60
    late_seconds = max(0, raw_late_seconds - grace_seconds)
    late_min = late_seconds // 60
    is_late = late_seconds > 0

    if exit_local is None:
        return ("Late" if is_late else "Present", late_min, 0, late_seconds, 0)

    shift_end = entry_local.replace(
        hour=shift.end.hour, minute=shift.end.minute, second=0, microsecond=0
    )
    raw_early_exit_seconds = max(0, int((shift_end - exit_local).total_seconds()))
    early_grace_seconds = max(0, shift.early_exit_grace_min) * 60
    early_exit_seconds = max(0, raw_early_exit_seconds - early_grace_seconds)
    early_min = early_exit_seconds // 60
    is_early = early_exit_seconds > 0

    if is_late:
        status = "Late"
    elif is_early:
        status = "Early Exit"
    else:
        status = "Present"

    return status, late_min, early_min, late_seconds, early_exit_seconds


def _image_url_for(snap: Snapshot) -> Optional[str]:
    if snap.image_data:
        return f"data:image/jpeg;base64,{snap.image_data}"
    return None


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().split())


def _name_key(name: str) -> str:
    """Case/whitespace-insensitive grouping key. Must match the key used by
    the snapshot retention job (services/cleanup.py:_normalize_name_key) so
    cleanup keeps the SAME first/last rows that the report selects.
    """
    return _normalize_name(name).lower()


def _earliest_with_image(snaps_sorted: list[Snapshot]) -> Optional[Snapshot]:
    """First capture (by time) whose image_data is still present. Used to
    fall back to a kept-image row when the absolute earliest capture had
    its image cleared (e.g. captures inserted out of order between cleanup
    runs).
    """
    for s in snaps_sorted:
        if s.image_data:
            return s
    return None


def _latest_with_image(snaps_sorted: list[Snapshot]) -> Optional[Snapshot]:
    for s in reversed(snaps_sorted):
        if s.image_data:
            return s
    return None


BreakPair = tuple[Snapshot, Snapshot, int]


def _movement_event(
    *,
    snap: Snapshot,
    movement_type: str,
    tz_offset_min: int,
) -> dict:
    local_dt = _to_local(snap.entry, tz_offset_min)
    return {
        "event_id": f"{movement_type.lower().replace(' ', '_')}|{snap.filename}",
        "movement_type": movement_type,
        "timestamp": local_dt.strftime("%H:%M:%S"),
        "timestamp_iso": local_dt.isoformat(),
        "snapshot_url": _image_url_for(snap),
        "snapshot_archived": not bool(snap.image_data),
        "camera_id": snap.camera_id or "",
        "camera_name": (snap.camera_name or "").strip() or None,
        "confidence": float(snap.score) if snap.score is not None else None,
    }


def _detect_breaks(
    snaps_sorted: list[Snapshot], tz_offset_min: int
) -> tuple[list[dict], int, list[BreakPair]]:
    """Return (break_details, total_break_seconds).

    A break is a gap between consecutive captures of at least
    BREAK_GAP_THRESHOLD_MIN minutes. break_out = capture before the gap,
    break_in = capture after.

    The first gap (after the entry) and the last gap (before the exit) are
    excluded from break detection because they are bounded by entry/exit
    themselves — otherwise a day with only an entry and an exit capture
    would treat the whole shift as one big "break". Auto-detection works
    best with dense captures; sparse data may need manual correction.
    """
    if len(snaps_sorted) < 4:
        return [], 0, []
    threshold = BREAK_GAP_THRESHOLD_MIN * 60
    breaks: list[dict] = []
    break_pairs: list[BreakPair] = []
    total = 0
    # Inspect only intermediate gaps: indices 2..len-2 (gaps between
    # snaps_sorted[i-1] and snaps_sorted[i] where neither end is the global
    # first or last capture).
    for i in range(2, len(snaps_sorted) - 1):
        prev = snaps_sorted[i - 1]
        cur = snaps_sorted[i]
        gap = int((cur.entry - prev.entry).total_seconds())
        if gap >= threshold:
            break_out_local = _to_local(prev.entry, tz_offset_min)
            break_in_local = _to_local(cur.entry, tz_offset_min)
            breaks.append({
                "break_out": break_out_local.strftime("%H:%M:%S"),
                "break_in": break_in_local.strftime("%H:%M:%S"),
                "break_out_iso": break_out_local.isoformat(),
                "break_in_iso": break_in_local.isoformat(),
                "duration_seconds": gap,
                "duration": _format_hours_minutes_seconds(gap),
            })
            break_pairs.append((prev, cur, gap))
            total += gap
    return breaks, total, break_pairs


def _build_movement_history(
    *,
    snaps_sorted: list[Snapshot],
    break_pairs: list[BreakPair],
    include_final_exit: bool,
    tz_offset_min: int,
    cam_types: Optional[dict[str, str]] = None,
) -> list[dict]:
    """Build the per-day movement timeline shown in the report's expandable
    "Break History & Movement Timeline" panel.

    When ``cam_types`` is supplied (camera_id -> "ENTRY" or "EXIT"), EVERY
    snapshot of the day becomes a timeline event classified by its source
    camera:
      * Entry camera + first snap → "Entry"
      * Entry camera + later     → "Break In"
      * Exit camera + last snap (and there's at least one earlier snap)
                                 → "Final Exit"
      * Exit camera + other      → "Break Out"
    This is the new path — the operator sees every entry and exit detection.

    When ``cam_types`` is empty/None (legacy single-camera ingest, or a
    snap with a missing camera_id), fall back to the original gap-pair
    heuristic that emits Entry + (Break Out / Break In)* + Final Exit
    only. This keeps history sane for pre-multi-camera databases.
    """
    if not snaps_sorted:
        return []

    # New path: classify by camera type when we have it. We use a per-snap
    # check so a mixed day (some snaps with camera_id, some without) still
    # falls back per-snap rather than wholesale.
    if cam_types:
        last_idx = len(snaps_sorted) - 1
        events: list[tuple[datetime, int, dict]] = []
        for i, snap in enumerate(snaps_sorted):
            cam_id = (snap.camera_id or "").strip()
            cam_type = cam_types.get(cam_id) if cam_id else None
            is_first = i == 0
            is_last = i == last_idx and include_final_exit and len(snaps_sorted) > 1
            if cam_type == "ENTRY":
                movement_type = "Entry" if is_first else "Break In"
            elif cam_type == "EXIT":
                movement_type = "Final Exit" if is_last else "Break Out"
            else:
                # Unknown / legacy camera — fall back to position-based labels
                # so the row still appears in the timeline.
                if is_first:
                    movement_type = "Entry"
                elif is_last:
                    movement_type = "Final Exit"
                else:
                    movement_type = "Break Out"
            events.append(
                (
                    snap.entry,
                    i,
                    _movement_event(
                        snap=snap,
                        movement_type=movement_type,
                        tz_offset_min=tz_offset_min,
                    ),
                )
            )
        events.sort(key=lambda item: (item[0], item[1]))
        return [payload for _ts, _seq, payload in events]

    # Legacy path: gap-pair heuristic. Kept for backwards compat with
    # pre-multi-camera databases where camera_id is unknown.
    first = snaps_sorted[0]
    events: list[tuple[datetime, int, dict]] = []
    sequence = 0
    events.append(
        (
            first.entry,
            sequence,
            _movement_event(
                snap=first,
                movement_type="Entry",
                tz_offset_min=tz_offset_min,
            ),
        )
    )
    sequence += 1
    for break_out, break_in, _gap in break_pairs:
        events.append(
            (
                break_out.entry,
                sequence,
                _movement_event(
                    snap=break_out,
                    movement_type="Break Out",
                    tz_offset_min=tz_offset_min,
                ),
            )
        )
        sequence += 1
        events.append(
            (
                break_in.entry,
                sequence,
                _movement_event(
                    snap=break_in,
                    movement_type="Break In",
                    tz_offset_min=tz_offset_min,
                ),
            )
        )
        sequence += 1
    if include_final_exit and len(snaps_sorted) > 1:
        last = snaps_sorted[-1]
        events.append(
            (
                last.entry,
                sequence,
                _movement_event(
                    snap=last,
                    movement_type="Final Exit",
                    tz_offset_min=tz_offset_min,
                ),
            )
        )
    events.sort(key=lambda item: (item[0], item[1]))
    return [payload for _ts, _seq, payload in events]


def _compute_totals_from_timeline(events: list[dict]) -> tuple[int, int]:
    """Derive ``(total_work_seconds, total_break_seconds)`` from the
    chronological Break History / Movement Timeline events.

    Walks the Entry / Break In / Break Out / Final Exit events in order,
    treating Entry / Break In as transitions to "inside the office" and
    Break Out / Final Exit as transitions to "outside the office". Time
    spent inside is summed into work; time spent outside is summed into
    break.

    This makes the headline "Total Working Hours" and "Total Break Time"
    numbers in the report match exactly what the operator can see and
    add up themselves in the expandable timeline below — every gap
    visible there is counted, nothing else is.

    Edge behaviour, by design:
      * Same-side repeats (e.g. two Entry events in a row, which can
        happen if a person lingered in front of the entry camera) keep
        the original boundary so we don't double-count.
      * A day that starts with an Exit-side event gets no preceding
        work credit — we can't infer time we don't have an entry for.
      * A day still "open" inside the office (no trailing exit yet)
        drops the trailing open interval — same reason.

    Returns ``(0, 0)`` on an empty timeline.
    """
    if not events:
        return 0, 0

    INSIDE = ("Entry", "Break In")
    OUTSIDE = ("Break Out", "Final Exit")

    work_seconds = 0
    break_seconds = 0
    state: Optional[str] = None  # "INSIDE" | "OUTSIDE"
    last_boundary: Optional[datetime] = None

    for ev in events:
        mt = str(ev.get("movement_type") or "")
        if mt in INSIDE:
            new_state = "INSIDE"
        elif mt in OUTSIDE:
            new_state = "OUTSIDE"
        else:
            continue
        ts_iso = ev.get("timestamp_iso")
        if not isinstance(ts_iso, str) or not ts_iso:
            continue
        try:
            ts = datetime.fromisoformat(ts_iso)
        except ValueError:
            continue

        if state == new_state:
            # Same-direction repeat — keep the original boundary so the
            # interval isn't artificially reset mid-stay.
            continue

        if state is not None and last_boundary is not None:
            delta = max(0, int((ts - last_boundary).total_seconds()))
            if state == "INSIDE":
                work_seconds += delta
            else:
                break_seconds += delta

        state = new_state
        last_boundary = ts

    return work_seconds, break_seconds


def _parse_iso(value: Optional[str], tz_offset_min: int) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_local_tz(tz_offset_min))
    return dt.astimezone(_local_tz(tz_offset_min))


def _today_local(tz_offset_min: int) -> date_cls:
    return datetime.now(timezone.utc).astimezone(_local_tz(tz_offset_min)).date()


def build_daily_records(
    snapshots: Iterable[Snapshot],
    *,
    target_date: date_cls,
    shift: ShiftSettings,
    base_url: str,
    expected_names: Optional[list[str]] = None,
    corrections: Optional[dict[tuple[str, str], dict]] = None,
    rollups: Optional[dict[tuple[str, str], dict]] = None,
    cam_types: Optional[dict[str, str]] = None,
) -> list[dict]:
    """One record per name detected on `target_date` (local). Optionally
    fills in 'Absent' rows for `expected_names` not found.

    ``rollups`` (optional) — keyed by ``(name_lower, date_iso)``. When
    present for a given (name, date), the rollup row is authoritative for
    in_time / out_time / break / work seconds / late / early / status —
    these override the gap-based derivation. HR corrections still win on
    top of the rollup, mirroring the legacy precedence.
    """
    # Group case-insensitively (matches the cleanup job's key) but keep the
    # first display-cased name we see so the report shows the original
    # spelling.
    by_name: dict[str, list[Snapshot]] = {}
    display_name: dict[str, str] = {}
    for snap in snapshots:
        entry_local = _to_local(snap.entry, shift.tz_offset_min)
        if entry_local.date() != target_date:
            continue
        canonical = _normalize_name(snap.name)
        if not canonical:
            continue
        key = canonical.lower()
        by_name.setdefault(key, []).append(snap)
        display_name.setdefault(key, canonical)

    today = _today_local(shift.tz_offset_min)
    is_today = target_date == today
    records: list[dict] = []
    for key, snaps in by_name.items():
        name = display_name[key]
        snaps_sorted = sorted(snaps, key=lambda s: s.entry)
        first = snaps_sorted[0]
        last = snaps_sorted[-1]
        # For images, fall back to the earliest/latest row that still has
        # image_data. Time-based first/last define entry/exit *time*; image
        # rows define entry/exit *thumbnail*. They are usually the same row,
        # but cleanup or out-of-order ingest can split them.
        entry_image_snap = first if first.image_data else _earliest_with_image(snaps_sorted)
        exit_image_snap = last if last.image_data else _latest_with_image(snaps_sorted)
        entry_local = _to_local(first.entry, shift.tz_offset_min)

        only_one = len(snaps_sorted) == 1
        if only_one:
            if is_today:
                # Active employee — entry recorded, no exit yet.
                exit_local: Optional[datetime] = None
                missing_checkout = False
                is_active = True
            else:
                # Older day with only one capture — checkout is missing.
                exit_local = None
                missing_checkout = True
                is_active = False
        else:
            exit_local = _to_local(last.exit, shift.tz_offset_min)
            missing_checkout = False
            is_active = False

        break_details, total_break_seconds, break_pairs = _detect_breaks(
            snaps_sorted, shift.tz_offset_min
        )

        # Rollup-first: if the attendance state machine has already
        # settled this person's day in ``daily_attendance``, replace the
        # gap-based view with the persisted rollup. Image URLs, movement
        # history, and per-break detail stay from the gap-based path
        # because the rollup doesn't carry that detail. HR corrections in
        # the block below still win over the rollup.
        rollup_row: Optional[dict] = (rollups or {}).get(
            (key, target_date.isoformat())
        )
        if rollup_row is not None:
            r_in = rollup_row.get("in_time")
            r_out = rollup_row.get("out_time")
            r_in_dt: Optional[datetime] = None
            r_out_dt: Optional[datetime] = None
            if isinstance(r_in, datetime):
                r_in_dt = r_in
            elif r_in is not None:
                r_in_dt = _parse_iso(str(r_in), shift.tz_offset_min)
            if isinstance(r_out, datetime):
                r_out_dt = r_out
            elif r_out is not None:
                r_out_dt = _parse_iso(str(r_out), shift.tz_offset_min)
            if r_in_dt is not None:
                entry_local = _to_local(r_in_dt, shift.tz_offset_min)
            if r_out_dt is not None:
                exit_local = _to_local(r_out_dt, shift.tz_offset_min)
                missing_checkout = False
            rb = rollup_row.get("total_break_seconds")
            if rb is not None:
                total_break_seconds = int(rb)
                # Clear the gap-based break_details/pairs so the rendered
                # break total agrees with what's in the rollup.
                break_details = []
                break_pairs = []

        # Apply manual correction overrides, if any.
        correction = (corrections or {}).get((key, target_date.isoformat()))
        correction_applied = False
        if correction:
            corrected_entry = _parse_iso(correction.get("entry_iso"), shift.tz_offset_min)
            corrected_exit = _parse_iso(correction.get("exit_iso"), shift.tz_offset_min)
            if corrected_entry is not None:
                entry_local = corrected_entry
                correction_applied = True
            if corrected_exit is not None:
                exit_local = corrected_exit
                missing_checkout = False
                correction_applied = True
            cb = correction.get("total_break_seconds")
            if cb is not None:
                total_break_seconds = int(cb)
                break_details = []  # break_details only describe auto-detected gaps
                break_pairs = []
                correction_applied = True
            if int(correction.get("missing_checkout_resolved") or 0) == 1:
                missing_checkout = False
                correction_applied = True

        if exit_local is None:
            total_sec = 0
            total_hours_str = "—"
            total_break_seconds = 0  # no exit -> break math is meaningless
            break_details = []
            break_pairs = []
        else:
            span = max(0, int((exit_local - entry_local).total_seconds()))
            total_sec = max(0, span - total_break_seconds)
            total_hours_str = _format_hours_minutes_seconds(total_sec)

        movement_history = _build_movement_history(
            snaps_sorted=snaps_sorted,
            break_pairs=break_pairs,
            include_final_exit=not only_one,
            tz_offset_min=shift.tz_offset_min,
            cam_types=cam_types,
        )

        # Headline totals: derive directly from the Break History timeline
        # so the numbers shown in the report row match what the operator
        # can add up themselves in the expandable panel. HR corrections
        # that explicitly set total_break_seconds win over this (admin
        # truth); the rollup path falls back to gap-based math when no
        # timeline is available. See _compute_totals_from_timeline for
        # the walk semantics.
        hr_break_correction = (
            correction is not None
            and correction.get("total_break_seconds") is not None
        )
        if movement_history and not hr_break_correction and exit_local is not None:
            tl_work, tl_break = _compute_totals_from_timeline(movement_history)
            if tl_work > 0 or tl_break > 0:
                total_break_seconds = tl_break
                total_sec = tl_work
                total_hours_str = _format_hours_minutes_seconds(total_sec)

        total_min = total_sec // 60
        status, late_min, early_min, late_seconds, early_exit_seconds = _classify(
            entry_local, exit_local, shift
        )

        # If the rollup is authoritative for this (name, date), trust its
        # late/early/status over the gap-based classification. Seconds
        # don't exist on the rollup so we synthesise them from minutes.
        if rollup_row is not None:
            r_late = rollup_row.get("late_minutes")
            r_early = rollup_row.get("early_exit_minutes")
            r_status = rollup_row.get("status")
            if r_late is not None:
                late_min = int(r_late)
                late_seconds = late_min * 60
            if r_early is not None:
                early_min = int(r_early)
                early_exit_seconds = early_min * 60
            if r_status:
                status = str(r_status)

        # Report-level overrides win over the auto-classified status. These
        # are HR-set and reflect things the camera pipeline can't infer.
        paid_leave_flag = False
        lop_flag = False
        wfh_flag = False
        if correction:
            override_status = correction.get("status_override")
            if override_status:
                status = override_status
                correction_applied = True
            paid_leave_flag = bool(int(correction.get("paid_leave") or 0))
            lop_flag = bool(int(correction.get("lop") or 0))
            wfh_flag = bool(int(correction.get("wfh") or 0))
            if paid_leave_flag or lop_flag or wfh_flag:
                correction_applied = True

        records.append({
            "name": name,
            "date": target_date.isoformat(),
            "entry": entry_local.strftime("%H:%M:%S"),
            "exit": exit_local.strftime("%H:%M:%S") if exit_local else None,
            "entry_iso": entry_local.isoformat(),
            "exit_iso": exit_local.isoformat() if exit_local else None,
            "total_hours": total_hours_str,
            "total_working_hours": total_hours_str,
            "total_minutes": total_min,
            "total_working_seconds": total_sec,
            "total_break_seconds": total_break_seconds,
            "total_break_time": _format_hours_minutes_seconds(total_break_seconds),
            "break_details": break_details,
            "movement_history": movement_history,
            "status": status,
            "late_minutes": late_min,
            "late_seconds": late_seconds,
            "early_exit_minutes": early_min,
            "early_exit_seconds": early_exit_seconds,
            "capture_count": len(snaps_sorted),
            "entry_image_url": _image_url_for(entry_image_snap) if entry_image_snap else None,
            "exit_image_url": (
                _image_url_for(exit_image_snap) if (not only_one and exit_image_snap) else None
            ),
            # Archived = the row exists in the DB but image_data has been
            # cleared by retention. We say "archived" only when there is
            # NO surviving image_data anywhere in the day's captures.
            "entry_image_archived": entry_image_snap is None and len(snaps_sorted) > 0,
            "exit_image_archived": (
                (not only_one) and exit_image_snap is None and len(snaps_sorted) > 0
            ),
            "missing_checkout": missing_checkout,
            "is_active": is_active,
            "correction_applied": correction_applied,
            "paid_leave": paid_leave_flag,
            "lop": lop_flag,
            "wfh": wfh_flag,
        })

    seen = {r["name"].lower() for r in records}

    def _absent_or_corrected_row(display: str) -> dict:
        """Build a no-capture row, applying any correction for this day."""
        corr = (corrections or {}).get((display.lower(), target_date.isoformat()))
        override_status = (corr.get("status_override") if corr else None) or "Absent"
        pl = bool(int(corr.get("paid_leave") or 0)) if corr else False
        lp = bool(int(corr.get("lop") or 0)) if corr else False
        wf = bool(int(corr.get("wfh") or 0)) if corr else False
        return {
            "name": display,
            "date": target_date.isoformat(),
            "entry": None,
            "exit": None,
            "entry_iso": None,
            "exit_iso": None,
            "total_hours": "—",
            "total_working_hours": "—",
            "total_minutes": 0,
            "total_working_seconds": 0,
            "total_break_seconds": 0,
            "total_break_time": "—",
            "break_details": [],
            "movement_history": [],
            "status": override_status,
            "late_minutes": 0,
            "late_seconds": 0,
            "early_exit_minutes": 0,
            "early_exit_seconds": 0,
            "capture_count": 0,
            "entry_image_url": None,
            "exit_image_url": None,
            "entry_image_archived": False,
            "exit_image_archived": False,
            "missing_checkout": False,
            "is_active": False,
            "correction_applied": bool(corr),
            "paid_leave": pl,
            "lop": lp,
            "wfh": wf,
        }

    if expected_names:
        for raw in expected_names:
            normalized = _normalize_name(raw)
            if not normalized or normalized.lower() in seen:
                continue
            records.append(_absent_or_corrected_row(normalized))
            seen.add(normalized.lower())

    # Surface correction-only days even when expected_names wasn't supplied
    # (e.g. /api/attendance/range filtered to a single employee). Without
    # this, an HR-marked Paid Leave / WFH / LOP for a day with no captures
    # would silently disappear from the response.
    if corrections:
        target_iso = target_date.isoformat()
        for (key, c_date), corr in corrections.items():
            if c_date != target_iso or key in seen:
                continue
            records.append(_absent_or_corrected_row(corr.get("name") or key))
            seen.add(key)

    records.sort(key=lambda r: (r["status"] == "Absent", r["name"].lower()))
    return records


def build_range_records(
    snapshots: Iterable[Snapshot],
    *,
    start_date: date_cls,
    end_date: date_cls,
    shift: ShiftSettings,
    base_url: str,
    name_filter: Optional[str] = None,
    corrections: Optional[dict[tuple[str, str], dict]] = None,
    rollups: Optional[dict[tuple[str, str], dict]] = None,
    cam_types: Optional[dict[str, str]] = None,
) -> list[dict]:
    """Daily records across a date range. If `name_filter` is given, only
    that person's days are returned (case-insensitive, ignores extra spaces).
    """
    snaps_list = list(snapshots)
    if name_filter:
        target = _normalize_name(name_filter).lower()
        snaps_list = [s for s in snaps_list if _normalize_name(s.name).lower() == target]

    out: list[dict] = []
    cursor = start_date
    while cursor <= end_date:
        out.extend(
            build_daily_records(
                snaps_list,
                target_date=cursor,
                shift=shift,
                base_url=base_url,
                corrections=corrections,
                rollups=rollups,
                cam_types=cam_types,
            )
        )
        cursor += timedelta(days=1)

    out.sort(key=lambda r: (r["date"], r["name"].lower()))
    return out
