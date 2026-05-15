# Production Deployment Guide — From Zero to Live

This guide takes you from a fresh server to a fully running, internet-accessible AI CCTV Attendance System using Docker. Read it once top to bottom, then follow it step by step.

> **Important up front.** This system needs to talk to RTSP cameras on your office LAN. That means the **server running the backend must be on the same local network as the cameras** (or have a VPN tunnel to them). You cannot run the backend on a generic cloud VM that has no path to your cameras. The dashboard, however, can be exposed publicly with HTTPS so admins can use it from anywhere.

---

## Table of Contents

1. [Production Architecture Overview](#1-production-architecture-overview)
2. [What You Need Before You Start](#2-what-you-need-before-you-start)
3. [Pre-flight Checklist](#3-pre-flight-checklist)
4. [Step 1 — Pick & Prepare the Server](#step-1--pick--prepare-the-server)
5. [Step 2 — Install Docker & Compose](#step-2--install-docker--compose)
6. [Step 3 — Project Layout for Production](#step-3--project-layout-for-production)
7. [Step 4 — Create the Backend Dockerfile](#step-4--create-the-backend-dockerfile)
8. [Step 5 — Create the Frontend Dockerfile](#step-5--create-the-frontend-dockerfile)
9. [Step 6 — `.dockerignore` Files](#step-6--dockerignore-files)
10. [Step 7 — Production `.env` File](#step-7--production-env-file)
11. [Step 8 — `docker-compose.yml`](#step-8--docker-composeyml)
12. [Step 9 — Nginx Reverse Proxy + HTTPS](#step-9--nginx-reverse-proxy--https)
13. [Step 10 — First-Time Launch](#step-10--first-time-launch)
14. [Step 11 — Domain & DNS](#step-11--domain--dns)
15. [Step 12 — Backups](#step-12--backups)
16. [Step 13 — Auto-Start on Reboot](#step-13--auto-start-on-reboot)
17. [Step 14 — Logs & Monitoring](#step-14--logs--monitoring)
18. [Step 15 — Updates & Redeploys](#step-15--updates--redeploys)
19. [Hardening Checklist](#hardening-checklist)
20. [Common Gotchas](#common-gotchas)

---

## 1. Production Architecture Overview

```
                                 INTERNET
                                    │
                                    │  HTTPS  (port 443)
                                    ▼
   ┌────────────────────────────────────────────────────────────┐
   │                ON-PREM SERVER (Linux + Docker)             │
   │                                                            │
   │   ┌────────────────┐                                       │
   │   │   nginx        │  TLS terminate, route /api → backend, │
   │   │  (host:443)    │  everything else → frontend           │
   │   └───┬───────┬────┘                                       │
   │       │       │                                            │
   │       ▼       ▼                                            │
   │  ┌────────┐ ┌──────────┐    ┌──────────────────────────┐   │
   │  │frontend│ │ backend  │───▶│       postgres           │   │
   │  │ :3000  │ │  :8000   │    │  (named volume: pgdata)  │   │
   │  └────────┘ └────┬─────┘    └──────────────────────────┘   │
   │                  │                                         │
   │                  │  named volumes                          │
   │                  ▼                                         │
   │       ┌─────────────────────────────────────┐              │
   │       │ storage  (snapshots,                │              │
   │       │           training_images,          │              │
   │       │           InsightFace model cache)  │              │
   │       │ logs                                │              │
   │       └─────────────────────────────────────┘              │
   │                                                            │
   │              ▲                                             │
   │              │  RTSP   (LAN only — never expose)           │
   │              │                                             │
   └──────────────┼─────────────────────────────────────────────┘
                  │
       ┌──────────┴──────────┐
       │                     │
   IP cam 1 / 2          IP cam 3 / 4   (ENTRY + EXIT)
```

**Key idea**: everything runs in containers on **one server**. Outsiders see only nginx on port 443. Cameras stay on the LAN. Data lives in named Docker volumes (so containers can be rebuilt without losing anything).

---

## 2. What You Need Before You Start

| Need | Why |
|---|---|
| A Linux server (Ubuntu 22.04 LTS recommended) on the office LAN | runs Docker; reaches cameras via RTSP |
| At least 4 GB RAM, 2 CPU cores, 50 GB disk | InsightFace + 4 camera workers + Postgres + snapshots |
| Cameras' RTSP URLs (e.g. `rtsp://user:pass@192.168.1.50:554/stream1`) | for the **Cameras** page |
| A domain name (e.g. `attendance.yourcompany.com`) | for HTTPS |
| Ability to point that domain at the server's public IP | DNS A record |
| Open ports `80` and `443` on the server | for nginx + Let's Encrypt |
| Internet access on the server (at least the first time) | to download Docker images and the InsightFace model |

> **GPU is optional.** The default config runs face inference on CPU (`FACE_PROVIDER=CPUExecutionProvider`) and works fine for 4 cameras. If you have an NVIDIA GPU, you can switch later — it doesn't change the deployment shape.

---

## 3. Pre-flight Checklist

Tick these off before touching the server:

- [ ] Domain name purchased
- [ ] DNS A record points to the server (`dig +short attendance.yourcompany.com` returns the right IP)
- [ ] All 4 cameras have static LAN IPs (or DHCP reservations)
- [ ] You can ping each camera from the server: `ping 192.168.1.50`
- [ ] You can open each RTSP URL with VLC from the server (sanity check)
- [ ] You have a long random `JWT_SECRET_KEY` ready (`openssl rand -hex 32`)
- [ ] You've decided on the bootstrap admin username & password
- [ ] You've set the timezone you want (e.g. `Asia/Kolkata`, `America/New_York`)

---

## Step 1 — Pick & Prepare the Server

### 1.1 Update the OS

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw
```

### 1.2 Set the timezone

```bash
sudo timedatectl set-timezone Asia/Kolkata   # change to yours
```

This matters because the system uses the host clock to decide what "today" is for daily attendance.

### 1.3 Open the firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

> Don't open port 8000 or 3000 to the internet — nginx will reach them inside Docker.

### 1.4 Create a non-root user (skip if already done)

```bash
sudo adduser deploy
sudo usermod -aG sudo deploy
sudo su - deploy
```

Do everything below as the `deploy` user.

---

## Step 2 — Install Docker & Compose

```bash
# Docker official install script
curl -fsSL https://get.docker.com | sudo sh

# Allow your user to run docker without sudo
sudo usermod -aG docker $USER

# Log out + log back in (or run `newgrp docker`)
exit
# … reconnect SSH …

# Verify
docker --version
docker compose version
```

You should see Docker 24+ and Compose v2+.

---

## Step 3 — Project Layout for Production

Clone the repo to the server:

```bash
cd /opt
sudo mkdir ai-attendance && sudo chown $USER:$USER ai-attendance
cd ai-attendance
git clone <your-git-url> .
```

You'll add a few new files at the project root. The final layout looks like:

```
/opt/ai-attendance/
├── backend/                  (existing)
├── frontend/                 (existing)
├── DOCUMENTATION.md          (existing)
├── DEPLOYMENT.md             (this file)
│
├── backend/Dockerfile        ← create in Step 4
├── backend/.dockerignore     ← create in Step 6
├── frontend/Dockerfile       ← create in Step 5
├── frontend/.dockerignore    ← create in Step 6
├── .env                      ← create in Step 7  (NEVER commit this)
├── docker-compose.yml        ← create in Step 8
├── nginx/
│   ├── nginx.conf            ← create in Step 9
│   └── certs/                ← Let's Encrypt drops certs here
└── backups/                  ← created by the backup cron
```

---

## Step 4 — Create the Backend Dockerfile

Create `backend/Dockerfile`:

```dockerfile
# ---- builder: install Python deps in a virtualenv ----
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Build tools needed by some wheels (insightface, opencv, psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt


# ---- runtime: small image with only what we need to run ----
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# OpenCV + InsightFace runtime libs
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libpq5 \
        tzdata \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bring the pre-built virtualenv from the builder stage
COPY --from=builder /opt/venv /opt/venv

# App code
COPY . /app

# Storage and logs are mounted as volumes — make sure the dirs exist
RUN mkdir -p /app/storage/models \
             /app/storage/training_images \
             /app/storage/snapshots \
             /app/logs

EXPOSE 8000

# Healthcheck hits the lightweight /health route
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Run alembic migrations, then start the API.
# (We do this in compose's `command:` instead — keep the image simple.)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Why two stages?** The builder pulls in `gcc`, `build-essential` etc. (~600 MB of tooling) just to compile the Python wheels. The runtime image only carries the compiled venv plus a few small system libs — final image is ~1.5 GB instead of 2.5 GB.

---

## Step 5 — Create the Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
# ---- deps: install node modules ----
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# ---- build: produce the .next directory ----
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# IMPORTANT: NEXT_PUBLIC_* values are baked into the build.
# Pass NEXT_PUBLIC_API_URL as a build-arg so it ends up in the bundle.
ARG NEXT_PUBLIC_API_URL=/api/v1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

# ---- runtime: only what's needed to `next start` ----
FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

# Copy only what's needed
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.mjs ./next.config.mjs
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000
CMD ["npm", "run", "start"]
```

> The default `NEXT_PUBLIC_API_URL=/api/v1` means the frontend talks to the backend through nginx on the same domain — no CORS headaches, no separate API hostname needed.

---

## Step 6 — `.dockerignore` Files

These keep junk out of the build context (faster builds, smaller images).

`backend/.dockerignore`:

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
storage/
logs/
*.log
.env
.env.*
!.env.example
.git/
.idea/
.vscode/
```

`frontend/.dockerignore`:

```
node_modules/
.next/
out/
.env.local
.env.*.local
.git/
.idea/
.vscode/
npm-debug.log*
```

---

## Step 7 — Production `.env` File

At the project root, create `.env` (NOT `backend/.env` — Compose will inject it into the backend container):

```bash
# === Database ===
POSTGRES_DB=ai_attendance
POSTGRES_USER=ai_attendance
POSTGRES_PASSWORD=CHANGE-THIS-TO-A-LONG-RANDOM-STRING
DATABASE_URL=postgresql+psycopg2://ai_attendance:CHANGE-THIS-TO-A-LONG-RANDOM-STRING@postgres:5432/ai_attendance

# === API ===
APP_NAME=AI CCTV Attendance
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false

# === Security — REGENERATE THESE ===
JWT_SECRET_KEY=PASTE-OUTPUT-OF-openssl-rand-hex-32-HERE
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# === Bootstrap admin (used ONLY on first boot) ===
BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_PASSWORD=CHANGE-THIS-AT-FIRST-LOGIN

# === Face recognition ===
FACE_MODEL_NAME=buffalo_l
FACE_MODEL_ROOT=/app/storage/models
FACE_PROVIDER=CPUExecutionProvider
FACE_DET_SIZE=640
FACE_MATCH_THRESHOLD=0.45
FACE_MIN_QUALITY=0.50
FACE_TRAIN_MIN_IMAGES=5
FACE_TRAIN_MAX_IMAGES=20

# === Camera pipeline ===
CAMERA_FPS=1
CAMERA_COOLDOWN_SECONDS=5
CAMERA_HEALTH_INTERVAL_SECONDS=10
CAMERA_HEARTBEAT_TIMEOUT_SECONDS=30
RTSP_CONNECT_TIMEOUT_MS=5000
RTSP_READ_TIMEOUT_MS=5000
RTSP_RECONNECT_MAX_SECONDS=30

# === Storage (paths inside the backend container) ===
STORAGE_ROOT=/app/storage
TRAINING_DIR=/app/storage/training_images
SNAPSHOT_DIR=/app/storage/snapshots

# === Timezone ===
TIMEZONE=Asia/Kolkata

# === CORS — your real public domain ===
CORS_ALLOW_ORIGINS=https://attendance.yourcompany.com

# === Logging ===
LOG_LEVEL=INFO
LOG_DIR=/app/logs
LOG_MAX_BYTES=104857600
LOG_BACKUP_COUNT=5

# === Frontend build-arg (used at build time) ===
NEXT_PUBLIC_API_URL=/api/v1
```

**Lock this file down:**

```bash
chmod 600 .env
```

Generate a strong `JWT_SECRET_KEY`:

```bash
openssl rand -hex 32
```

Generate a strong `POSTGRES_PASSWORD` the same way and paste it into both `POSTGRES_PASSWORD` and the `DATABASE_URL`.

---

## Step 8 — `docker-compose.yml`

At the project root:

```yaml
services:

  postgres:
    image: postgres:16-alpine
    container_name: aa_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - aa_net

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: aa_backend
    restart: unless-stopped
    env_file: .env
    # Run migrations every time the container starts, then launch uvicorn.
    # `alembic upgrade head` is a no-op when the schema is already current.
    command: >
      sh -c "alembic upgrade head &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - storage:/app/storage
      - logs:/app/logs
    networks:
      - aa_net
    # Cameras live on the host LAN. The backend container reaches them
    # through the standard Docker bridge — no extra config needed for
    # most LANs. If your cameras are on a different VLAN, you may need
    # `network_mode: host` instead. See "Common Gotchas".

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
    container_name: aa_frontend
    restart: unless-stopped
    depends_on:
      - backend
    networks:
      - aa_net

  nginx:
    image: nginx:1.27-alpine
    container_name: aa_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/letsencrypt:ro
      - ./nginx/www:/var/www/certbot:ro
    depends_on:
      - frontend
      - backend
    networks:
      - aa_net

volumes:
  pgdata:
  storage:
  logs:

networks:
  aa_net:
    driver: bridge
```

**Why one worker?** The backend keeps the InsightFace model and embedding cache as **process-wide singletons** — they take ~1.5 GB of RAM. Multiple uvicorn workers would each load their own copy AND each spawn their own camera threads (you'd get duplicate events). One worker is correct for this app.

---

## Step 9 — Nginx Reverse Proxy + HTTPS

### 9.1 Initial nginx config (HTTP only — for cert issuance)

Create `nginx/nginx.conf`:

```nginx
worker_processes auto;
events { worker_connections 1024; }

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;

    # MJPEG streams need a larger client buffer + no buffering
    client_max_body_size 25m;
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;

    server {
        listen 80;
        server_name attendance.yourcompany.com;

        # Used by certbot to prove domain ownership
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    server {
        listen 443 ssl;
        http2 on;
        server_name attendance.yourcompany.com;

        ssl_certificate     /etc/letsencrypt/live/attendance.yourcompany.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/attendance.yourcompany.com/privkey.pem;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Backend API
        location /api/ {
            proxy_pass         http://backend:8000;
            proxy_http_version 1.1;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;

            # MJPEG live stream needs un-buffered, long-lived connections
            proxy_buffering off;
            proxy_cache off;
        }

        # Health endpoint (handy for uptime checks)
        location /health {
            proxy_pass http://backend:8000/health;
        }

        # Everything else → Next.js
        location / {
            proxy_pass         http://frontend:3000;
            proxy_http_version 1.1;
            proxy_set_header   Upgrade $http_upgrade;
            proxy_set_header   Connection "upgrade";
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;
        }
    }
}
```

> Replace `attendance.yourcompany.com` with your real domain (3 places).

### 9.2 Get a real SSL certificate (Let's Encrypt, one-time)

```bash
# Make the directories nginx expects
mkdir -p nginx/certs nginx/www

# Run certbot in a one-shot container; it talks to Let's Encrypt and
# writes the cert into nginx/certs.
docker run --rm \
  -p 80:80 \
  -v $(pwd)/nginx/certs:/etc/letsencrypt \
  -v $(pwd)/nginx/www:/var/www/certbot \
  certbot/certbot certonly --standalone \
  -d attendance.yourcompany.com \
  --email you@yourcompany.com \
  --agree-tos --no-eff-email
```

You should see `Successfully received certificate.` Files land under `nginx/certs/live/attendance.yourcompany.com/`.

### 9.3 Auto-renewal

Add a daily cron job to renew the cert and reload nginx:

```bash
crontab -e
```

Add this line:

```cron
0 3 * * * cd /opt/ai-attendance && docker run --rm -v $(pwd)/nginx/certs:/etc/letsencrypt -v $(pwd)/nginx/www:/var/www/certbot certbot/certbot renew --quiet && docker compose exec -T nginx nginx -s reload
```

---

## Step 10 — First-Time Launch

From `/opt/ai-attendance`:

```bash
# 1. Build images
docker compose build

# 2. Start everything in the background
docker compose up -d

# 3. Watch the backend logs — alembic should run, model should load,
#    bootstrap admin should be created.
docker compose logs -f backend
```

You're looking for:

```
INFO ... Starting AI CCTV Attendance
INFO ... Bootstrapped admin: admin
INFO ... FaceService loaded model=buffalo_l
INFO ... EmbeddingCache loaded N embeddings
INFO ... [cam-...] worker starting (type=ENTRY)
INFO ... Application startup complete.
```

Open `https://attendance.yourcompany.com` in a browser and log in with the bootstrap admin credentials.

**Immediately after first login:**

1. Click your username → **Change password** → set a new strong password.
2. **Cameras** → add your 4 RTSP cameras (use **Probe** before saving each).
3. **Employees** → create employees.
4. **Training** → upload 5–20 face photos per employee.

That's it — the system is now running.

---

## Step 11 — Domain & DNS

If you didn't do this earlier:

1. In your DNS provider (Cloudflare, Route 53, GoDaddy, etc.) create an **A record**:
   - Name: `attendance`
   - Type: `A`
   - Value: `<your server's public IP>`
   - TTL: `300`
2. Wait a few minutes, then verify:
   ```bash
   dig +short attendance.yourcompany.com
   ```
3. Re-run Step 9.2 if you got the cert before DNS was correct.

---

## Step 12 — Backups

Two things need backing up:

| What | How big | How critical |
|---|---|---|
| Postgres database | small (MB) | **critical** — losing it loses all attendance |
| `storage/` volume (snapshots, training images, model cache) | grows over time (GB) | important — losing snapshots loses face evidence; training images can be re-uploaded |

### 12.1 One-shot backup script

Create `/opt/ai-attendance/scripts/backup.sh`:

```bash
#!/bin/bash
set -euo pipefail
cd /opt/ai-attendance

DATE=$(date +%Y-%m-%d_%H%M)
DIR="./backups/$DATE"
mkdir -p "$DIR"

# 1. Postgres dump
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  | gzip > "$DIR/db.sql.gz"

# 2. Storage volume
docker run --rm -v ai-attendance_storage:/source -v "$(pwd)/$DIR":/backup \
  alpine tar czf /backup/storage.tar.gz -C /source .

# 3. Keep only last 14 backups
ls -1dt ./backups/*/ | tail -n +15 | xargs -r rm -rf

echo "Backup written to $DIR"
```

Make it executable, source the env so `$POSTGRES_USER` etc. are set, run it daily via cron:

```bash
chmod +x scripts/backup.sh
crontab -e
```

Add:

```cron
30 2 * * * cd /opt/ai-attendance && set -a && source .env && set +a && ./scripts/backup.sh >> backups/backup.log 2>&1
```

### 12.2 Off-site copies

Local backups die with the server. Copy `backups/` to S3, an external NAS, or `rsync` it to another box:

```cron
0 4 * * * rsync -az /opt/ai-attendance/backups/ backup-host:/safe/place/ai-attendance/
```

### 12.3 Restoring (in a hurry)

```bash
# Stop the app
docker compose down

# Restore DB
docker compose up -d postgres
gunzip < backups/2026-04-29_0230/db.sql.gz | \
  docker compose exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

# Restore storage
docker run --rm -v ai-attendance_storage:/target -v "$(pwd)/backups/2026-04-29_0230":/backup \
  alpine sh -c "cd /target && tar xzf /backup/storage.tar.gz"

# Bring everything back up
docker compose up -d
```

---

## Step 13 — Auto-Start on Reboot

Docker's `restart: unless-stopped` already restarts containers if they crash, but if the **server reboots** you need Docker itself to come up. It does by default on Ubuntu, but verify:

```bash
sudo systemctl enable docker
sudo systemctl status docker
```

For belt-and-braces, create a systemd unit that brings the stack up after Docker is ready.

`/etc/systemd/system/ai-attendance.service`:

```ini
[Unit]
Description=AI CCTV Attendance Stack
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/ai-attendance
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-attendance
sudo systemctl start ai-attendance
```

Now `sudo reboot` and watch it come back on its own.

---

## Step 14 — Logs & Monitoring

### 14.1 Tail logs

```bash
docker compose logs -f backend
docker compose logs -f --tail=200 nginx
docker compose logs -f          # everything together
```

### 14.2 Where files actually live

| Source | Where |
|---|---|
| Backend rotating log | inside the `logs` named volume → `/var/lib/docker/volumes/ai-attendance_logs/_data/app.log` |
| Postgres data | `/var/lib/docker/volumes/ai-attendance_pgdata/_data/` |
| Snapshots / training images / models | `/var/lib/docker/volumes/ai-attendance_storage/_data/` |

### 14.3 Camera & worker health

In the dashboard:
- **Live status** indicator on each camera (green = streaming, red = stale)
- **Cameras** page shows last frame age, frames processed, last error

From the command line:
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  https://attendance.yourcompany.com/api/v1/admin/live-status | jq
```

### 14.4 Optional uptime probe

Point any external uptime service (UptimeRobot, BetterStack, healthchecks.io) at:
```
https://attendance.yourcompany.com/health
```
That route is unauthenticated and returns `{"status":"ok"}` when the backend is up.

---

## Step 15 — Updates & Redeploys

When the code changes (you push, then pull on the server):

```bash
cd /opt/ai-attendance
git pull

# Rebuild only what changed
docker compose build backend frontend

# Roll containers — Compose stops + recreates only the changed services
docker compose up -d

# Watch the rollout
docker compose logs -f --tail=100
```

Database migrations run automatically on backend startup (`alembic upgrade head` in `command:`).

> If a migration is **destructive** (drops a column, etc.), take a backup first:
> ```bash
> ./scripts/backup.sh
> ```

### Rolling back

```bash
git checkout <previous-commit>
docker compose build backend frontend
docker compose up -d
```

If a migration needs rolling back too, `alembic downgrade -1` against the database — but this is rare.

---

## Hardening Checklist

Run through this list before declaring "production":

- [ ] `JWT_SECRET_KEY` is 32+ random bytes (not the default placeholder)
- [ ] `POSTGRES_PASSWORD` is a long random string
- [ ] `BOOTSTRAP_ADMIN_PASSWORD` was changed at first login
- [ ] `.env` is `chmod 600` and **not** in git
- [ ] Firewall exposes only `80` and `443` (and SSH from trusted IPs)
- [ ] `CORS_ALLOW_ORIGINS` is your real domain only — not `*`, not `http://localhost:3000`
- [ ] `APP_DEBUG=false`
- [ ] HTTPS works (`https://...` shows a valid lock icon)
- [ ] Cert auto-renewal cron is installed
- [ ] Daily backup cron is installed and you've **tested a restore** at least once
- [ ] `ai-attendance.service` survives a reboot
- [ ] At least 2 admin accounts exist (so losing one password isn't a lockout)
- [ ] Cameras are NOT exposed to the internet (RTSP is plaintext)
- [ ] Server OS auto-updates security patches (`unattended-upgrades` on Ubuntu)

---

## Common Gotchas

### "Cameras can't be reached from the container"

Docker's bridge network usually has the same LAN access the host has, but on **multi-VLAN** networks or with strict firewalls, the container may not see a camera the host can ping.

Fix: switch the backend to the host network. In `docker-compose.yml`, replace the backend's `networks:` block with:

```yaml
    network_mode: host
```

Then change `DATABASE_URL` to point to `localhost:5432` and remove the backend from the `aa_net` network. The downside is that nginx now has to reach the backend at `host.docker.internal:8000` (or you put nginx on host-network too).

### "InsightFace download stalls / fails on first boot"

The model (~250 MB) is downloaded once, then cached in the `storage` volume. If your firewall blocks the CDN, the first boot will hang forever.

Fix: download the model on a machine with internet, copy it to the volume manually:

```bash
# On a machine with internet:
mkdir -p models && cd models
# (insightface fetches from huggingface; the buffalo_l zip is ~280 MB)
# … copy the buffalo_l folder to the server …

# On the server:
docker cp ./buffalo_l aa_backend:/app/storage/models/
docker compose restart backend
```

### "Frontend says 'Network Error' even though backend is up"

Two usual causes:

1. `NEXT_PUBLIC_API_URL` was baked into the build with the wrong value. Rebuild the frontend with the right build-arg:
   ```bash
   docker compose build --no-cache frontend
   docker compose up -d frontend
   ```
2. `CORS_ALLOW_ORIGINS` doesn't include the domain the browser sees. Update `.env`, then `docker compose up -d backend`.

### "Time is wrong — daily rollups are off by a day"

The system uses `TIMEZONE` from `.env` for "what is today". If you change it, the next event after the change uses the new TZ. Existing rows are not migrated.

Fix: set the right `TIMEZONE` from day one. If you have to change it later, run:
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  "https://attendance.yourcompany.com/api/v1/attendance/recompute-range?start_date=2026-01-01&end_date=2026-12-31"
```

### "Disk is full — snapshots are huge"

Snapshots accumulate at ~10–50 KB per event × thousands of events per day. Add a retention cron:

```bash
# Delete snapshot folders older than 90 days
0 5 * * * find /var/lib/docker/volumes/ai-attendance_storage/_data/snapshots -mindepth 3 -maxdepth 3 -type d -mtime +90 -exec rm -rf {} +
```

### "I bumped Python or Node version — image won't build"

Pin the exact base image tags in the Dockerfiles (`python:3.11-slim`, `node:20-alpine`). Don't use `python:latest` — it'll break randomly.

### "Multiple uvicorn workers — duplicate events"

Don't do it. The camera threads and the InsightFace model are global state inside one process. Two workers means two sets of camera threads, both writing the same events. Keep `--workers 1`.

---

## Quick Reference — Cheatsheet

```bash
# Bring everything up
docker compose up -d

# Bring everything down
docker compose down

# Rebuild after code change
docker compose build backend frontend && docker compose up -d

# View logs
docker compose logs -f backend

# Open a shell inside the backend
docker compose exec backend bash

# Run alembic manually
docker compose exec backend alembic upgrade head
docker compose exec backend alembic downgrade -1

# Talk to the DB directly
docker compose exec postgres psql -U $POSTGRES_USER $POSTGRES_DB

# Take a one-off backup
./scripts/backup.sh

# Renew SSL cert manually
docker run --rm -v $(pwd)/nginx/certs:/etc/letsencrypt -v $(pwd)/nginx/www:/var/www/certbot certbot/certbot renew
docker compose exec nginx nginx -s reload

# Restart a single service
docker compose restart backend
```

---

*This guide gets you to a hardened, HTTPS-protected, auto-recovering deployment. Pair it with the main [DOCUMENTATION.md](DOCUMENTATION.md) for what each part of the system actually does.*
