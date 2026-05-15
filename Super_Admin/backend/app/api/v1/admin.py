from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import (
    get_camera_manager,
    get_company_scope,
    get_current_admin,
    get_db,
    require_roles,
)
from app.core.constants import Role, SessionStatus
from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.core.security import hash_password
from app.models.admin import Admin
from app.repositories.admin_repo import AdminRepository
from app.repositories.camera_repo import CameraRepository
from app.repositories.daily_attendance_repo import DailyAttendanceRepository
from app.repositories.employee_repo import EmployeeRepository
from app.repositories.event_repo import EventRepository
from app.schemas.admin import LiveWorkerStatus, StatsResponse
from app.schemas.auth import HrAccountCreate, HrAccountRead
from app.schemas.dashboard import (
    DashboardResponse,
    HourBucketSchema,
    PresenceStatus,
    TimelineItemSchema,
)
from app.services.dashboard_service import DashboardService
from app.services.realtime_bus import bus as realtime_bus
from app.utils.time_utils import now_local, now_utc
from app.workers.camera_manager import CameraManager

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=StatsResponse)
def stats(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
    scoped_company: str | None = Depends(get_company_scope),
) -> StatsResponse:
    employee_repo = EmployeeRepository(db)
    camera_repo = CameraRepository(db)
    daily_repo = DailyAttendanceRepository(db)
    event_repo = EventRepository(db)

    today = now_local().date()
    status_counts = daily_repo.count_by_status_for_date(today, company=scoped_company)
    since = now_utc() - timedelta(hours=24)

    if scoped_company is not None:
        # Only the company's own employees, but cameras are global —
        # show 0 cameras to HR users so the field doesn't read confusingly.
        _items, total_emp = employee_repo.search(
            query=None,
            is_active=None,
            department=None,
            company=scoped_company,
            limit=1,
            offset=0,
        )
        # Use search.total which already counts; for active_employees
        # run a second narrow search.
        _, active_emp = employee_repo.search(
            query=None,
            is_active=True,
            department=None,
            company=scoped_company,
            limit=1,
            offset=0,
        )
        _events_company, _ = event_repo.list_filtered(
            employee_id=None,
            camera_id=None,
            event_type=None,
            start=since,
            end=None,
            company=scoped_company,
            limit=1,
            offset=0,
        )
        # We want the COUNT, not the rows — re-derive via filter total.
        _, events_24h_count = event_repo.list_filtered(
            employee_id=None,
            camera_id=None,
            event_type=None,
            start=since,
            end=None,
            company=scoped_company,
            limit=1,
            offset=0,
        )
        return StatsResponse(
            total_employees=total_emp,
            active_employees=active_emp,
            total_cameras=0,
            active_cameras=0,
            today_present=status_counts.get(SessionStatus.PRESENT, 0),
            today_incomplete=status_counts.get(SessionStatus.INCOMPLETE, 0),
            today_absent=status_counts.get(SessionStatus.ABSENT, 0),
            events_last_24h=events_24h_count,
        )

    return StatsResponse(
        total_employees=employee_repo.count(),
        active_employees=employee_repo.count(only_active=True),
        total_cameras=camera_repo.count(),
        active_cameras=camera_repo.count(only_active=True),
        today_present=status_counts.get(SessionStatus.PRESENT, 0),
        today_incomplete=status_counts.get(SessionStatus.INCOMPLETE, 0),
        today_absent=status_counts.get(SessionStatus.ABSENT, 0),
        events_last_24h=event_repo.count_since(since),
    )


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> DashboardResponse:
    snap = DashboardService(db).snapshot()
    return DashboardResponse(
        as_of=snap.as_of,
        work_date=snap.work_date,
        total_employees=snap.total_employees,
        active_employees=snap.active_employees,
        present_today=snap.present_today,
        absent_today=snap.absent_today,
        incomplete_today=snap.incomplete_today,
        inside_office=snap.inside_office,
        on_break=snap.on_break,
        outside_office=snap.outside_office,
        late_today=snap.late_today,
        early_exit_today=snap.early_exit_today,
        events_last_24h=snap.events_last_24h,
        total_cameras=snap.total_cameras,
        active_cameras=snap.active_cameras,
    )


