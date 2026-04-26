#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_DIR=".harness/runtime"
LOG_DIR="$RUNTIME_DIR/logs"
APP_ENV="$RUNTIME_DIR/app.env"
PID_FILE="$RUNTIME_DIR/app.pid"

mkdir -p "$LOG_DIR"

if [ -f "$PID_FILE" ]; then
  pid="$(cat "$PID_FILE")"
  if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
    echo "dev: app already running with pid $pid"
    [ -f "$APP_ENV" ] && cat "$APP_ENV"
    exit 0
  fi
fi

if [ -x scripts/product/dev.sh ]; then
  scripts/product/dev.sh > "$LOG_DIR/app.log" 2>&1 &
  pid="$!"
  echo "$pid" > "$PID_FILE"
  {
    echo "INTENTOS_APP_PID=$pid"
    echo "INTENTOS_APP_LOG=$LOG_DIR/app.log"
    echo "INTENTOS_APP_STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$APP_ENV"
  echo "dev: started product runtime with pid $pid"
  cat "$APP_ENV"
  exit 0
fi

if [ -f package.json ] && command -v node >/dev/null 2>&1 && node -e "const p=require('./package.json'); process.exit(p.scripts && p.scripts.dev ? 0 : 1)"; then
  npm run dev > "$LOG_DIR/app.log" 2>&1 &
  pid="$!"
  echo "$pid" > "$PID_FILE"
  {
    echo "INTENTOS_APP_PID=$pid"
    echo "INTENTOS_APP_LOG=$LOG_DIR/app.log"
    echo "INTENTOS_APP_STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$APP_ENV"
  echo "dev: started npm dev runtime with pid $pid"
  cat "$APP_ENV"
  exit 0
fi

echo "dev: no product runtime configured" >&2
echo "dev: add scripts/product/dev.sh or an npm dev script" >&2
exit 2
