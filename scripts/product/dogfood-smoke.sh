#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_DIR="${INTENTOS_RUNTIME_DIR:-.harness/runtime}"
BETA_ENV="$RUNTIME_DIR/beta/app.env"
ARTIFACT_DIR="$RUNTIME_DIR/artifacts"
LOG_DIR="$RUNTIME_DIR/logs"
SMOKE_JSON="$ARTIFACT_DIR/beta-dogfood-smoke.json"
REVIEW_JSON="$ARTIFACT_DIR/beta-dogfood-smoke-daily-review.json"
SCREENSHOT="$ARTIFACT_DIR/beta-dogfood-smoke-dashboard.png"
SMOKE_LOG="$LOG_DIR/beta-dogfood-smoke.log"
SECONDS_TO_RUN="${INTENTOS_DOGFOOD_SMOKE_SECONDS:-1800}"
POLL_SECONDS="${INTENTOS_DOGFOOD_SMOKE_POLL_SECONDS:-60}"

mkdir -p "$ARTIFACT_DIR" "$LOG_DIR"
: > "$SMOKE_LOG"

echo "dogfood-smoke: starting beta with native recorder and without fake Chrome bridge" | tee -a "$SMOKE_LOG"
INTENTOS_RUNTIME_DIR="$RUNTIME_DIR" \
INTENTOS_BETA_FAKE_BRIDGE=0 \
INTENTOS_BETA_NATIVE_RECORDER=1 \
INTENTOS_BETA_PERMISSION_MODE=real \
scripts/harness/beta-dev.sh >> "$SMOKE_LOG" 2>&1

if [ ! -f "$BETA_ENV" ]; then
  echo "dogfood-smoke: missing beta app.env" | tee -a "$SMOKE_LOG"
  exit 2
fi

service_url="$(grep '^INTENTOS_BETA_SERVICE_URL=' "$BETA_ENV" | tail -n 1 | cut -d= -f2-)"
ui_url="$(grep '^INTENTOS_BETA_UI_URL=' "$BETA_ENV" | tail -n 1 | cut -d= -f2-)"
api_token="$(grep '^INTENTOS_BETA_API_TOKEN=' "$BETA_ENV" | tail -n 1 | cut -d= -f2-)"
date_value="$(date +%Y-%m-%d)"

python3 - "$service_url" "$ui_url" "$date_value" "$SMOKE_JSON" "$REVIEW_JSON" \
  "$SCREENSHOT" "$SMOKE_LOG" "$SECONDS_TO_RUN" "$POLL_SECONDS" "$api_token" <<'PY'
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

service_url, ui_url, date_value, smoke_path, review_path, screenshot_path, log_path, seconds_text, poll_text, api_token = sys.argv[1:]
smoke_path = Path(smoke_path)
review_path = Path(review_path)
screenshot_path = Path(screenshot_path)
log_path = Path(log_path)
seconds_to_run = int(seconds_text)
poll_seconds = max(5, int(poll_text))


def log(message: str) -> None:
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")
    print(message, flush=True)


def get_json(url: str) -> dict:
    request = Request(url, headers={"X-IntentOS-Token": api_token})
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-IntentOS-Token": api_token},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def permission_failures(status: dict) -> list[str]:
    failures = []
    for key, item in status.get("permissions", {}).items():
        if key == "chrome_extension":
            continue
        state = item.get("state")
        if state in {"blocked", "needs_action"}:
            failures.append(f"{key}: {item.get('detail')}")
    return failures


def extension_warning(status: dict) -> str | None:
    extension = status.get("extension") or {}
    state = extension.get("state")
    if state in {"connected", "posting_events", "fixture_bridge"}:
        return None
    return "Chrome bridge is absent or stale; native recorder is still the beta launch path."


def verify_pause_resume() -> dict:
    before = get_json(f"{service_url}/api/status")
    interval = int((before.get("native_recorder") or {}).get("interval_seconds") or 5)
    wait_seconds = max(6, interval + 2)
    post_json(f"{service_url}/api/pause", {"minutes": 15})
    time.sleep(wait_seconds)
    settled = get_json(f"{service_url}/api/status")
    settled_rows = settled["row_counts"]["activity_events"]
    time.sleep(wait_seconds)
    paused = get_json(f"{service_url}/api/status")
    paused_rows = paused["row_counts"]["activity_events"]
    post_json(f"{service_url}/api/resume", {})
    resumed = get_json(f"{service_url}/api/status")
    return {
        "wait_seconds": wait_seconds,
        "before_rows": before["row_counts"]["activity_events"],
        "settled_rows": settled_rows,
        "paused_rows": paused_rows,
        "resume_status": resumed.get("pause", {}),
        "passed": paused_rows == settled_rows and not resumed.get("pause", {}).get("paused"),
    }


def privacy_failures(events: list[dict]) -> list[str]:
    forbidden = {"body", "page_body", "content", "cookies", "cookie", "authorization", "token", "password"}
    failures = []
    for index, event in enumerate(events):
        metadata = event.get("metadata") or {}
        found = sorted(key for key in metadata if key.lower() in forbidden)
        if found:
            failures.append(f"event {index} contains unsupported private metadata: {', '.join(found)}")
        if any(key in event for key in forbidden):
            failures.append(f"event {index} contains unsupported private top-level fields")
    return failures


def find_browser() -> str | None:
    explicit = os.environ.get("INTENTOS_BROWSER_BIN")
    if explicit and Path(explicit).is_file():
        return explicit
    for candidate in [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]:
        if Path(candidate).is_file():
            return candidate
    return None


