#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_DIR=".harness/runtime"
LOG_DIR="$RUNTIME_DIR/logs"
ARTIFACT_DIR="$RUNTIME_DIR/artifacts"
APP_ENV="$RUNTIME_DIR/app.env"
PID_FILE="$RUNTIME_DIR/app.pid"

mkdir -p "$LOG_DIR"

choose_port() {
  python3 - <<'PY'
import socket
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
}

wait_for_url() {
  local url="$1"
  local pid="$2"
  python3 - "$url" "$pid" <<'PY'
import os
import sys
import time
from urllib.request import urlopen

url = sys.argv[1]
pid = int(sys.argv[2])
last_error = None
for _ in range(30):
    try:
        os.kill(pid, 0)
    except OSError as exc:
        raise SystemExit(f"process {pid} exited before serving {url}: {exc}")
    try:
        with urlopen(url, timeout=1) as response:
            if 200 <= response.status < 400:
                raise SystemExit(0)
            last_error = f"HTTP {response.status}"
    except Exception as exc:
        last_error = exc
        time.sleep(0.1)
raise SystemExit(f"timed out waiting for {url}: {last_error}")
PY
}

if [ -f "$PID_FILE" ]; then
  pid="$(cat "$PID_FILE")"
  if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
    if scripts/harness/app-status.sh >/dev/null 2>&1; then
      echo "dev: app already running with pid $pid"
      [ -f "$APP_ENV" ] && cat "$APP_ENV"
      exit 0
    fi
    echo "dev: recorded app pid $pid is unhealthy; rebuilding runtime"
    kill "$pid" >/dev/null 2>&1 || true
  fi
  rm -f "$PID_FILE"
fi

if [ -x scripts/product/dev.sh ]; then
  export INTENTOS_RUNTIME_DIR="$RUNTIME_DIR"
  rm -f "$PID_FILE"
  scripts/harness/runtime-log.py harness dev_start mode=artifact_build
  scripts/product/dev.sh > "$LOG_DIR/app.log" 2>&1

  if [ -x scripts/product/start-ui.sh ]; then
    port="$(choose_port)"
    url="http://127.0.0.1:$port/site/index.html"
    INTENTOS_RUNTIME_DIR="$RUNTIME_DIR" INTENTOS_APP_PORT="$port" \
      nohup scripts/product/start-ui.sh >> "$LOG_DIR/app.log" 2>&1 &
    pid="$!"
    echo "$pid" > "$PID_FILE"
    if ! wait_for_url "$url" "$pid"; then
      scripts/harness/runtime-log.py harness ui_start_failed mode=ui pid="$pid" port="$port"
      kill "$pid" >/dev/null 2>&1 || true
      rm -f "$PID_FILE"
      echo "dev: product UI runtime failed to start; see $LOG_DIR/app.log" >&2
      exit 1
    fi
    scripts/harness/runtime-log.py harness ui_started \
      mode=ui pid="$pid" port="$port" url="$url"
    {
      echo "INTENTOS_APP_STATUS=running"
      echo "INTENTOS_APP_MODE=ui"
      echo "INTENTOS_APP_PID=$pid"
      echo "INTENTOS_APP_PORT=$port"
      echo "INTENTOS_APP_URL=$url"
      echo "INTENTOS_APP_LOG=$LOG_DIR/app.log"
      echo "INTENTOS_ARTIFACT_DIR=$ARTIFACT_DIR"
      echo "INTENTOS_SITE_DIR=$RUNTIME_DIR/site"
      echo "INTENTOS_APP_STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    } > "$APP_ENV"
    echo "dev: started product UI runtime with pid $pid"
    cat "$APP_ENV"
    exit 0
  else
    scripts/harness/runtime-log.py harness dev_completed mode=cli
    {
      echo "INTENTOS_APP_STATUS=completed"
      echo "INTENTOS_APP_MODE=cli"
      echo "INTENTOS_APP_LOG=$LOG_DIR/app.log"
      echo "INTENTOS_ARTIFACT_DIR=$ARTIFACT_DIR"
      echo "INTENTOS_APP_COMPLETED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    } > "$APP_ENV"
    echo "dev: completed product runtime"
    cat "$APP_ENV"
    exit 0
  fi
fi

if [ -f package.json ] && command -v node >/dev/null 2>&1 && node -e "const p=require('./package.json'); process.exit(p.scripts && p.scripts.dev ? 0 : 1)"; then
  nohup npm run dev > "$LOG_DIR/app.log" 2>&1 &
  pid="$!"
  echo "$pid" > "$PID_FILE"
  scripts/harness/runtime-log.py harness npm_dev_started mode=npm pid="$pid"
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
