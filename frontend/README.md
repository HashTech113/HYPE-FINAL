# Frontend (Attendance Dashboard UI)

This frontend is a Vite + React app.

- Default local port: `8080`
- API base URL comes from `VITE_API_BASE_URL` (default in `.env.example` is `http://localhost:8000`)

## Setup

### Windows (PowerShell)

```powershell
cd frontend
npm install
copy .env.example .env
```

### Ubuntu / Linux

```bash
cd frontend
npm install
cp .env.example .env
```

## Run

Windows or Ubuntu:

```bash
cd frontend
npm run dev
```

Open:

- `http://localhost:8080`

## Build

```bash
cd frontend
npm run build
npm run preview
```

## Common issue

If `localhost:8080` shows "refused to connect", the dev server is not running.
Start `npm run dev` in `frontend/`, then refresh the browser.
