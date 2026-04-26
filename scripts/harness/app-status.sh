#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_DIR=".harness/runtime"
APP_ENV="$RUNTIME_DIR/app.env"
PID_FILE="$RUNTIME_DIR/app.pid"

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
[ -f "$APP_ENV" ] && cat "$APP_ENV"
