# Camera Capture API

FastAPI service that:

- Polls the camera's real-time AI event API (`POST /API/AI/processAlarm/Get`) — see [../API/processAlarm_get.md](../API/processAlarm_get.md)
- POSTs each new face capture to `/api/ingest`, which stores it in the database (name, timestamp, `image_data` base64)
- Serves attendance summaries, snapshot logs, and the employee roster to the React dashboard

**The database is the single source of truth.** Local dev uses SQLite by default; production uses PostgreSQL via `DATABASE_URL`. Captures are stored inline as base64 in `snapshot_logs.image_data` / `attendance_logs.image_data`. There is no filesystem snapshot store any more — the backend does not read or write JPEGs on disk.

## Overall workflow

1. `start.sh` starts the FastAPI app (`uvicorn`) and background workers (`capture.py`, `backfill_from_camera.py`, and optional replay sync loops).
2. `capture.py` polls the camera endpoint `POST /API/AI/processAlarm/Get` every few seconds.
3. For each detected face event, `capture.py` sends a payload to `POST /api/ingest`.
4. `/api/ingest` normalizes timestamp + image identity and writes to the database:
   - every event goes to `snapshot_logs`
   - recognized names (not `Unknown`) are also written to `attendance_logs`
5. Dashboard/read APIs fetch from the database:
   - `/api/snapshots` for raw capture stream
   - `/api/attendance*` for attendance summaries
   - `/api/health`, `/api/faces/history`, `/api/employees` for monitoring/history/roster
6. Retention cleanup keeps rows but may clear old `image_data` blobs to reduce DB size.
7. Optional replay sync (`replay_to_railway.py`) forwards local rows to remote ingest targets for backup/centralization.

## Layout

```text
backend/
├── app/
│   ├── __init__.py
│   ├── config.py                    ← env/default settings
│   ├── db.py                        ← SQLAlchemy engine/session (SQLite or PostgreSQL)
│   ├── dependencies.py              ← auth/API-key dependency guards
│   ├── main.py                      ← FastAPI app factory + router wiring
│   ├── upgrade.py                   ← startup migrations/backfills
│   ├── models/                      ← ORM models (users, employees, cameras, logs, lookups)
│   ├── routers/
│   │   ├── auth.py                  ← /api/auth/*
│   │   ├── health.py                ← /api/health
│   │   ├── faces.py                 ← /api/faces/history
│   │   ├── attendance.py            ← /api/attendance/config|daily|range
│   │   ├── logs.py                  ← /api/attendance + /api/snapshots
│   │   ├── corrections.py           ← /api/attendance/corrections
│   │   ├── employees.py             ← /api/employees CRUD
│   │   ├── cameras.py               ← /api/cameras CRUD/check/stream
│   │   ├── ingest.py                ← /api/ingest + /api/ingest/last-seen
│   │   ├── external_attendance.py   ← /api/external-attendance/sync
│   │   └── admin.py                 ← /api/admin/* utilities
│   ├── schemas/                     ← pydantic request/response models
│   └── services/                    ← business logic, camera I/O, cleanup, crypto, lookups
├── scripts/
│   └── migrate_sqlite_to_postgres.py ← one-shot SQLite → PostgreSQL migration utility
├── capture.py                       ← camera poller, posts detections to ingest endpoint(s)
├── backfill_from_camera.py          ← camera-history backfill runner
├── replay_to_railway.py             ← periodic replay sync to remote ingest
├── data/
│   └── employees.json               ← first-boot employee seed
├── database.db                      ← local SQLite DB (dev fallback)
├── start.sh                         ← supervisor for API + workers
└── requirements.txt
```

## Setup

### Ubuntu / Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

### Backend only (local, recommended)

Ubuntu / Linux:

```bash
bash backend/start.sh
```

Windows:

- Use **Git Bash** or **WSL** for `bash backend/start.sh`, or
- Run the manual PowerShell commands below.

`start.sh` supervises `uvicorn`, `capture.py`, `backfill_from_camera.py`, and optional replay sync loops. If not set, `INGEST_API_URL` defaults to the production Railway ingest URL.

### Two terminals (manual)

Ubuntu / Linux:

```bash
# terminal 1 — API
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# terminal 2 — capture
cd backend && source .venv/bin/activate && python capture.py
```

Windows (PowerShell):

```powershell
# terminal 1 — API
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# terminal 2 — capture
cd backend
.\.venv\Scripts\Activate.ps1
python capture.py
```

`capture.py` always writes to the local DB through `/api/ingest` when running with the API. Set `INGEST_API_URL` only for optional remote replication (comma-separated targets):

```bash
INGEST_API_URL=https://hype-dashboard-production-8938.up.railway.app/api/ingest \
  python capture.py
```

## Endpoints

- `GET /api/health`
- `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/change-password`, `PUT /api/auth/profile`
- `GET/POST/PUT/DELETE /api/employees`
- `GET /api/faces/history`
- `GET /api/attendance/config`, `GET /api/attendance/daily`, `GET /api/attendance/range`
- `GET /api/attendance`, `GET /api/snapshots`
- `GET/POST/DELETE /api/attendance/corrections`
- `POST /api/ingest`, `GET /api/ingest/last-seen`
- `GET/POST/PUT/DELETE /api/cameras...` (+ check/stream-token/stream)
- `POST /api/external-attendance/sync` (admin)
- `POST/DELETE /api/admin/...` (rename/discover/prune/backfill/correction helpers)

