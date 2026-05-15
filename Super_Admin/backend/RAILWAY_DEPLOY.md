# Railway Deploy — AI Attendance Backend (API-Only Mode)

The `backend/` directory contains everything Railway needs to deploy
the API-only image: `Dockerfile`, `railway.json`, and a code branch in
`app/main.py` that skips camera workers / face recognition when
`DISABLE_CAMERA_WORKERS=true`.

This deploy is for the **read API** (admin login, attendance queries,
the `/external/*` endpoints used by HR dashboards). It does NOT do any
face recognition — that keeps running on the on-prem Windows machine
where the cameras live.

---

## 1 — Push this repo to GitHub

If it isn't already on GitHub, push it. Railway deploys from a
connected Git repo.

```bash
git add backend/Dockerfile backend/railway.json backend/.dockerignore backend/app/main.py
git commit -m "Add Railway deploy config and API-only mode"
git push origin main
```

## 2 — Create the Railway project

1. Go to https://railway.app/new
2. Click **"Deploy from GitHub repo"** → pick this repository.
3. When the project loads, click the empty service that was created.
4. Click **Settings → Service Settings**:
   - **Root Directory**: `backend`
     *(the path that contains the `Dockerfile`).*
   - **Builder**: should auto-detect "Dockerfile". If not, set it.

## 3 — Add a Postgres database

1. In the same Railway project, click **+ New → Database → PostgreSQL**.
2. Wait ~30 s for it to provision.
3. Click the new Postgres service → **Connect** tab → copy the
   `DATABASE_URL` (the one starting with `postgresql://`).

## 4 — Set environment variables on the API service

Click your API service → **Variables** → add:

| Name | Value |
|---|---|
| `DATABASE_URL` | *(paste from step 3, but change scheme to `postgresql+psycopg2://`)* |
| `DISABLE_CAMERA_WORKERS` | `true` |
| `JWT_SECRET_KEY` | *(generate fresh: `python -c "import secrets; print(secrets.token_hex(32))"`)* |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` |
| `BOOTSTRAP_ADMIN_USERNAME` | `admin` |
| `BOOTSTRAP_ADMIN_PASSWORD` | *(strong password — used once on first boot to create the admin)* |
| `CORS_ALLOW_ORIGINS` | *(your HR dashboard origin — e.g. `https://hr.example.com`)* |
| `LOG_LEVEL` | `INFO` |
| `TIMEZONE` | `Asia/Kolkata` |

> **Important**: do NOT set `FACE_PROVIDER` to `DmlExecutionProvider` in
> production — that's Windows-only. The default `CPUExecutionProvider`
> is correct here, but it never runs anyway because
> `DISABLE_CAMERA_WORKERS=true` short-circuits face init.

## 5 — Deploy

Railway will rebuild on every push to `main`. The first build takes
~5–8 min (downloads opencv + onnxruntime + insightface deps). Watch
the **Deployments** tab for "Active" status.

The startup command runs `alembic upgrade head` first — if the DB is
empty, every migration applies; if it's already at head, this is a
no-op. Either way the schema is in sync with the code.

## 6 — Generate a public domain

1. API service → **Settings → Networking → Generate Domain**.
2. You'll get a URL like `https://ai-attendance-backend.up.railway.app`.
3. **Add `/api/v1` for the actual API base URL**:
   `https://ai-attendance-backend.up.railway.app/api/v1`

## 7 — Smoke test

```bash
# Health check (no auth)
curl https://ai-attendance-backend.up.railway.app/health
# → {"status":"ok"}

# Log in as the bootstrap admin
curl -X POST https://ai-attendance-backend.up.railway.app/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"<the password from step 4>"}'
# → {"access_token":"…"}
```

## 8 — Mint a production API key on Railway

```bash
TOKEN="<paste the access_token from step 7>"

curl -X POST https://ai-attendance-backend.up.railway.app/api/v1/api-keys \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name":"Production - HR Dashboard"}'
```

The response includes `plaintext` once — save it. That's the key the
HR dashboard will use:

```
X-API-Key: aiatt_live_…
```

## 9 — Verify the external API

```bash
curl https://ai-attendance-backend.up.railway.app/api/v1/external/health \
     -H "X-API-Key: aiatt_live_…"
# → {"ok":true, ...}
```

---

## Connecting the on-prem backend to the same DB (optional)

If you want the cameras at the office to keep recognizing AND the
events to show up via the Railway API, point the on-prem backend's
`DATABASE_URL` (in `backend/.env`) at the **public Postgres URL** that
Railway exposes:

1. Postgres service → **Connect** tab → copy the **Public Network**
   URL (NOT the internal one — the on-prem machine isn't on Railway's
   internal network).
2. Set `DATABASE_URL=postgresql+psycopg2://…public-railway-url…` in
   `backend/.env` on the Windows machine.
3. Restart the on-prem backend.
4. Run `alembic upgrade head` on the on-prem machine once to create
   tables — but if Railway already booted, the schema is there
   already and this no-ops.

> Watch out: every recognition write now does a round-trip to Railway
> (~50–200 ms over the public internet). The event queue handles this
> off the detection hot path so recognition stays smooth, but
> sustained throughput will be lower than a local DB.

---

## What's deliberately broken on Railway

- `/api/v1/cameras/*/preview.jpg` and `/preview.mjpg` → 500 (no
  `camera_manager`)
- Live training-from-camera → same
- `/api/v1/realtime/...` SSE → connects but emits no events (no
  recognition pipeline)

Everything else — admin auth, employee CRUD, attendance event queries,
the entire `/external/*` API — works exactly as on-prem.
