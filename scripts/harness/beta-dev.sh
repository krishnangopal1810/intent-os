#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_DIR="${INTENTOS_RUNTIME_DIR:-.harness/runtime}"
BETA_DIR="$RUNTIME_DIR/beta"
LOG_DIR="$RUNTIME_DIR/logs"
ARTIFACT_DIR="$RUNTIME_DIR/artifacts"
SITE_RUNTIME_DIR="$BETA_DIR"
SITE_DIR="$SITE_RUNTIME_DIR/site"
BETA_ENV="$BETA_DIR/app.env"
SERVICE_PID_FILE="$BETA_DIR/service.pid"
BRIDGE_PID_FILE="$BETA_DIR/fake-bridge.pid"
RECORDER_PID_FILE="$BETA_DIR/native-recorder.pid"
UI_PID_FILE="$BETA_DIR/ui.pid"
DB_PATH="$BETA_DIR/intentos.sqlite"
SERVICE_LOG="$LOG_DIR/beta-service.log"
BRIDGE_LOG="$LOG_DIR/beta-fake-bridge.log"
RECORDER_LOG="$LOG_DIR/beta-native-recorder.log"
UI_LOG="$LOG_DIR/beta-ui.log"
BETA_DATE="${INTENTOS_BETA_DATE:-$(date +%Y-%m-%d)}"
FAKE_BRIDGE="${INTENTOS_BETA_FAKE_BRIDGE:-0}"
PERMISSION_MODE="${INTENTOS_BETA_PERMISSION_MODE:-real}"
NATIVE_RECORDER="${INTENTOS_BETA_NATIVE_RECORDER:-1}"
NATIVE_RECORDER_INTERVAL="${INTENTOS_BETA_NATIVE_RECORDER_INTERVAL_SECONDS:-5}"
DEFAULT_SERVICE_PORT="${INTENTOS_BETA_SERVICE_PORT:-58917}"

mkdir -p "$BETA_DIR" "$LOG_DIR" "$ARTIFACT_DIR"

choose_port() {
  python3 - <<'PY'
import socket
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
}