Example:

### `GET /api/health`

```json
{ "status": "ok", "snapshot_count": 1801 }
```

Data is served from the configured DB backend (SQLite locally, PostgreSQL in production).

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | *(unset)* | Production DB URL (PostgreSQL) |
| `DATABASE_PATH` | `backend/database.db` | Local SQLite file path (fallback when `DATABASE_URL` is empty) |
| `APP_ENV` | `development` | `production` blocks SQLite fallback |
| `JWT_SECRET` | `dev-only-change-me-in-production` | JWT signing secret |
| `JWT_TTL_SECONDS` | `43200` | Access token lifetime (12h) |
| `SEED_ADMIN_USERNAME` | `admin` | First-boot admin username seed |
| `SEED_ADMIN_PASSWORD` | `admin@123` | First-boot admin password seed |
| `INGEST_API_KEY` | *(empty)* | Required `X-API-Key` for `POST /api/ingest` |
| `CAMERA_HOST` | `172.18.10.12` | Camera IP / hostname |
| `CAMERA_USER` | `admin` | Login username |
| `CAMERA_PASS` | *(empty)* | Login password (must be set in env) |
| `CAMERA_MAC` | *(empty)* | Optional MAC pin for camera rediscovery |
| `CAMERA_DISCOVERY_SUBNETS` | derived from `CAMERA_HOST` | Comma-separated `/24` prefixes to scan |
| `CAPTURE_INTERVAL_SECONDS` | `5` | Seconds between `processAlarm/Get` polls |
| `REQUEST_TIMEOUT_SECONDS` | `30` | HTTP timeout for camera calls |
| `INGEST_API_URL` | *(unset)* | Optional comma-separated remote ingest target(s) for replication |
| `REMOTE_SYNC_URLS` | Railway ingest URL | replay sync target(s) in `start.sh` |
| `REMOTE_SYNC_INTERVAL` | `300` | Seconds between replay sync passes |
| `DEFAULT_HISTORY_START` | `2026-04-15` | Fallback `start` for `/api/faces/history` |
| `DEFAULT_PAGE_LIMIT` | `50` | Default `limit` for list endpoints |
| `MAX_PAGE_LIMIT` | `500` | Max `limit` / `latest` |
| `SHIFT_START` | `09:30` | Local shift start |
| `SHIFT_END` | `18:30` | Local shift end |
| `LATE_GRACE_MIN` | `15` | Minutes of grace before a late arrival |
| `EARLY_EXIT_GRACE_MIN` | `5` | Minutes of grace before an early exit |
| `LOCAL_TZ_OFFSET_MIN` | `330` | Local timezone offset from UTC |
| `BREAK_GAP_THRESHOLD_MIN` | `30` | Minimum gap treated as break duration |
| `EXTERNAL_ATTENDANCE_API_URL` | *(unset)* | External attendance API base URL |
| `EXTERNAL_ATTENDANCE_API_KEY` | *(unset)* | External attendance API auth key |
| `ALLOWED_ORIGINS` | *(unset)* | Extra CORS origins, comma-separated |

## Deploying to Railway

Use Railway Postgres and set `DATABASE_URL`. In production mode the backend refuses SQLite fallback when `DATABASE_URL` is missing.

Required Railway env vars:
- `DATABASE_URL` (from Railway Postgres plugin)
- `JWT_SECRET` (strong random value)
- `INGEST_API_KEY` (shared with capture/replay producers)
- `CAMERA_PASS` (if this deploy talks directly to the camera)
- `INGEST_API_URL` (only if you run `capture.py` inside the same service — otherwise the LAN machine running capture posts directly to Railway's `/api/ingest`)
- `ALLOWED_ORIGINS` if your frontend runs on a host not already in the regex allowlist

Checklist for a clean deploy:
1. Attach Railway Postgres and confirm `DATABASE_URL` is present.
2. (Optional one-time migration) run `python -m scripts.migrate_sqlite_to_postgres --database-url '<postgres-url>'`.
3. Verify `GET /api/health` returns `status: ok`.
4. Point the LAN capture machine at Railway: `INGEST_API_URL=https://<your-service>.up.railway.app/api/ingest`.

## Troubleshooting

| Symptom | First check | Likely cause → fix |
|---|---|---|
| `Camera HTTP error 401` | Credentials + Digest auth | Update `CAMERA_USER` / `CAMERA_PASS`. |
| `Poll returned 0 faces` forever | Stand in front of the camera | This endpoint is a real-time alarm buffer, not a history query. |
| `No image data for SnapId=...` | The `keys=[...]` in the warning | Firmware uses a different image field. Extend `IMAGE_FIELDS` in [app/services/snapshots.py](app/services/snapshots.py). |
| API fails to boot on Railway with DB config error | Service logs on startup | `DATABASE_URL` is missing/invalid while running in production mode. Attach Postgres and set `DATABASE_URL`. |
| Frontend fetch blocked by CORS | Browser devtools network tab | Add origin to `ALLOWED_ORIGINS` env var or to the regex in [app/main.py](app/main.py). |

## Frontend wiring

[../frontend/src/api/dashboardApi.ts](../frontend/src/api/dashboardApi.ts) exports the read/write helpers the dashboard uses. Images come through as `data:` URLs — no special proxy or static mount is required.
