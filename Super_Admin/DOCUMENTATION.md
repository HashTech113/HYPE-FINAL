# AI CCTV Attendance System — Complete Documentation

A production-grade, fully **on-premise** office attendance system that uses CCTV cameras and face recognition to automatically log when employees arrive, leave, and take breaks. No cloud services. No paid APIs.

---

## Table of Contents

1. [What It Does (in plain English)](#1-what-it-does-in-plain-english)
2. [System Architecture](#2-system-architecture)
3. [How a Face Becomes an Attendance Record](#3-how-a-face-becomes-an-attendance-record-end-to-end-flow)
4. [The Attendance State Machine](#4-the-attendance-state-machine)
5. [Core Features](#5-core-features)
6. [Backend Layout](#6-backend-layout)
7. [Frontend Layout](#7-frontend-layout)
8. [Database Schema](#8-database-schema-key-tables)
9. [REST API Reference](#9-rest-api-reference-all-paths-prefixed-apiv1)
10. [Setup & Installation](#10-setup--installation)
11. [Configuration Reference](#11-configuration-reference-env)
12. [Roles & Permissions](#12-roles--permissions)
13. [Day-to-Day Operations](#13-day-to-day-operations)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. What It Does (in plain English)

You place 4 IP cameras at the office:

- **2 ENTRY cameras** — pointed at people walking *into* the office
- **2 EXIT cameras** — pointed at people walking *out* of the office

The system continuously watches all 4 streams. When it sees a known employee's face, it automatically records the right kind of event:

| Camera type | What gets recorded |
|---|---|
| ENTRY (first time today) | **IN** — the employee arrived |
| EXIT (after IN)          | **BREAK_OUT** — they stepped out |
| ENTRY (after BREAK_OUT)  | **BREAK_IN** — they came back |
| EXIT (after BREAK_IN)    | **BREAK_OUT** — another break |
| End-of-day job           | trailing **BREAK_OUT** is converted to **OUT** |

Admins use a web dashboard to view live presence, browse events, correct mistakes, download Excel reports, and manage employees and cameras.

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      OFFICE NETWORK (LAN)                        │
│                                                                  │
│   IP Camera 1 ──┐                                                │
│   IP Camera 2 ──┼─ RTSP ─▶  ┌──────────────────────────────┐     │
│   IP Camera 3 ──┤           │       BACKEND SERVER         │     │
│   IP Camera 4 ──┘           │  FastAPI + Python 3.11       │     │
│                             │                              │     │
│                             │  • CameraManager             │     │
│                             │     └─ 1 thread per camera   │     │
│                             │  • InsightFace (buffalo_l)   │     │
│                             │  • EmbeddingCache (in-mem)   │     │
│                             │  • Attendance state machine  │     │
│                             │  • REST API (JWT auth)       │     │
│                             └──────────┬───────────────────┘     │
│                                        │                         │
│                                        ▼                         │
│                             ┌──────────────────────┐             │
│                             │   PostgreSQL 14+     │             │
│                             │   + storage/ folder  │             │
│                             │   (snapshots,        │             │
│                             │    training images,  │             │
│                             │    AI model cache)   │             │
│                             └──────────┬───────────┘             │
│                                        │                         │
│                                        ▼                         │
│                             ┌──────────────────────┐             │
│                             │  FRONTEND (Next.js)  │             │
│                             │  Admin Dashboard     │             │
│                             │  http://host:3000    │             │
│                             └──────────────────────┘             │
└──────────────────────────────────────────────────────────────────┘
```

### Two processes, one box

- **Backend** ([backend/](backend/)) — Python FastAPI server. Runs the camera workers, AI inference, and the REST API. Port `8000`.
- **Frontend** ([frontend/](frontend/)) — Next.js 15 SPA. Admin dashboard. Port `3000`.

Both can run on the same machine. PostgreSQL can be local or remote.

### Internal layers (clean architecture)

```
HTTP request
    │
    ▼
┌─────────────┐
│   API       │  FastAPI routers — HTTP, validation, auth
│  (app/api)  │
└──────┬──────┘
       ▼
┌─────────────┐
│  Services   │  Business logic — recognition, attendance,
│ (app/svcs)  │  daily rollup, reports, training, snapshots
└──────┬──────┘
       ▼
┌─────────────┐
│Repositories │  Database access — one repo per table
│ (app/repos) │
└──────┬──────┘
       ▼
┌─────────────┐
│   Models    │  SQLAlchemy ORM tables
│(app/models) │
└─────────────┘
```

Camera workers ([app/workers/](backend/app/workers/)) live alongside this stack and feed into the **Services** layer (they call `AttendanceService`, `TrainingService`, etc.).

---

## 3. How a Face Becomes an Attendance Record (end-to-end flow)

This is the single most important flow in the system. Follow it once and the rest makes sense.

```
                       ┌─────────────────────┐
                       │   IP Camera (RTSP)  │
                       └──────────┬──────────┘
                                  │  raw frames
                                  ▼
                       ┌─────────────────────┐
                       │     RTSPReader      │   reconnects automatically
                       │  (one per camera)   │   if the stream drops
                       └──────────┬──────────┘
                                  │  1 frame / sec (configurable)
                                  ▼
                       ┌─────────────────────┐
                       │   CameraWorker      │   reader thread keeps preview
                       │   (reader thread)   │   smooth at full FPS
                       └──────────┬──────────┘
                                  │  newest frame
                                  ▼
                       ┌─────────────────────┐
                       │  Detector thread    │   ≈20 detections/sec target
                       │ (sibling thread)    │
                       └──────────┬──────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                ▼                                   ▼
      ┌─────────────────┐               ┌─────────────────────┐
      │  FaceService    │               │  EmbeddingCache     │
      │ (InsightFace)   │               │  (in-memory matrix  │
      │ detect + embed  │               │   of all employees) │
      └────────┬────────┘               └──────────┬──────────┘
               │ face embedding                    │
               └──────────┬────────────────────────┘
                          ▼
                ┌─────────────────────┐
                │ RecognitionService  │   cosine similarity
                │  match()            │   ≥ threshold → matched
                └──────────┬──────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       (no match)                  (matched!)
              │                         │
              ▼                         ▼
   ┌──────────────────┐       ┌──────────────────────┐
   │ UnknownCapture   │       │  CooldownService     │
   │ (optional)       │       │  ≥5 s since last     │
   │ stores for later │       │  event for this emp? │
   │ admin review     │       └──────────┬───────────┘
   └──────────────────┘                  │ yes
                                         ▼
                              ┌──────────────────────┐
                              │ AttendanceService    │
                              │ process_auto_event() │
                              │  • check state       │
                              │  • compute IN/       │
                              │    BREAK_OUT/        │
                              │    BREAK_IN          │
                              │  • save snapshot     │
                              │  • write event       │
                              │  • recompute daily   │
                              │    rollup            │
                              └──────────┬───────────┘
                                         ▼
                              ┌──────────────────────┐
                              │  PostgreSQL          │
                              │  + storage/snapshots │
                              └──────────────────────┘
```

### Key timing facts

- **1 frame per second** is read from each camera (tunable via `camera_fps`).
- **5-second global cooldown** per employee — no matter how many cameras see them, only one event can be created in any 5-second window.
- **Snapshots** are saved only when a real state transition is created (not on every detection).
- **Unknown faces** are silently dropped from attendance, but can be optionally saved for manual review.

---

## 4. The Attendance State Machine

Every employee has one independent state machine **per day**. The current state is determined by their most recent event today.

```
                                    (start of day)
                                         │
                                         ▼
                                    ┌────────┐
                ┌──── ENTRY cam ───▶│   IN   │
                │                   └───┬────┘
                │                       │ EXIT cam
                │                       ▼
                │                ┌──────────────┐
                │                │  BREAK_OUT   │◀─┐
                │                └───────┬──────┘  │
                │                        │ ENTRY   │
                │                        ▼         │
                │                ┌──────────────┐  │ EXIT
                │                │   BREAK_IN   │──┘
                │                └──────────────┘
                │
                │       (manual entry OR end-of-day job
                │        converts trailing BREAK_OUT)
                │                        │
                │                        ▼
                │                   ┌────────┐
                │                   │   OUT  │ ◀── terminal
                │                   └────────┘     no more auto-events
                │                                  for this day
        (next day)
```

Defined in [backend/app/core/constants.py](backend/app/core/constants.py):

```
None       + ENTRY → IN
IN         + EXIT  → BREAK_OUT
BREAK_OUT  + ENTRY → BREAK_IN
BREAK_IN   + EXIT  → BREAK_OUT     (repeat as many times as needed)
```

`OUT` is created two ways only:
1. An admin manually adds an OUT event.
2. The end-of-day **close-day** job converts a trailing `BREAK_OUT` (employee never came back) into `OUT`.

Once `OUT` is recorded, the auto pipeline ignores any further detections of that employee for the rest of the day.

---

## 5. Core Features

### 5.1 Live camera processing
- 4 simultaneous RTSP streams (2 ENTRY + 2 EXIT)
- One dedicated worker thread per camera with auto-reconnect
- Self-healing: a stalled or crashed worker is auto-restarted by the health monitor
- Live MJPEG preview stream + still-frame JPEG endpoint for the dashboard

### 5.2 Face recognition
- InsightFace `buffalo_l` model — detection + 512-d embeddings
- Cosine-similarity matching against an in-memory matrix of all enrolled embeddings
- Configurable match threshold (default `0.45`)
- Configurable minimum face size (rejects far-away faces)
- Quality gate (`FACE_MIN_QUALITY`) — blurry / poorly-lit faces rejected during training

### 5.3 Employee training
- Upload 5–20 face images per employee (multipart upload)
- Or capture directly from a live camera frame
- Or auto-update embeddings from high-confidence recognitions (opt-in)
- Per-image embedding lifecycle — admin can list / delete individual training samples

### 5.4 Attendance logic
- Multi-break state machine (unlimited breaks per day)
- 5-second global cooldown per employee (prevents duplicate events)
- Late-entry tracking with grace minutes (default `09:30 + grace`)
- Early-exit tracking with grace minutes (default `18:30 - grace`)
- Daily rollup: in-time, out-time, total work seconds, total break seconds, break count, late minutes, early-exit minutes
- Manual create / edit / delete events with audit trail (`is_manual`, `corrected_by`)
- Recompute daily rollup on demand for any date range
- Day-close job — converts trailing `BREAK_OUT` to `OUT`, marks day closed
- Day-reopen — clears `is_day_closed` for corrections

### 5.5 Snapshots
- Face crop saved on every state-transition event
- Layout: `storage/snapshots/YYYY/MM/DD/{employee_id}/...jpg`
- Browseable via the **Snapshots** page, or fetchable per event

### 5.6 Unknown faces (optional)
- When enabled, faces that don't match any employee are clustered and stored
- Admins can review clusters and **promote** a cluster into a new employee in one click
- Unrelated clusters can be ignored / merged / re-clustered

### 5.7 Reports
- **Daily** — one workbook per date
- **Monthly** — one workbook per month
- **Date range** — arbitrary span
- **Per-employee** — one workbook for one person across a date range
- All as Excel `.xlsx` (openpyxl)

### 5.8 Admin dashboard (frontend)
- **Dashboard** — live stat cards (total / present / absent / inside / on break / late / early-exit) + event timeline + events-by-hour chart
- **Live** — 4-camera grid with live MJPEG and bounding-box overlays
- **Employees** — CRUD
- **Training** — upload / capture / list / delete face images
- **Cameras** — CRUD + RTSP probe + restart + health
- **Attendance** — events list, manual correction, daily summary
- **Presence** — current inside-office / outside / on-break list
- **Snapshots** — gallery
- **Reports** — one-click Excel downloads
- **Settings** — runtime-tunable thresholds, hours, grace, cooldown, etc.
- **Unknowns** — review and promote unknown face clusters

### 5.9 Security
- JWT bearer authentication on every API
- Role-based access (`SUPER_ADMIN`, `ADMIN`, `HR`, `VIEWER`)
- HR users are scoped to a single company (multi-tenant style restriction)
- Bootstrap super-admin seeded from env on first boot
- Password change endpoint
- Unsafe defaults flagged: change `JWT_SECRET_KEY` and bootstrap password before going live

### 5.10 Runtime-tunable settings
All of these can be changed from the **Settings** page **without restarting the server**:

| Setting | What it controls |
|---|---|
| `face_match_threshold` | minimum cosine similarity to declare a match |
| `recognize_min_face_size_px` | reject tiny faces from recognition |
| `cooldown_seconds` | per-employee event dedup window |
| `camera_fps` | how many frames/sec each worker reads |
| `work_start_time` / `work_end_time` | office hours for late/early calc |
| `grace_minutes` / `early_exit_grace_minutes` | tolerance windows |
| `auto_update_enabled` / `auto_update_threshold` | learn-on-the-fly toggle |
| `unknown_capture_enabled` | save unrecognized faces for review |

---

## 6. Backend Layout

```
backend/
├── alembic.ini
├── requirements.txt
├── .env.example
├── migrations/                       # Alembic migrations (versioned schema)
│   └── versions/0001 … 0005_*.py
├── storage/                          # created at runtime
│   ├── models/                       # InsightFace model cache
│   ├── training_images/{code}/*.jpg  # raw training images
│   └── snapshots/YYYY/MM/DD/*.jpg    # event snapshots
├── logs/
│   └── app.log                       # rotating
└── app/
    ├── main.py                       # FastAPI app + lifespan
    ├── config.py                     # env-loaded settings
    │
    ├── api/v1/                       # HTTP routes — one file per resource
    │   ├── auth.py
    │   ├── employees.py
    │   ├── training.py
    │   ├── cameras.py
    │   ├── attendance.py
    │   ├── snapshots.py
    │   ├── recognition.py
    │   ├── reports.py
    │   ├── settings.py
    │   ├── unknowns.py
    │   └── admin.py                  # stats, dashboard, presence, live status
    │
    ├── core/                         # constants, exceptions, logger, security
    ├── db/                           # SQLAlchemy session + base
    │
    ├── models/                       # ORM entities
    │   admin, employee, camera,
    │   attendance_event, daily_attendance,
    │   face_image, face_embedding,
    │   unknown_face, attendance_settings
    │
    ├── repositories/                 # one per table — all DB queries live here
    ├── schemas/                      # Pydantic request/response models
    │
    ├── services/                     # business logic
    │   auth_service, attendance_service,
    │   daily_attendance_service, recognition_service,
    │   face_service, embedding_cache, training_service,
    │   snapshot_service, dashboard_service, report_service,
    │   settings_service, cooldown_service, preview_service,
    │   unknown_capture_service, unknown_promotion_service,
    │   unknown_recluster_service, unknown_purge_service
    │
    ├── utils/                        # face_quality, image_utils, time_utils, excel_utils
    │
    └── workers/                      # background camera processing
        camera_manager, camera_worker, rtsp_reader, rtsp_probe
```

### Process-wide singletons

These are created once at app startup ([backend/app/main.py](backend/app/main.py)) and shared between API requests and camera threads:

- **`FaceService`** — wraps InsightFace; thread-safe detect + embed
- **`EmbeddingCache`** — in-memory `numpy` matrix of all enrolled embeddings, refreshed when training changes
- **`CameraManager`** — owns the worker threads, restarts unhealthy ones

---

## 7. Frontend Layout

```
frontend/
├── app/                              # Next.js 15 App Router
│   ├── layout.tsx                    # root providers
│   ├── globals.css
│   ├── page.tsx                      # → redirects to /dashboard
│   ├── (auth)/login/page.tsx         # public login
│   └── (dashboard)/                  # protected shell
│       ├── layout.tsx                # auth gate + sidebar + topbar
│       ├── dashboard/page.tsx        # live stats + timeline
│       ├── live/page.tsx             # 4-camera live grid (MJPEG)
│       ├── employees/page.tsx
│       ├── training/page.tsx
│       ├── cameras/page.tsx
│       ├── attendance/page.tsx
│       ├── attendance/summary/page.tsx
│       ├── presence/page.tsx
│       ├── snapshots/page.tsx
│       ├── reports/page.tsx
│       ├── settings/page.tsx
│       └── unknowns/page.tsx
│
├── components/
│   ├── ui/                           # ShadCN primitives
│   ├── layout/                       # sidebar, topbar, theme toggle
│   ├── auth/                         # login form
│   ├── dashboard/                    # stat grid, timeline
│   ├── shared/                       # reusable
│   └── providers.tsx                 # Theme + React Query + Auth + Toaster
│
├── lib/
│   ├── api/                          # axios client + per-feature fetchers
│   ├── auth/                         # cookie helpers + auth context
│   ├── hooks/                        # TanStack Query hooks
│   ├── types/                        # mirrors of backend Pydantic schemas
│   └── utils.ts
│
├── middleware.ts                     # route guard — redirects /login if no cookie
├── next.config.mjs
├── tailwind.config.ts
└── package.json
```

### Key technical choices

- **JWT** stored in an `aa_token` cookie (read by middleware on every request)
- **TanStack Query** for all server state — dashboard polls every 10–15 s
- **Axios** with one shared instance — interceptor injects `Authorization: Bearer <token>` and handles 401
- **react-hook-form + zod** for forms
- **Tailwind + ShadCN UI + lucide-react** for design
- **next-themes** for dark mode
- **recharts** for the events-by-hour chart

---

## 8. Database Schema (key tables)

| Table | Purpose |
|---|---|
| `admins` | user accounts that log into the dashboard |
| `employees` | the people whose attendance is tracked |
| `cameras` | registered RTSP cameras (ENTRY / EXIT) |
| `face_images` | raw uploaded training photos per employee |
| `face_embeddings` | 512-d vectors derived from face_images |
| `attendance_events` | every IN / BREAK_OUT / BREAK_IN / OUT event |
| `daily_attendance` | per-employee per-day summary (rollup) |
| `unknown_faces` | optional — captures of unrecognized faces |
| `attendance_settings` | single row of runtime-tunable settings |

### Important relationships

- `attendance_events.employee_id → employees.id`
- `attendance_events.camera_id → cameras.id`
- `attendance_events.corrected_by → admins.id` (set when manually edited)
- `face_embeddings.face_image_id → face_images.id`
- `daily_attendance` has a unique `(employee_id, work_date)` constraint

### Migration tool

Alembic ([backend/migrations/](backend/migrations/)) — apply with:
```bash
alembic upgrade head
```

---

## 9. REST API Reference (all paths prefixed `/api/v1`)

### Auth — [auth.py](backend/app/api/v1/auth.py)
| Method | Path | Roles | Purpose |
|---|---|---|---|
| `POST` | `/auth/login` | public | exchange username+password for JWT |
| `GET`  | `/auth/me` | any | current admin profile |
| `POST` | `/auth/change-password` | any | change own password |

### Employees — [employees.py](backend/app/api/v1/employees.py)
| Method | Path | Roles |
|---|---|---|
| `GET`    | `/employees` | any |
| `GET`    | `/employees/{id}` | any |
| `GET`    | `/employees/by-code/{code}` | any |
| `POST`   | `/employees` | ADMIN+ |
| `PATCH`  | `/employees/{id}` | ADMIN+ |
| `DELETE` | `/employees/{id}` | SUPER_ADMIN (soft delete: `is_active=false`) |

### Training — [training.py](backend/app/api/v1/training.py)
| Method | Path | Purpose |
|---|---|---|
| `GET`    | `/employees/{id}/training/images` | list training images |
| `GET`    | `/employees/{id}/training/embeddings` | list embeddings |
| `POST`   | `/employees/{id}/training/images` | multipart upload (5–20 images) |
| `POST`   | `/employees/{id}/training/capture` | capture from a live camera |
| `POST`   | `/employees/{id}/training/rebuild-cache` | rebuild in-memory embedding matrix |
| `DELETE` | `/employees/{id}/training/images/{image_id}` | remove a single training image |

### Cameras — [cameras.py](backend/app/api/v1/cameras.py)
| Method | Path | Purpose |
|---|---|---|
| `GET`    | `/cameras` | list |
| `GET`    | `/cameras/{id}` | get |
| `POST`   | `/cameras` | create + auto-start worker |
| `PATCH`  | `/cameras/{id}` | update + restart worker |
| `DELETE` | `/cameras/{id}` | deactivate + stop worker |
| `POST`   | `/cameras/{id}/restart` | force-restart worker |
| `POST`   | `/cameras/probe` | test if an RTSP URL is reachable |
| `GET`    | `/cameras/health` | per-camera live health |
| `GET`    | `/cameras/{id}/preview.jpg` | latest annotated still |
| `GET`    | `/cameras/{id}/preview.mjpg?token=…` | live MJPEG stream |

### Attendance — [attendance.py](backend/app/api/v1/attendance.py)
| Method | Path | Purpose |
|---|---|---|
| `GET`    | `/attendance/events` | filter events by employee/camera/type/date |
| `GET`    | `/attendance/events/detailed` | same but joined with employee + camera names |
| `GET`    | `/attendance/events/today?employee_id=…` | today only |
| `POST`   | `/attendance/events` | manual event (audited) |
| `PATCH`  | `/attendance/events/{id}` | edit event (audited) |
| `DELETE` | `/attendance/events/{id}` | delete event (SUPER_ADMIN) |
| `GET`    | `/attendance/daily?work_date=…` | daily summary for a date |
| `GET`    | `/attendance/daily/employee/{id}` | daily summaries for one employee in a range |
| `POST`   | `/attendance/recompute` | recompute one date |
| `POST`   | `/attendance/recompute-range` | recompute a range |
| `POST`   | `/attendance/close-day` | end-of-day job |
| `POST`   | `/attendance/reopen-day` | clear `is_day_closed` |

### Snapshots — [snapshots.py](backend/app/api/v1/snapshots.py)
| Method | Path | Purpose |
|---|---|---|
| `GET` | `/snapshots` | list snapshots (filterable) |
| `GET` | `/snapshots/{event_id}.jpg` | fetch the JPEG for an event |

### Reports — [reports.py](backend/app/api/v1/reports.py)
All return Excel `.xlsx` downloads.

| Method | Path |
|---|---|
| `GET` | `/reports/daily.xlsx?work_date=YYYY-MM-DD` |
| `GET` | `/reports/monthly.xlsx?year=YYYY&month=M` |
| `GET` | `/reports/date-range.xlsx?start_date=…&end_date=…` |
| `GET` | `/reports/employee/{id}.xlsx?start_date=…&end_date=…` |

### Settings — [settings.py](backend/app/api/v1/settings.py)
| Method | Path |
|---|---|
| `GET`   | `/settings` |
| `PATCH` | `/settings` |

### Unknowns — [unknowns.py](backend/app/api/v1/unknowns.py)
| Method | Path | Purpose |
|---|---|---|
| `GET`    | `/unknowns/clusters` | list pending clusters |
| `POST`   | `/unknowns/clusters/{id}/promote` | convert cluster to a new employee |
| `POST`   | `/unknowns/clusters/{id}/ignore` | discard |
| `POST`   | `/unknowns/clusters/{id}/merge` | merge into another cluster |
| `POST`   | `/unknowns/recluster` | re-run clustering |

### Admin / Dashboard — [admin.py](backend/app/api/v1/admin.py)
| Method | Path | Purpose |
|---|---|---|
| `GET` | `/admin/stats` | high-level counts |
| `GET` | `/admin/dashboard` | full dashboard snapshot |
| `GET` | `/admin/dashboard/timeline` | recent events |
| `GET` | `/admin/dashboard/events-by-hour` | for the chart |
| `GET` | `/admin/presence` | current location of every employee |
| `GET` | `/admin/live-status` | per-camera worker health |

---

## 10. Setup & Installation

### 10.1 Prerequisites

- Python **3.11**
- PostgreSQL **14+**
- Node.js **18+** and npm
- A Windows or Linux box (tested on Windows 10/11)
- 4 IP cameras with RTSP URLs

### 10.2 Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# edit .env — DATABASE_URL, JWT_SECRET_KEY, BOOTSTRAP_ADMIN_*, TIMEZONE, CORS_ALLOW_ORIGINS
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

On first boot a super-admin is seeded from `BOOTSTRAP_ADMIN_USERNAME` / `BOOTSTRAP_ADMIN_PASSWORD`. **Log in and change the password immediately.**

### 10.3 Frontend

```powershell
cd frontend
npm install
copy .env.local.example .env.local
# edit .env.local if backend isn't on http://localhost:8000
npm run dev
# open http://localhost:3000
```

### 10.4 First-time configuration flow

1. Log in with the bootstrapped super-admin.
2. **Settings** → review thresholds, office hours, timezone.
3. **Cameras** → add 4 cameras (2 ENTRY + 2 EXIT) with their RTSP URLs.
   - Use the **Probe** button before saving to confirm the URL works.
4. **Employees** → create employees.
5. **Training** → upload 5–20 face photos per employee (or use **Capture** from a live feed).
6. Done — workers are now recognizing faces and writing events.

---

## 11. Configuration Reference (`.env`)

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://…` | required |
| `APP_NAME` | `AI CCTV Attendance` | shown in logs and API title |
| `APP_HOST` / `APP_PORT` | `0.0.0.0` / `8000` | |
| `APP_DEBUG` | `false` | enables FastAPI debug |
| `JWT_SECRET_KEY` | `change-me-…` | **must change in production** |
| `JWT_ALGORITHM` | `HS256` | |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | 24 hours |
| `BOOTSTRAP_ADMIN_USERNAME` / `BOOTSTRAP_ADMIN_PASSWORD` | `admin` / `ChangeMe@123` | seeded only on first boot |
| `FACE_MODEL_NAME` | `buffalo_l` | InsightFace pack |
| `FACE_PROVIDER` | `CPUExecutionProvider` | switch to GPU provider if available |
| `FACE_DET_SIZE` | `640` | detection input size |
| `FACE_MATCH_THRESHOLD` | `0.45` | runtime-tunable from UI |
| `FACE_MIN_QUALITY` | `0.50` | reject blurry training images |
| `FACE_TRAIN_MIN_IMAGES` / `_MAX_IMAGES` | `5` / `20` | per-employee upload bounds |
| `CAMERA_FPS` | `1` | runtime-tunable |
| `CAMERA_COOLDOWN_SECONDS` | `5` | runtime-tunable |
| `CAMERA_HEALTH_INTERVAL_SECONDS` | `10` | health monitor cadence |
| `CAMERA_HEARTBEAT_TIMEOUT_SECONDS` | `30` | restart worker if stale |
| `RTSP_CONNECT_TIMEOUT_MS` / `_READ_TIMEOUT_MS` | `5000` / `5000` | |
| `RTSP_RECONNECT_MAX_SECONDS` | `30` | back-off cap |
| `STORAGE_ROOT` / `TRAINING_DIR` / `SNAPSHOT_DIR` | `./storage…` | filesystem paths |
| `TIMEZONE` | `Asia/Kolkata` | used for daily date boundaries |
| `CORS_ALLOW_ORIGINS` | `http://localhost:3000,…` | comma-separated |
| `LOG_LEVEL` / `LOG_DIR` / `LOG_MAX_BYTES` / `LOG_BACKUP_COUNT` | `INFO` / `./logs` / 100 MB / 5 | rotating file logger |

---

## 12. Roles & Permissions

| Role | Read | Create / Edit | Delete | Special |
|---|---|---|---|---|
| `SUPER_ADMIN` | everything | everything | yes (events, employees, cameras) | reopen day, run reclustering, full settings |
| `ADMIN` | everything | most things | (no destructive deletes) | runs close-day, manual events |
| `HR` | scoped to one company | (read-only by default) | no | sees only their company's employees & data |
| `VIEWER` | dashboard / training images / lists | no | no | read-only |

Role gates live in [backend/app/api/deps.py](backend/app/api/deps.py) (`require_roles(...)`).

---

## 13. Day-to-Day Operations

### Add a new employee
1. **Employees → Add** — fill name (employee code is auto-generated as `EMP-NNNNNN`).
2. **Training → select employee → Upload** — drop 5–20 clear face photos.
   The system runs each photo through quality + face-detection gates and rejects bad ones with a reason.
3. The new embeddings are added to the in-memory cache automatically — recognition starts immediately.

### Correct a missed punch
1. **Attendance → Events** — find the day.
2. Click **Add manual event** — pick employee, type (IN / BREAK_OUT / BREAK_IN / OUT), time, optional note.
3. The daily rollup recomputes automatically. The event is flagged `is_manual=true` with `corrected_by=<your admin id>`.

### Close a day
1. End of day, **Attendance → Close Day** with the work date.
2. For every employee whose last event today is `BREAK_OUT`, the system rewrites that event to `OUT` (with an audit note `[auto-closed: trailing BREAK_OUT → OUT]`).
3. The day is marked `is_day_closed=true`. Auto-events for that date are still possible only by re-opening.

### Download a report
1. **Reports** → pick **Daily / Monthly / Date range / Per-employee**.
2. The browser receives an `.xlsx` file with summaries, totals, late minutes, early-exit minutes, etc.

### Promote an unknown face
*(only when `unknown_capture_enabled=true`)*
1. **Unknowns** — clusters of similar unrecognized faces appear here.
2. Pick a cluster → **Promote** → fill the new employee's details.
3. The cluster's snapshots become the seed training images and embeddings — recognition starts on the next frame.

---

## 14. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Camera shows "No frame" / "Stale" | RTSP URL wrong or camera offline | Use **Cameras → Probe**; check network; click **Restart** |
| All workers crash at startup | InsightFace model failed to download | Check internet on first boot; `storage/models/` should fill up. After that it's offline. |
| 401 on every request | Token expired or wrong | Log out + log in. Tokens last `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (default 24 h) |
| Recognized as wrong person | Threshold too low, or training photos low quality | Raise `face_match_threshold` in **Settings**; re-upload clearer photos |
| Recognized intermittently | `recognize_min_face_size_px` too high, camera too far | Lower the min size, or move the camera |
| Duplicate events for same person | Cooldown disabled or too low | Raise `cooldown_seconds` in **Settings** |
| Late minutes not computing | `work_start_time` not set | Set office hours in **Settings** |
| "Worker stale; restarting" in logs | Camera lost connection > heartbeat timeout | Self-heals automatically; check camera if it persists |
| Backend slow under load | Detection too aggressive | Lower `camera_fps` or `FACE_DET_SIZE` |

### Where to look

- **Backend logs**: `backend/logs/app.log` (rotating, 100 MB × 5)
- **Per-camera health**: `GET /api/v1/admin/live-status`
- **Process-wide health**: `GET /health`

---

## Appendix A — One-line "what is this folder"

| Path | What |
|---|---|
| [backend/app/main.py](backend/app/main.py) | FastAPI entrypoint, lifespan, CORS, error handler |
| [backend/app/config.py](backend/app/config.py) | Loads `.env` via pydantic-settings |
| [backend/app/api/v1/](backend/app/api/v1/) | All HTTP endpoints |
| [backend/app/services/](backend/app/services/) | All business logic |
| [backend/app/repositories/](backend/app/repositories/) | All database queries |
| [backend/app/models/](backend/app/models/) | SQLAlchemy ORM models |
| [backend/app/workers/](backend/app/workers/) | Camera threads + RTSP |
| [backend/app/utils/](backend/app/utils/) | Time, image, Excel, face-quality helpers |
| [backend/migrations/](backend/migrations/) | Alembic schema versions |
| [frontend/app/](frontend/app/) | Next.js pages |
| [frontend/components/](frontend/components/) | React components (UI + features) |
| [frontend/lib/](frontend/lib/) | Axios client, query hooks, types, auth |
| [frontend/middleware.ts](frontend/middleware.ts) | Route guard |

---

*This document covers the architecture and all major functionality. For deeper code-level reading, the backend [README](backend/README.md) and frontend [README](frontend/README.md) have additional notes.*

**Deploying to production?** See [DEPLOYMENT.md](DEPLOYMENT.md) — a complete step-by-step guide covering Docker, nginx + HTTPS, backups, and auto-restart.
