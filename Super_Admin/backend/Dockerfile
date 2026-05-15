# syntax=docker/dockerfile:1.6

# Backend image for Railway / Fly / any Linux container host.
# Designed for **API-only** mode (DISABLE_CAMERA_WORKERS=true) — the
# heavy InsightFace runtime is still installed (cheaper than
# maintaining two requirements files) but is never imported when the
# env flag is set, so cold-start stays under ~10 s.

FROM python:3.12-slim AS base

# --- System dependencies -----------------------------------------------------
# libgl1 / libglib2 / libsm6 / libxext6: required by opencv-python at import
# time even when no UI is used. libgomp1: OpenMP runtime used by onnxruntime.
# All `--no-install-recommends` to keep the image small. Cleanup in the same
# layer to avoid leaving the apt cache behind.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgomp1 \
        ca-certificates \
        curl \
        # build-essential is needed because `insightface` ships a
        # Cython extension that compiles g++ at install time. Even
        # when DISABLE_CAMERA_WORKERS skips the runtime import, the
        # wheel still has to build during `pip install`.
        build-essential \
        python3-dev \
 && rm -rf /var/lib/apt/lists/*

# --- Python deps --------------------------------------------------------------
# Copy requirements first so the install layer is cached across code changes.
# `--no-cache-dir` shaves ~150 MB off the final image.
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# --- App code -----------------------------------------------------------------
# Everything in the build context (backend/) lands here. .dockerignore keeps
# the storage/, logs/, and .env out so we don't ship the model files or local
# secrets into the image.
COPY . ./

# Buffered stdout makes Railway's live logs feel laggy; turn buffering off so
# every print() / log line streams immediately.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Railway injects $PORT at runtime. The default is for local `docker run`
# without -e PORT=…
ENV PORT=8000
EXPOSE 8000

# Run alembic on every boot — idempotent (it no-ops once the DB is at head)
# and keeps the deploy "schema in sync" with the code without a separate
# release step. If migrations fail, the container exits and Railway shows
# the failure on the deploy log instead of half-booting against an old DB.
# Use a small shim script (start.sh) instead of inlining shell — keeps
# logs reliable and lets us flush/echo at every stage. Several Linux
# images can buffer-discard the tail of an `&&`-chained inline CMD if
# the previous tool flushes oddly; running the same logic from a real
# script file is the documented-stable pattern.
COPY start.sh /start.sh
RUN chmod +x /start.sh
CMD ["/start.sh"]