def capture_screenshot() -> dict:
    browser = find_browser()
    if not browser:
        return {"status": "skipped", "reason": "Chrome or Chromium not found"}
    profile = screenshot_path.parent / "dogfood-smoke-browser-profile"
    subprocess.run(["rm", "-rf", str(profile)], check=False)
    command = [
        browser,
        "--headless=new",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-extensions",
        "--disable-gpu",
        "--disable-sync",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1440,1000",
        f"--user-data-dir={profile}",
        f"--screenshot={screenshot_path}",
        ui_url,
    ]
    try:
        subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    except subprocess.TimeoutExpired:
        if screenshot_path.is_file() and screenshot_path.stat().st_size > 20000:
            return {"status": "captured", "path": str(screenshot_path), "note": "Chrome timed out after writing screenshot"}
        return {"status": "failed", "reason": "Chrome screenshot timed out", "path": str(screenshot_path)}
    if screenshot_path.is_file() and screenshot_path.stat().st_size > 20000:
        return {"status": "captured", "path": str(screenshot_path)}
    return {"status": "failed", "path": str(screenshot_path)}


started_at = datetime.now(timezone.utc)
permission_status = post_json(f"{service_url}/api/permissions/check", {})
baseline = get_json(f"{service_url}/api/status")
native_state = (baseline.get("native_recorder") or {}).get("state")
if native_state != "running":
    payload = {
        "status": "blocked",
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "duration_seconds": 0,
        "service_url": service_url,
        "ui_url": ui_url,
        "failures": [f"native recorder is not running; current state is {native_state}"],
        "permission_preflight": permission_status.get("permissions", {}),
        "baseline_status": baseline,
        "pause_check": None,
    }
    smoke_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    log(f"dogfood-smoke: blocked: {payload['failures'][0]}")
    raise SystemExit(2)
pause_check = verify_pause_resume()
baseline = get_json(f"{service_url}/api/status")
baseline_rows = baseline["row_counts"]["activity_events"]
samples = []
log(f"dogfood-smoke: observing for {seconds_to_run}s; baseline_rows={baseline_rows}")

deadline = time.monotonic() + seconds_to_run
while time.monotonic() < deadline:
    status = get_json(f"{service_url}/api/status")
    samples.append(
        {
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "rows": status["row_counts"]["activity_events"],
            "last_event_time": status.get("last_event_time"),
            "readiness": status.get("readiness", {}).get("state"),
            "native_recorder": status.get("native_recorder", {}).get("state"),
            "extension": status.get("extension", {}).get("state"),
        }
    )
    remaining = max(0, int(deadline - time.monotonic()))
    log(
        "dogfood-smoke: "
        f"rows={samples[-1]['rows']} "
        f"native_recorder={samples[-1]['native_recorder']} "
        f"extension={samples[-1]['extension']} "
        f"remaining={remaining}s"
    )
    time.sleep(min(poll_seconds, max(0, deadline - time.monotonic())))

final_status = get_json(f"{service_url}/api/status")
review = get_json(f"{service_url}/api/daily-review?date={date_value}")
events = get_json(f"{service_url}/api/events?date={date_value}")["items"]
review_path.write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")
screenshot = capture_screenshot()

final_rows = final_status["row_counts"]["activity_events"]
event_seen = final_rows > baseline_rows
failures = []
failures.extend(permission_failures(final_status))
failures.extend(privacy_failures(events))
if not pause_check["passed"]:
    failures.append(
        "pause did not hold as a privacy control; rows changed from "
        f"{pause_check['settled_rows']} to {pause_check['paused_rows']} while paused"
    )
final_native_state = (final_status.get("native_recorder") or {}).get("state")
if final_native_state != "running":
    failures.append(f"native recorder stopped or failed during smoke; final state is {final_native_state}")
if not event_seen:
    failures.append("no new real native recorder or Chrome bridge events reached SQLite during the smoke window")
if not review.get("items"):
    failures.append("daily review did not render any timeline items for the smoke date")
if screenshot["status"] == "failed":
    failures.append("dashboard screenshot was not captured")
warnings = []
warning = extension_warning(final_status)
if warning:
    warnings.append(warning)

payload = {
    "status": "blocked" if failures else "passed",
    "started_at": started_at.isoformat().replace("+00:00", "Z"),
    "duration_seconds": seconds_to_run,
    "service_url": service_url,
    "ui_url": ui_url,
    "date": date_value,
    "baseline_rows": baseline_rows,
    "final_rows": final_rows,
    "baseline_last_event_time": baseline.get("last_event_time"),
    "final_last_event_time": final_status.get("last_event_time"),
    "event_seen": event_seen,
    "pause_check": pause_check,
    "native_recorder": final_status.get("native_recorder", {}),
    "extension": final_status.get("extension", {}),
    "permission_preflight": permission_status.get("permissions", {}),
    "final_permissions": final_status.get("permissions", {}),
    "samples": samples,
    "review_path": str(review_path),
    "screenshot": screenshot,
    "failures": failures,
    "warnings": warnings,
}
smoke_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
log(f"dogfood-smoke: {payload['status']} evidence={smoke_path}")
if failures:
    for failure in failures:
        log(f"dogfood-smoke: blocked: {failure}")
    raise SystemExit(2)
for warning in warnings:
    log(f"dogfood-smoke: warning: {warning}")
PY

echo "dogfood-smoke: ok"
