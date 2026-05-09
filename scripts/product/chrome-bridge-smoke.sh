#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_DIR="${INTENTOS_RUNTIME_DIR:-.harness/runtime}"
BETA_ENV="$RUNTIME_DIR/beta/app.env"
ARTIFACT_DIR="$RUNTIME_DIR/artifacts"
LOG_DIR="$RUNTIME_DIR/logs"
SMOKE_JSON="$ARTIFACT_DIR/beta-chrome-bridge-smoke.json"
SMOKE_LOG="$LOG_DIR/beta-chrome-bridge-smoke.log"
SECONDS_TO_RUN="${INTENTOS_CHROME_BRIDGE_SMOKE_SECONDS:-300}"
POLL_SECONDS="${INTENTOS_CHROME_BRIDGE_SMOKE_POLL_SECONDS:-5}"

mkdir -p "$ARTIFACT_DIR" "$LOG_DIR"
: > "$SMOKE_LOG"

echo "chrome-bridge-smoke: starting beta without fake bridge" | tee -a "$SMOKE_LOG"
INTENTOS_RUNTIME_DIR="$RUNTIME_DIR" \
INTENTOS_BETA_FAKE_BRIDGE=0 \
INTENTOS_BETA_NATIVE_RECORDER=1 \
INTENTOS_BETA_PERMISSION_MODE=real \
scripts/harness/beta-dev.sh >> "$SMOKE_LOG" 2>&1

if [ ! -f "$BETA_ENV" ]; then
  echo "chrome-bridge-smoke: missing beta app.env" | tee -a "$SMOKE_LOG"
  exit 2
fi

service_url="$(grep '^INTENTOS_BETA_SERVICE_URL=' "$BETA_ENV" | tail -n 1 | cut -d= -f2-)"
ui_url="$(grep '^INTENTOS_BETA_UI_URL=' "$BETA_ENV" | tail -n 1 | cut -d= -f2-)"
fake_bridge="$(grep '^INTENTOS_BETA_FAKE_BRIDGE_ENABLED=' "$BETA_ENV" | tail -n 1 | cut -d= -f2-)"
api_token="$(grep '^INTENTOS_BETA_API_TOKEN=' "$BETA_ENV" | tail -n 1 | cut -d= -f2-)"

python3 - "$service_url" "$ui_url" "$fake_bridge" "$SMOKE_JSON" "$SMOKE_LOG" \
  "$SECONDS_TO_RUN" "$POLL_SECONDS" "$api_token" <<'PY'
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

service_url, ui_url, fake_bridge, smoke_path, log_path, seconds_text, poll_text, api_token = sys.argv[1:]
smoke_path = Path(smoke_path)
log_path = Path(log_path)
seconds_to_run = int(seconds_text)
poll_seconds = max(2, int(poll_text))


def log(message: str) -> None:
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")
    print(message, flush=True)


def get_json(url: str) -> dict:
    request = Request(url, headers={"X-IntentOS-Token": api_token})
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


started_at = datetime.now(timezone.utc)
baseline = get_json(f"{service_url}/api/status")
baseline_rows = baseline.get("row_counts", {}).get("activity_events")
samples = []
connected = False
deadline = time.monotonic() + seconds_to_run
log(
    "chrome-bridge-smoke: waiting for installed bridge; "
    f"baseline_rows={baseline_rows} timeout={seconds_to_run}s"
)

while time.monotonic() <= deadline:
    status = get_json(f"{service_url}/api/status")
    extension_state = (status.get("extension") or {}).get("state")
    native_state = (status.get("native_recorder") or {}).get("state")
    row_count = status.get("row_counts", {}).get("activity_events")
    sample = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "extension": extension_state,
        "native_recorder": native_state,
        "rows": row_count,
        "readiness": (status.get("readiness") or {}).get("state"),
    }
    samples.append(sample)
    log(
        "chrome-bridge-smoke: "
        f"extension={extension_state} native_recorder={native_state} rows={row_count}"
    )
    if extension_state in {"connected", "posting_events"}:
        connected = True
        break
    time.sleep(min(poll_seconds, max(0, deadline - time.monotonic())))

final_status = get_json(f"{service_url}/api/status")
failures = []
if fake_bridge != "0":
    failures.append("fake bridge was enabled; installed-extension smoke must not seed fake rows")
if (final_status.get("native_recorder") or {}).get("state") != "running":
    failures.append("native recorder is not running; it remains the primary beta capture path")
if not connected:
    failures.append("Chrome bridge did not reach connected or posting_events before timeout")

payload = {
    "status": "blocked" if failures else "passed",
    "started_at": started_at.isoformat(timespec="seconds").replace("+00:00", "Z"),
    "duration_seconds": int((datetime.now(timezone.utc) - started_at).total_seconds()),
    "service_url": service_url,
    "ui_url": ui_url,
    "fake_bridge_enabled": fake_bridge == "1",
    "baseline_rows": baseline_rows,
    "final_rows": final_status.get("row_counts", {}).get("activity_events"),
    "extension": final_status.get("extension"),
    "native_recorder": final_status.get("native_recorder"),
    "readiness": final_status.get("readiness"),
    "samples": samples,
    "failures": failures,
}
smoke_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
log(f"chrome-bridge-smoke: {payload['status']}; wrote {smoke_path}")
if failures:
    for failure in failures:
        log(f"chrome-bridge-smoke: blocker: {failure}")
    raise SystemExit(2)
PY
