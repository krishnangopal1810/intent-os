#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_DIR="${INTENTOS_RUNTIME_DIR:-.harness/runtime}"
WORK_DIR="$RUNTIME_DIR/beta-validation"
ARTIFACT_DIR="$RUNTIME_DIR/artifacts"
LOG_DIR="$RUNTIME_DIR/logs"
SITE_DIR="$RUNTIME_DIR/site"
DB_PATH="$WORK_DIR/intentos.sqlite"
SERVICE_LOG="$LOG_DIR/beta-service.log"
VALIDATION_JSON="$ARTIFACT_DIR/beta-validation.json"
DAILY_REVIEW_JSON="$ARTIFACT_DIR/beta-daily-review.json"
BETA_DATE="2026-04-27"

mkdir -p "$WORK_DIR" "$ARTIFACT_DIR" "$LOG_DIR"
rm -f "$DB_PATH" "$DB_PATH-wal" "$DB_PATH-shm"

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
last = None
for _ in range(40):
    try:
        os.kill(pid, 0)
    except OSError as exc:
        raise SystemExit(f"process {pid} exited: {exc}")
    try:
        with urlopen(url, timeout=1) as response:
            if 200 <= response.status < 400:
                raise SystemExit(0)
            last = response.status
    except Exception as exc:
        last = exc
        time.sleep(0.1)
raise SystemExit(f"timed out waiting for {url}: {last}")
PY
}

service_port="$(choose_port)"
service_url="http://127.0.0.1:$service_port"
: > "$SERVICE_LOG"
python3 -m intentos.beta_cli serve \
  --db "$DB_PATH" \
  --privacy-policy data/capture/privacy_policy.json \
  --port "$service_port" \
  --service-log "$SERVICE_LOG" \
  >> "$SERVICE_LOG" 2>&1 &
service_pid="$!"

cleanup() {
  if kill -0 "$service_pid" >/dev/null 2>&1; then
    kill "$service_pid" >/dev/null 2>&1 || true
  fi
  if [ -n "${ui_pid:-}" ] && kill -0 "$ui_pid" >/dev/null 2>&1; then
    kill "$ui_pid" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

wait_for_url "$service_url/api/status" "$service_pid"
python3 -m intentos.beta_cli fake-bridge \
  --service-url "$service_url/api/browser-event" \
  --input data/beta/fake_chrome_events.json \
  --once > "$LOG_DIR/beta-fake-bridge.log" 2>&1

INTENTOS_RUNTIME_DIR="$RUNTIME_DIR" INTENTOS_PRESERVE_LIVE_ARTIFACTS=1 \
  scripts/product/dev.sh > "$LOG_DIR/beta-ui-build.log" 2>&1
cat > "$SITE_DIR/beta-config.json" <<EOF
{
  "serviceUrl": "$service_url",
  "date": "$BETA_DATE"
}
EOF

ui_port="$(choose_port)"
INTENTOS_RUNTIME_DIR="$RUNTIME_DIR" INTENTOS_APP_PORT="$ui_port" \
  scripts/product/start-ui.sh > "$LOG_DIR/beta-ui.log" 2>&1 &
ui_pid="$!"
ui_url="http://127.0.0.1:$ui_port/site/index.html"
wait_for_url "$ui_url" "$ui_pid"

python3 - "$service_url" "$ui_url" "$VALIDATION_JSON" "$DAILY_REVIEW_JSON" "$BETA_DATE" <<'PY'
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

service_url, ui_url, validation_path, review_path, date = sys.argv[1:]

def get_json(url):
    with urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))

def post_json(url, payload):
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))

status = get_json(f"{service_url}/api/status")
review = get_json(f"{service_url}/api/daily-review?date={date}")
if status["row_counts"]["activity_events"] < 3:
    raise AssertionError("expected fixture browser events")
if not review["items"]:
    raise AssertionError("daily review must include timeline items")
segment = review["items"][0]
correction = post_json(
    f"{service_url}/api/corrections",
    {
        "segment": segment,
        "corrected_label": "learning",
        "apply_to_future": True,
    },
)
corrected = get_json(f"{service_url}/api/daily-review?date={date}")
if corrected["items"][0]["label"] != "learning":
    raise AssertionError("correction did not update rendered report")
pause = post_json(f"{service_url}/api/pause", {"minutes": 15})
paused = get_json(f"{service_url}/api/status")
if not paused["pause"]["paused"]:
    raise AssertionError("pause state was not set")
post_json(f"{service_url}/api/resume", {})
with urlopen(ui_url, timeout=3) as response:
    html = response.read().decode("utf-8")
with urlopen(ui_url.replace("index.html", "app.js"), timeout=3) as response:
    app_js = response.read().decode("utf-8")
with urlopen(ui_url.replace("index.html", "beta-config.json"), timeout=3) as response:
    config = json.loads(response.read().decode("utf-8"))
for token in ["data-correction-controls", "POST /api/corrections", "daily-review"]:
    if token not in html + app_js:
        raise AssertionError(f"missing beta UI token: {token}")
delete = post_json(f"{service_url}/api/delete-local-data", {})
deleted = get_json(f"{service_url}/api/status")
if deleted["row_counts"]["activity_events"] != 0:
    raise AssertionError("delete-local-data did not clear activity events")
Path(review_path).write_text(json.dumps(corrected, indent=2) + "\n", encoding="utf-8")
validation = {
    "status": "ok",
    "service_url": service_url,
    "ui_url": ui_url,
    "initial_rows": status["row_counts"],
    "correction": correction,
    "pause": pause,
    "delete": delete,
    "config": config,
}
Path(validation_path).write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
print(json.dumps(validation, indent=2))
PY

echo "validate-beta: ok"
