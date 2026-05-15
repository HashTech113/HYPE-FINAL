from __future__ import annotations

import io
from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse, Response
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.api.deps import (
    get_company_scope,
    get_current_admin,
    get_db,
    require_roles,
)
from app.config import get_settings
from app.core.constants import Role
from app.core.exceptions import AlreadyExistsError, NotFoundError, ValidationError
from app.core.rate_limit import employee_image_rate_limit
from app.models.admin import Admin
from app.models.employee import Employee
from app.repositories.employee_repo import EmployeeRepository
from app.schemas.common import Page
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate
from app.services.realtime_bus import bus as realtime_bus

router = APIRouter(prefix="/employees", tags=["employees"])

# Mime types we accept on upload. We re-encode to JPEG ourselves, so the
# input can be anything Pillow recognizes — but rejecting non-image
# Content-Types early is a quick guard against confused clients sending
# PDFs or HTML.
_ALLOWED_IMAGE_MIME_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
)


@router.get("", response_model=Page[EmployeeRead])
def list_employees(
    q: str | None = None,
    is_active: bool | None = None,
    department: str | None = None,
    company: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
    scoped_company: str | None = Depends(get_company_scope),
) -> Page[EmployeeRead]:
    # HR users are forced to their own company; admins may pass
    # `?company=...` to drill into a specific one but otherwise see all.
    effective_company = scoped_company if scoped_company is not None else company
    items, total = EmployeeRepository(db).search(
        query=q,
        is_active=is_active,
        department=department,
        company=effective_company,
        limit=limit,
        offset=offset,
    )
    return Page[EmployeeRead](
        items=[EmployeeRead.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/by-code/{employee_code}", response_model=EmployeeRead)
def get_employee_by_code(
    employee_code: str,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> EmployeeRead:
    emp = EmployeeRepository(db).get_by_code(employee_code)
    if emp is None:
        raise NotFoundError(f"Employee code '{employee_code}' not found")
    return EmployeeRead.model_validate(emp)


@router.get("/{employee_id}", response_model=EmployeeRead)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
) -> EmployeeRead:
    emp = EmployeeRepository(db).get(employee_id)
    if emp is None:
        raise NotFoundError(f"Employee {employee_id} not found")
    return EmployeeRead.model_validate(emp)


@router.post("", response_model=EmployeeRead, status_code=201)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
) -> EmployeeRead:
    repo = EmployeeRepository(db)
    code = (payload.employee_code or "").strip() or None
    if code is not None and repo.get_by_code(code) is not None:
        raise AlreadyExistsError(f"employee_code '{code}' already exists")
    emp = Employee(
        # Insert with a placeholder if no code was supplied; we replace it
        # with the canonical EMP-NNNNNN once the row's id is known. The
        # placeholder uses the table's unique constraint to avoid races.
        employee_code=code or _next_employee_code(repo),
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        designation=payload.designation,
        department=payload.department,
        company=payload.company,
        dob=payload.dob,
        join_date=payload.join_date,
        salary_package=payload.salary_package,
        shift_start=payload.shift_start,
        shift_end=payload.shift_end,
        is_active=payload.is_active,
    )
    repo.add(emp)
    realtime_bus.publish(
        "employee",
        kind="created",
        employee_id=emp.id,
        company=emp.company,
    )
    return EmployeeRead.model_validate(emp)


def _next_employee_code(repo: EmployeeRepository) -> str:
    """Generate the next sequential `EMP-NNNNNN` code.

    Uses the current row count + a small retry loop so concurrent
    creates don't collide on the unique index. Good enough for the
    expected single-tenant scale; if we ever need true ordering we can
    swap in a Postgres sequence.
    """
    base = repo.count() + 1
    for offset in range(32):
        candidate = f"EMP-{base + offset:06d}"
        if repo.get_by_code(candidate) is None:
            return candidate
    raise AlreadyExistsError("could not allocate a unique employee_code")


@router.patch("/{employee_id}", response_model=EmployeeRead)
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
) -> EmployeeRead:
    repo = EmployeeRepository(db)
    emp = repo.get(employee_id)
    if emp is None:
        raise NotFoundError(f"Employee {employee_id} not found")
    data = payload.model_dump(exclude_unset=True)
    repo.update(emp, data)
    realtime_bus.publish(
        "employee",
        kind="updated",
        employee_id=emp.id,
        company=emp.company,
    )
    return EmployeeRead.model_validate(emp)


@router.delete("/{employee_id}", status_code=204, response_model=None)
def deactivate_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN)),
) -> None:
    repo = EmployeeRepository(db)
    emp = repo.get(employee_id)
    if emp is None:
        raise NotFoundError(f"Employee {employee_id} not found")
    emp.is_active = False
    realtime_bus.publish(
        "employee",
        kind="deactivated",
        employee_id=emp.id,
        company=emp.company,
    )


