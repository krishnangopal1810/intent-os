#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_DIR=".harness/runtime"
APP_ENV="$RUNTIME_DIR/app.env"
PID_FILE="$RUNTIME_DIR/app.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "app-status: no app pid recorded"
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