require_port_available() {
  local port="$1"
  python3 - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
with socket.socket() as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError as exc:
        raise SystemExit(f"stable beta service port {port} is unavailable: {exc}")
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
for _ in range(40):
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

start_process() {
  local log_path="$1"
  shift
  python3 - "$log_path" "$@" <<'PY'
import subprocess
import sys
from pathlib import Path

log_path = Path(sys.argv[1])
command = sys.argv[2:]
log_path.parent.mkdir(parents=True, exist_ok=True)
log = log_path.open("ab", buffering=0)
process = subprocess.Popen(
    command,
    stdout=log,
    stderr=subprocess.STDOUT,
    stdin=subprocess.DEVNULL,
    start_new_session=True,
)
print(process.pid)
PY
}

scripts/harness/beta-stop.sh >/dev/null 2>&1 || true
scripts/harness/runtime-log.py beta dev_start mode=dogfood_harness

INTENTOS_RUNTIME_DIR="$SITE_RUNTIME_DIR" INTENTOS_PRESERVE_LIVE_ARTIFACTS=1 \
  scripts/product/dev.sh > "$UI_LOG" 2>&1

service_port="$DEFAULT_SERVICE_PORT"
require_port_available "$service_port"
service_url="http://127.0.0.1:$service_port"
: > "$SERVICE_LOG"
service_pid="$(start_process "$SERVICE_LOG" \
  python3 -m intentos.beta_cli serve \
  --db "$DB_PATH" \
  --privacy-policy data/capture/privacy_policy.json \
  --port "$service_port" \
  --service-log "$SERVICE_LOG" \
  --runtime-dir "$RUNTIME_DIR" \
  --permission-mode "$PERMISSION_MODE")"
echo "$service_pid" > "$SERVICE_PID_FILE"
wait_for_url "$service_url/api/status" "$service_pid"

if [ "$NATIVE_RECORDER" = "1" ]; then
  : > "$RECORDER_LOG"
  recorder_pid="$(start_process "$RECORDER_LOG" \
    python3 -m intentos.beta_cli live-recorder \
    --db "$DB_PATH" \
    --privacy-policy data/capture/privacy_policy.json \
    --interval-seconds "$NATIVE_RECORDER_INTERVAL" \
    --recorder-log "$RECORDER_LOG")"
  echo "$recorder_pid" > "$RECORDER_PID_FILE"
else
  recorder_pid=""
  rm -f "$RECORDER_PID_FILE"
  python3 - "$DB_PATH" <<'PY'
import sys
from intentos.beta import store

with store.connect(sys.argv[1]) as conn:
    store.init_db(conn)
    store.set_status(conn, "native_recorder_state", "disabled")
PY
fi

if [ "$FAKE_BRIDGE" = "1" ]; then
  python3 -m intentos.beta_cli fake-bridge \
    --service-url "$service_url/api/browser-event" \
    --input data/beta/fake_chrome_events.json \
    --once > "$BRIDGE_LOG" 2>&1

  bridge_pid="$(start_process "$BRIDGE_LOG" \
    python3 -m intentos.beta_cli fake-bridge \
    --service-url "$service_url/api/browser-event" \
    --input data/beta/fake_chrome_events.json \
    --interval-seconds "${INTENTOS_BETA_FAKE_BRIDGE_INTERVAL_SECONDS:-60}")"
  echo "$bridge_pid" > "$BRIDGE_PID_FILE"
else
  : > "$BRIDGE_LOG"
  rm -f "$BRIDGE_PID_FILE"
  bridge_pid=""
  python3 - "$DB_PATH" data/beta/fake_chrome_events.json data/capture/privacy_policy.json <<'PY'
import json
import sys
from intentos.beta import store
from intentos.beta.extension import chrome_event_to_activity
from intentos.capture.privacy import load_privacy_policy

db_path, fake_path, policy_path = sys.argv[1:]
policy = load_privacy_policy(policy_path)
raw = json.loads(open(fake_path, encoding="utf-8").read())
fixture_events = [
    event for index, item in enumerate(raw)
    if (event := chrome_event_to_activity(item, policy, index)) is not None
]
event_keys = [store.event_key(event) for event in fixture_events]
segment_keys = [store.segment_key(event) for event in fixture_events]

with store.connect(db_path) as conn:
    store.init_db(conn)
    if event_keys:
        placeholders = ",".join("?" for _ in event_keys)
        conn.execute(f"DELETE FROM activity_events WHERE event_key IN ({placeholders})", event_keys)
    if segment_keys:
        placeholders = ",".join("?" for _ in segment_keys)
        conn.execute(f"DELETE FROM classified_segments WHERE segment_key IN ({placeholders})", segment_keys)
        conn.execute(f"DELETE FROM corrections WHERE segment_key IN ({placeholders})", segment_keys)
    latest = conn.execute(
        "SELECT MAX(started_at) FROM activity_events WHERE source_adapter = ?",
        ("chrome_extension_bridge",),
    ).fetchone()[0]
    store.set_status(conn, "extension_state", "stale" if latest else "never_connected")
    store.set_status(conn, "last_browser_event_at", latest or "")
    if not latest:
        store.set_status(conn, "extension_last_seen_at", "")
    store.set_status(conn, "capture_state", "ready")
    store.set_status(conn, "capture_note", "")
PY
fi

python3 -m intentos.beta_cli daily-review \
  --db "$DB_PATH" \
  --date "$BETA_DATE" \
  --output "$ARTIFACT_DIR/beta-daily-review.json" >> "$UI_LOG" 2>&1

cat > "$SITE_DIR/beta-config.json" <<EOF
{
  "serviceUrl": "$service_url",
  "date": "$BETA_DATE"
}
EOF

ui_port="$(choose_port)"
ui_url="http://127.0.0.1:$ui_port/site/index.html?mode=beta"
ui_pid="$(start_process "$UI_LOG" env \
  INTENTOS_RUNTIME_DIR="$SITE_RUNTIME_DIR" \
  INTENTOS_APP_PORT="$ui_port" \
  scripts/product/start-ui.sh)"
echo "$ui_pid" > "$UI_PID_FILE"
wait_for_url "$ui_url" "$ui_pid"

{
  echo "INTENTOS_BETA_STATUS=running"
  echo "INTENTOS_BETA_MODE=dogfood_harness"
  echo "INTENTOS_BETA_DB=$DB_PATH"
  echo "INTENTOS_BETA_DATE=$BETA_DATE"
  echo "INTENTOS_BETA_SERVICE_PID=$service_pid"
  echo "INTENTOS_BETA_SERVICE_PORT=$service_port"
  echo "INTENTOS_BETA_SERVICE_URL=$service_url"
  echo "INTENTOS_BETA_SERVICE_LOG=$SERVICE_LOG"
  echo "INTENTOS_BETA_PERMISSION_MODE=$PERMISSION_MODE"
  echo "INTENTOS_BETA_NATIVE_RECORDER_ENABLED=$NATIVE_RECORDER"
  echo "INTENTOS_BETA_NATIVE_RECORDER_PID=$recorder_pid"
  echo "INTENTOS_BETA_NATIVE_RECORDER_LOG=$RECORDER_LOG"
  echo "INTENTOS_BETA_NATIVE_RECORDER_INTERVAL_SECONDS=$NATIVE_RECORDER_INTERVAL"
  echo "INTENTOS_BETA_FAKE_BRIDGE_ENABLED=$FAKE_BRIDGE"
  echo "INTENTOS_BETA_FAKE_BRIDGE_PID=$bridge_pid"
  echo "INTENTOS_BETA_FAKE_BRIDGE_LOG=$BRIDGE_LOG"
  echo "INTENTOS_BETA_UI_PID=$ui_pid"
  echo "INTENTOS_BETA_UI_PORT=$ui_port"
  echo "INTENTOS_BETA_UI_URL=$ui_url"
  echo "INTENTOS_BETA_SITE_DIR=$SITE_DIR"
  echo "INTENTOS_BETA_UI_LOG=$UI_LOG"
  echo "INTENTOS_BETA_DAILY_REVIEW=$ARTIFACT_DIR/beta-daily-review.json"
  echo "INTENTOS_BETA_STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$BETA_ENV"

scripts/harness/runtime-log.py beta dev_started \
  mode=dogfood_harness pid="$service_pid" port="$service_port" url="$ui_url"
echo "beta-dev: started"
cat "$BETA_ENV"
