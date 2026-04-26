#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_DIR=".harness/runtime"
APP_ENV="$RUNTIME_DIR/app.env"
PID_FILE="$RUNTIME_DIR/app.pid"

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
