#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_DIR=".harness/runtime"
APP_ENV="$RUNTIME_DIR/app.env"
PID_FILE="$RUNTIME_DIR/app.pid"
CAPTURE_PID_FILE="$RUNTIME_DIR/capture.pid"

value_from_env() {
  local key="$1"
  grep "^$key=" "$APP_ENV" | tail -n 1 | cut -d= -f2-
}

if [ -f "$APP_ENV" ] && grep -q '^INTENTOS_APP_STATUS=completed$' "$APP_ENV"; then
  echo "app-status: completed"
  cat "$APP_ENV"
  exit 0
fi

if [ ! -f "$PID_FILE" ]; then
  echo "app-status: no app runtime recorded"
  exit 2
fi

pid="$(cat "$PID_FILE")"
if [ -z "$pid" ] || ! kill -0 "$pid" >/dev/null 2>&1; then
  echo "app-status: recorded app process is not running"
  exit 1
fi

echo "app-status: running"
echo "pid=$pid"
if [ -f "$APP_ENV" ]; then
  cat "$APP_ENV"
  capture_required=false
  if grep -Eq '^INTENTOS_CAPTURE_MODE=(background_live_sensor|background_timeline)$' "$APP_ENV"; then
    capture_required=true
  fi
  if [ -f "$CAPTURE_PID_FILE" ]; then
    capture_pid="$(cat "$CAPTURE_PID_FILE")"
    if [ -n "$capture_pid" ] && kill -0 "$capture_pid" >/dev/null 2>&1; then
      echo "capture=running pid=$capture_pid"
    else
      echo "capture=not_running pid=$capture_pid"
      if [ "$capture_required" = true ]; then
        exit 1
      fi
    fi
  else
    echo "capture=not_recorded"
    if [ "$capture_required" = true ]; then
      exit 1
    fi
  fi
  capture_status="$(value_from_env INTENTOS_CAPTURE_STATUS || true)"
  if [ -n "${capture_status:-}" ] && [ -f "$capture_status" ]; then
    echo "capture_status_json=$capture_status"
    cat "$capture_status"
  fi
  url="$(value_from_env INTENTOS_APP_URL || true)"
  if [ -n "${url:-}" ]; then
    python3 - "$url" <<'PY'
import sys
from urllib.request import urlopen

url = sys.argv[1]
try:
    with urlopen(url, timeout=1) as response:
        print(f"health=http_{response.status}")
except Exception as exc:
    print(f"health=failed:{exc}")
    raise SystemExit(1)
PY
  fi
fi
