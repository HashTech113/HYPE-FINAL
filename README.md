# Attendance Dashboard (Main Project)

This is the main project in this repo:

- `backend/` = FastAPI API + capture workers + SQLite/PostgreSQL storage
- `frontend/` = Vite + React dashboard (runs on port `8080`)

If you copied this folder to another PC (Windows/Ubuntu), follow the steps below.

## 0) Single Command Start (Backend + Frontend Together)

After one-time setup, from project root run:

```bash
npm run dev
```

This **single command starts both services at the same time**:

- Backend API: `http://localhost:8000`
- Frontend UI: `http://localhost:8080`

Windows note:

- Run `npm run dev` from **Git Bash** or **WSL** (it calls `bash backend/start.sh` internally).

## 1) Requirements

- Python `3.11+` (3.12 works)
- Node.js `22+`
- npm

## 2) One-time setup (Windows)

Run these in **PowerShell** from project root:

```powershell
# backend deps
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
deactivate
cd ..

# frontend deps
cd frontend
npm install
cd ..

# root helper deps (required for the single-command run)
npm install
```

## 3) One-time setup (Ubuntu)

Run these in terminal from project root:

```bash
# backend deps
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# frontend deps
cd frontend
npm install
cd ..

# root helper deps (required for the single-command run)
npm install
```

## 4) Run locally (recommended: both on one command)

### Windows

Use **Git Bash** or **WSL** (because the backend launcher is `bash backend/start.sh`):

```bash
npm run dev
```

### Ubuntu

```bash
npm run dev
```

Again, this one command starts both:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:8080`

## 5) Alternative: run backend/frontend separately

If you do not want the combined command:

### Backend

Windows PowerShell:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Ubuntu:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

Windows or Ubuntu:

```bash
cd frontend
npm run dev
```

## 6) Health checks

- Backend health: `http://localhost:8000/api/health`
- Frontend: `http://localhost:8080`

If frontend opens but shows API errors, confirm backend is running first.

## 7) Data when moving to another PC

- Main local DB file is usually `backend/database.db` (SQLite fallback).
- If you want old employees/snapshots, copy this DB file too.
- No migration is needed when staying on SQLite + same codebase.
- Migration is needed only when moving to PostgreSQL (see `backend/scripts/migrate_sqlite_to_postgres.py`).

## 8) Detailed docs

- Backend docs: [backend/README.md](backend/README.md)
- Frontend docs: [frontend/README.md](frontend/README.md)