@router.get("/dashboard/timeline", response_model=list[TimelineItemSchema])
def timeline(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> list[TimelineItemSchema]:
    items = DashboardService(db).timeline(limit=limit, offset=offset)
    return [
        TimelineItemSchema(
            event_id=i.event_id,
            employee_id=i.employee_id,
            employee_code=i.employee_code,
            employee_name=i.employee_name,
            event_type=i.event_type,
            event_time=i.event_time,
            camera_id=i.camera_id,
            camera_name=i.camera_name,
            confidence=i.confidence,
            is_manual=i.is_manual,
            snapshot_available=i.snapshot_available,
        )
        for i in items
    ]


@router.get("/presence", response_model=list[PresenceStatus])
def presence(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> list[PresenceStatus]:
    items = DashboardService(db).presence_list()
    return [
        PresenceStatus(
            employee_id=i.employee_id,
            employee_code=i.employee_code,
            employee_name=i.employee_name,
            department=i.department,
            status=i.status,
            last_event_type=i.last_event_type,
            last_event_time=i.last_event_time,
            last_camera_name=i.last_camera_name,
            last_event_id=i.last_event_id,
        )
        for i in items
    ]


@router.get("/dashboard/events-by-hour", response_model=list[HourBucketSchema])
def dashboard_events_by_hour(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> list[HourBucketSchema]:
    buckets = DashboardService(db).events_by_hour(hours=hours)
    return [HourBucketSchema(bucket_start=b.bucket_start, count=b.count) for b in buckets]


@router.get("/live-status", response_model=list[LiveWorkerStatus])
def live_status(
    manager: CameraManager = Depends(get_camera_manager),
    _: Admin = Depends(get_current_admin),
) -> list[LiveWorkerStatus]:
    return [LiveWorkerStatus(**s) for s in manager.status()]


# ----------------------------------------------------------------------
# HR account management — super-admin only
# ----------------------------------------------------------------------


@router.post(
    "/hr-accounts",
    response_model=HrAccountRead,
    status_code=201,
)
def create_hr_account(
    payload: HrAccountCreate,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN)),
) -> HrAccountRead:
    """Create an HR-role admin account scoped to one company. Username
    must be unique. Company string should match `Employee.company`
    exactly (case-sensitive) — that's how the HR dashboard's data
    scoping works.
    """
    repo = AdminRepository(db)
    if repo.get_by_username(payload.username) is not None:
        raise AlreadyExistsError(f"Username '{payload.username}' is already taken")
    hr = Admin(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=Role.HR,
        is_active=True,
        company=payload.company.strip(),
    )
    repo.add(hr)
    realtime_bus.publish(
        "hr_account",
        kind="created",
        account_id=hr.id,
        company=hr.company,
    )
    return HrAccountRead.model_validate(hr)


@router.get("/hr-accounts", response_model=list[HrAccountRead])
def list_hr_accounts(
    db: Session = Depends(get_db),
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN)),
) -> list[HrAccountRead]:
    items = AdminRepository(db).list_by_role(Role.HR)
    return [HrAccountRead.model_validate(i) for i in items]


@router.delete("/hr-accounts/{account_id}", status_code=204, response_model=None)
def delete_hr_account(
    account_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN)),
) -> None:
    """Hard-delete an HR account so its username can be reused. The HR
    account doesn't own attendance data — only employees and events do —
    so it's safe to remove the row outright."""
    repo = AdminRepository(db)
    acct = repo.get(account_id)
    if acct is None or acct.role != Role.HR:
        raise NotFoundError(f"HR account {account_id} not found")
    company = acct.company
    repo.delete(acct)
    realtime_bus.publish(
        "hr_account",
        kind="deleted",
        account_id=account_id,
        company=company,
    )
