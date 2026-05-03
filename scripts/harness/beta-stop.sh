#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

BETA_DIR=".harness/runtime/beta"
BETA_ENV="$BETA_DIR/app.env"

pid_from_env() {
  local key="$1"
  if [ -f "$BETA_ENV" ]; then
    grep "^$key=" "$BETA_ENV" | tail -n 1 | cut -d= -f2-
  fi
}

wait_for_exit() {
  local label="$1"
  local pid="$2"
  local attempt
  for attempt in {1..30}; do
    if ! kill -0 "$pid" >/dev/null 2>&1; then
      return
    fi
    sleep 0.1
  done
  if kill -0 "$pid" >/dev/null 2>&1; then
    kill -KILL "$pid" >/dev/null 2>&1 || true
    echo "beta-stop: force stopped $label pid $pid"
  fi
  for attempt in {1..10}; do
    if ! kill -0 "$pid" >/dev/null 2>&1; then
      return
    fi
    sleep 0.1
  done
}

stop_pid_file() {
  local label="$1"
  local pid_file="$2"
  local pid
  if [ -f "$pid_file" ]; then
    pid="$(cat "$pid_file")"
  else
    pid="$(pid_from_env "$3" || true)"
  fi
  if [ -z "${pid:-}" ]; then
    return
  fi
  if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
    kill "$pid" >/dev/null 2>&1 || true
    wait_for_exit "$label" "$pid"
    echo "beta-stop: stopped $label pid $pid"
  else
    echo "beta-stop: recorded $label process was not running"
  fi
  rm -f "$pid_file"
}

stop_pid_file "fake bridge" "$BETA_DIR/fake-bridge.pid" "INTENTOS_BETA_FAKE_BRIDGE_PID"
stop_pid_file "native recorder" "$BETA_DIR/native-recorder.pid" "INTENTOS_BETA_NATIVE_RECORDER_PID"
stop_pid_file "service" "$BETA_DIR/service.pid" "INTENTOS_BETA_SERVICE_PID"
stop_pid_file "ui" "$BETA_DIR/ui.pid" "INTENTOS_BETA_UI_PID"

db_path="$(pid_from_env INTENTOS_BETA_DB || true)"
if [ -n "${db_path:-}" ] && [ -f "$db_path" ]; then
  python3 - "$db_path" <<'PY'
import sys
from intentos.beta import store

conn = store.connect(sys.argv[1])
try:
    store.init_db(conn)
    store.set_status(conn, "service_state", "stopped")
    store.set_status(conn, "capture_state", "stopped")
    store.set_status(conn, "native_recorder_state", "stopped")
finally:
    conn.close()
PY
fi

if [ -f "$BETA_DIR/app.env" ]; then
  tmp_env="$BETA_DIR/app.env.tmp"
  grep -v '^INTENTOS_BETA_STATUS=' "$BETA_DIR/app.env" > "$tmp_env" || true
  echo "INTENTOS_BETA_STATUS=stopped" >> "$tmp_env"
  mv "$tmp_env" "$BETA_DIR/app.env"
fi
