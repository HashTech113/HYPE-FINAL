# Backend project structure

PostgreSQL is the source of truth in production (Railway-hosted). Local dev
falls back to SQLite at `backend/database.db` when `DATABASE_URL` is not
set; production refuses that fallback because `APP_ENV=production`.

## Layout

```
backend/
├── app/
│   ├── main.py                  FastAPI factory, CORS, lifespan
│   ├── config.py                env vars + computed defaults
│   ├── db.py                    SQLAlchemy engine, Session, get_db, dialect-aware upserts
│   ├── upgrade.py               idempotent boot migrations + backfills
│   ├── dependencies.py          require_admin / require_admin_or_hr / API-key guards
│   ├── models/                  ORM models (one file per aggregate)
│   ├── schemas/                 Pydantic request/response shapes
│   ├── routers/                 HTTP layer — one router per feature area
│   └── services/                business logic (DB writes, crypto, lookups)
├── scripts/
│   └── migrate_sqlite_to_postgres.py    one-shot SQLite → PostgreSQL utility
├── data/
│   └── employees.json           first-boot seed only (NOT a live source of truth)
├── capture.py                   camera poller (runs as background worker)
├── backfill_from_camera.py      camera-history backfill runner
├── replay_to_railway.py         optional remote-replay sync
├── start.sh                     supervisor for uvicorn + workers
├── requirements.txt
└── database.db                  local SQLite fallback (gitignored in prod)
```

## Where things go

| Adding... | Put it in | Pattern |
|---|---|---|
| A new HTTP endpoint | `app/routers/<feature>.py` | thin router → calls a service; do not put DB logic in routers |
| Business logic that touches the DB | `app/services/<feature>.py` | wrap each unit of work in `with session_scope()` (background) or `Depends(get_db)` (FastAPI) |
| A request/response shape | `app/schemas/<feature>.py` | Pydantic v2; camelCase fields if the frontend uses camelCase |
| A new ORM table | `app/models/<aggregate>.py` | also re-export from `app/models/__init__.py` so create_all sees it |
| A new column on an existing table | model + `_NEW_COLUMNS` in `app/upgrade.py` | upgrade.py runs `ALTER TABLE ADD COLUMN` for legacy DBs at boot |
| A one-shot operational script | `backend/scripts/<verb>_<object>.py` | not in the FastAPI import graph; safe to import `app.config` etc. |
| A long-running worker | `backend/<worker>.py` (root) | imported by `start.sh`; uses `session_scope()` directly |
| Generic helper utilities | colocate with caller's module, or a small `_helpers.py` | avoid a global `utils/` until it has 3+ consumers |

## Database rules

- All website writes go through `app/services/*` and land in PostgreSQL.
- `data/employees.json` is read **only** when the `employees` table is empty
  on first boot (`seed_if_empty()` in `services/employees.py`). After that,
  the DB is authoritative — JSON edits are ignored.
- Every service uses `Depends(get_db)` (request handlers) or
  `with session_scope()` (workers / scripts). Sessions are short-lived and
  do not span network calls (camera RTSP, external HTTP) — see
  `services/cameras.py::check_connection` and `routers/external_attendance.py`
  for the pattern: do the network call first, then open the session for the
  DB write.

## Common commands

```bash
# fresh local boot (auto-creates SQLite DB)
cd backend && uvicorn app.main:app --reload --port 8000

# boot with workers
bash backend/start.sh

# one-time migration to Railway PG
python -m scripts.migrate_sqlite_to_postgres \
  --rollback-on-error \
  --database-url "$DATABASE_URL"

# refuse SQLite fallback (mimics production guard)
APP_ENV=production python -c "from app.db import engine"

# OpenAPI schema dump
python -c "from app.main import app; import json; print(json.dumps(app.openapi()))"
```

## Railway deploy notes

Required env vars on the backend service:

- `DATABASE_URL` — set automatically by Railway's PostgreSQL plugin
- `APP_ENV=production` — enforces the no-SQLite-fallback guard
- `JWT_SECRET` — long random string, ≥32 chars
- `INGEST_API_KEY` — shared with `capture.py` / `replay_to_railway.py`
- `CAMERA_SECRET_KEY` — Fernet key for camera password encryption
- `EXTERNAL_ATTENDANCE_API_URL` / `EXTERNAL_ATTENDANCE_API_KEY` (optional)

Build / start command is in [nixpacks.toml](../nixpacks.toml). Lifespan
runs `init_db()` (CREATE IF NOT EXISTS) and `upgrade.run()` (idempotent
ALTERs + lookup-table backfills) at every boot, so a fresh Railway PG
plugin gets the schema on the first deploy.

## Naming conventions

| Item | Convention | Example |
|---|---|---|
| Python files | snake_case | `external_attendance.py` |
| Classes | PascalCase | `AttendanceLog`, `EmployeeOut` |
| Functions / vars | snake_case | `record_capture`, `pg_session` |
| Constants | UPPER_SNAKE_CASE | `JWT_TTL_SECONDS`, `_NEW_COLUMNS` |
| Pydantic schemas | PascalCase, suffix by role | `EmployeeCreate`, `EmployeeUpdate`, `EmployeeOut` |
| ORM models | PascalCase, singular | `Employee`, `AttendanceLog` |
| Table names | snake_case, plural | `employees`, `attendance_logs` |
| Service modules | feature singular (no `_service` suffix) | `app/services/employees.py` exports `update`, `create`, etc. |
| Migration scripts | `<verb>_<object>.py` | `migrate_sqlite_to_postgres.py` |

## Why the layout looks this way (and not the deeper nested form)

A common alternative is `app/database/connection.py` + `app/database/session.py` +
`app/database/models/...`, plus per-domain `app/services/employee_service.py` etc.
That extra nesting helps in projects with 50+ models and a dozen teams. With
the current size — 11 tables, ~10 routers, single team — the flat
`app/db.py` + `app/models/<aggregate>.py` + `app/services/<feature>.py`
layout is faster to navigate and matches FastAPI's own examples. Add the
nested structure when (a) `models/` exceeds ~25 files or (b) multiple
"feature packages" need to share private helpers without exposing them as
top-level services.
