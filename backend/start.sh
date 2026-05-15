#!/usr/bin/env bash
# Starts every backend process under a supervise() loop that auto-restarts
# on crash. Invoked by `npm run dev` at the repo root via concurrently, or
# runnable on its own (`bash backend/start.sh`).
#
# Optional env:
#   INGEST_API_URL    — comma-separated remote ingest URLs for live
#                       replication. Localhost entries are stripped because
#                       capture.py writes directly to the local DB.
#   REMOTE_SYNC_URLS  — comma-separated targets for the periodic replay
#                       worker. Defaults to the production Railway URL.
#   REMOTE_SYNC_INTERVAL — seconds between replay passes (default 300).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

# Local-only env (camera credentials, MAC pin, discovery subnets, etc.).
# Gitignored. `set -a` exports every var defined inside the file so the
# Python workers spawned below inherit them.
if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source ./.env
  set +a
fi

: "${INGEST_API_URL:=https://hype-dashboard-production-8938.up.railway.app/api/ingest}"
export INGEST_API_URL

: "${REMOTE_SYNC_URLS:=https://hype-dashboard-production-8938.up.railway.app/api/ingest}"
: "${REMOTE_SYNC_INTERVAL:=300}"

pids=()

cleanup() {
  echo
  echo "[backend] stopping supervised children..."
  for pid in "${pids[@]:-}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill -TERM "$pid" 2>/dev/null || true
    fi
  done
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# Run a child forever, restarting on crash with bounded exponential
# backoff (capped at 30s). Each subshell isolates its own grandchild PID
# so shutdown propagates cleanly.
supervise() {
  local name="$1"; shift
  (
    pid=0
    trap 'if (( pid > 0 )); then kill -TERM "$pid" 2>/dev/null; wait "$pid" 2>/dev/null; fi; exit 0' TERM INT
    attempt=0
    while true; do
      if (( attempt > 0 )); then
        backoff=$(( 2 ** (attempt < 4 ? attempt : 4) ))
        (( backoff > 30 )) && backoff=30
        echo "[supervisor:$name] restart #$attempt in ${backoff}s"
        sleep "$backoff"
      fi
      echo "[supervisor:$name] starting: $*"
      "$@" &
      pid=$!
      wait "$pid"
      rc=$?
      pid=0
      echo "[supervisor:$name] exited rc=$rc"
      attempt=$(( attempt + 1 ))
    done
  ) &
}

supervise api uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pids+=($!)

sleep 2

supervise capture python capture.py
pids+=($!)

supervise backfill python backfill_from_camera.py
pids+=($!)

if [ -n "$REMOTE_SYNC_URLS" ]; then
  IFS=',' read -r -a _sync_targets <<< "$REMOTE_SYNC_URLS"
  for target in "${_sync_targets[@]}"; do
    target_trimmed="$(echo "$target" | xargs)"
    [ -z "$target_trimmed" ] && continue
    echo "[supervisor] sync loop every ${REMOTE_SYNC_INTERVAL}s → $target_trimmed"
    supervise sync python replay_to_railway.py --target "$target_trimmed" --loop "$REMOTE_SYNC_INTERVAL" --sleep 0.15
    pids+=($!)
  done
fi

wait