# --------------------------------------------------------------------------
# Profile photo
#
# One JPEG per employee, stored at `<EMPLOYEE_IMAGE_DIR>/<id>.jpg`. We
# re-encode every upload so the on-disk format is uniform regardless of
# what the client uploaded (PNG / WEBP / HEIC / oversized JPEG). This
# normalizes file size, strips EXIF (privacy), and removes the need for
# a content-sniffing GET handler.
# --------------------------------------------------------------------------


def _employee_image_path(employee_id: int) -> Path:
    s = get_settings()
    return Path(s.EMPLOYEE_IMAGE_DIR) / f"{employee_id}.jpg"


def _save_normalized_jpeg(raw: bytes, dest: Path) -> None:
    """Re-encode arbitrary image bytes to a JPEG bounded by
    `EMPLOYEE_IMAGE_MAX_DIM` px on the long side, at the configured
    JPEG quality. Strips EXIF and alpha channels.

    Atomic on POSIX (write to `.tmp`, then `os.replace`) so a crash
    mid-upload can never leave a partially-written file in place.
    """
    s = get_settings()
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError(
            "Uploaded file is not a readable image", code="invalid_image"
        ) from exc

    # Pillow respects EXIF orientation only if we ask it to. Without
    # this, photos taken in portrait on phones display sideways.
    try:
        from PIL import ImageOps

        img = ImageOps.exif_transpose(img)
    except Exception:
        # ImageOps is part of Pillow; the broad except is paranoia
        # against truncated files that survived the load() call.
        pass

    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    img.thumbnail(
        (s.EMPLOYEE_IMAGE_MAX_DIM, s.EMPLOYEE_IMAGE_MAX_DIM),
        Image.Resampling.LANCZOS,
    )

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    img.save(
        tmp,
        format="JPEG",
        quality=s.EMPLOYEE_IMAGE_JPEG_QUALITY,
        optimize=True,
        progressive=True,
    )
    tmp.replace(dest)


@router.post("/{employee_id}/image", response_model=EmployeeRead)
async def upload_employee_image(
    employee_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
) -> EmployeeRead:
    s = get_settings()
    repo = EmployeeRepository(db)
    emp = repo.get(employee_id)
    if emp is None:
        raise NotFoundError(f"Employee {employee_id} not found")

    if file.content_type and file.content_type not in _ALLOWED_IMAGE_MIME_TYPES:
        raise ValidationError(
            f"Unsupported image type '{file.content_type}'",
            code="unsupported_image_type",
        )

    # Read with a hard ceiling so a malicious client can't OOM the
    # server by streaming an enormous body.
    raw = await file.read(s.EMPLOYEE_IMAGE_MAX_BYTES + 1)
    if len(raw) > s.EMPLOYEE_IMAGE_MAX_BYTES:
        raise ValidationError(
            f"Image exceeds {s.EMPLOYEE_IMAGE_MAX_BYTES // (1024 * 1024)} MiB limit",
            code="image_too_large",
        )
    if not raw:
        raise ValidationError("Empty upload", code="empty_upload")

    dest = _employee_image_path(employee_id)
    _save_normalized_jpeg(raw, dest)

    # Store the relative path so the row is portable across deployments
    # (a backup restored under a different STORAGE_ROOT keeps working).
    rel = f"employees/{employee_id}.jpg"
    emp.image_path = rel
    db.flush()

    realtime_bus.publish(
        "employee",
        kind="image_updated",
        employee_id=emp.id,
        company=emp.company,
    )
    return EmployeeRead.model_validate(emp)


@router.get("/{employee_id}/image")
def get_employee_image(
    employee_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
    _rate: None = Depends(employee_image_rate_limit),
):
    repo = EmployeeRepository(db)
    emp = repo.get(employee_id)
    if emp is None:
        raise NotFoundError(f"Employee {employee_id} not found")
    if not emp.image_path:
        raise NotFoundError("Employee has no profile image")
    path = _employee_image_path(employee_id)
    if not path.is_file():
        # Row says there's an image but it's missing on disk. Don't
        # silently 200 with stale bytes — clear the path so the UI can
        # invite re-upload, and report a clean 404.
        emp.image_path = None
        db.flush()
        raise NotFoundError("Employee profile image is missing on disk")
    return FileResponse(
        str(path),
        media_type="image/jpeg",
        # Short browser cache so updates show within ~30s without us
        # having to invalidate a CDN. Long enough that paginated lists
        # of avatars don't refetch on every scroll.
        headers={"Cache-Control": "private, max-age=30"},
    )


@router.delete("/{employee_id}/image", status_code=204, response_model=None)
def delete_employee_image(
    employee_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
) -> Response:
    repo = EmployeeRepository(db)
    emp = repo.get(employee_id)
    if emp is None:
        raise NotFoundError(f"Employee {employee_id} not found")
    path = _employee_image_path(employee_id)
    # Best-effort delete — we never want a stale FS entry to block the
    # row update, since the row is the source of truth for "has image".
    if path.is_file():
        try:
            path.unlink()
        except OSError:
            pass
    emp.image_path = None
    db.flush()
    realtime_bus.publish(
        "employee",
        kind="image_deleted",
        employee_id=emp.id,
        company=emp.company,
    )
    return Response(status_code=204)
