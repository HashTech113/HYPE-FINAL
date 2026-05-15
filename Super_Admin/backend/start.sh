#!/bin/sh
# Container entrypoint. Each phase prints a marker to stdout (with
# stdbuf to defeat output buffering) so `railway logs` can prove
# exactly how far we got if startup hangs.

set -e

PORT="${PORT:-8000}"

echo "[boot] start.sh running"
echo "[boot] PORT=${PORT}"
echo "[boot] DATABASE_URL host=$(echo "${DATABASE_URL}" | sed -E 's/.*@([^/]+)\/.*/\1/' )"
echo "[boot] API_ONLY=${API_ONLY:-} DISABLE_CAMERA_WORKERS=${DISABLE_CAMERA_WORKERS:-}"

echo "[boot] running alembic upgrade head"
alembic upgrade head
echo "[boot] alembic done"

echo "[boot] importing app to verify it loads cleanly"
python -u -c "import app.main; print('[boot] app.main imported OK')"

echo "[boot] launching uvicorn on 0.0.0.0:${PORT}"
exec python -u -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --log-level info --no-access-log
