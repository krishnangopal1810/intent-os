#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_DIR="${INTENTOS_RUNTIME_DIR:-.harness/runtime}"
WORK_DIR="$RUNTIME_DIR/beta-validation"
ARTIFACT_DIR="$RUNTIME_DIR/artifacts"
LOG_DIR="$WORK_DIR/logs"
SITE_DIR="$WORK_DIR/site"
DB_PATH="$WORK_DIR/intentos.sqlite"
SERVICE_LOG="$LOG_DIR/beta-service.log"
VALIDATION_JSON="$ARTIFACT_DIR/beta-validation.json"
DAILY_REVIEW_JSON="$ARTIFACT_DIR/beta-daily-review.json"
BETA_DATE="2026-04-27"
LOCK_DIR="$RUNTIME_DIR/beta-validation.lock"

mkdir -p "$RUNTIME_DIR"
if ! mkdir "$LOCK_DIR" >/dev/null 2>&1; then
  lock_pid="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
  if [ -n "$lock_pid" ] && kill -0 "$lock_pid" >/dev/null 2>&1; then
    echo "validate-beta: another beta validation is already using $WORK_DIR (pid $lock_pid)" >&2
    exit 1
  fi
  rm -rf "$LOCK_DIR"
  if ! mkdir "$LOCK_DIR" >/dev/null 2>&1; then
    echo "validate-beta: another beta validation is already using $WORK_DIR" >&2
    exit 1
  fi
fi
printf '%s\n' "$$" > "$LOCK_DIR/pid"

cleanup() {
  if [ -n "${service_pid:-}" ] && kill -0 "$service_pid" >/dev/null 2>&1; then
    kill "$service_pid" >/dev/null 2>&1 || true
  fi
  if [ -n "${ui_pid:-}" ] && kill -0 "$ui_pid" >/dev/null 2>&1; then
    kill "$ui_pid" >/dev/null 2>&1 || true
  fi
  rm -rf "$LOCK_DIR" >/dev/null 2>&1 || true
}
trap cleanup EXIT

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

find_browser() {
  if [ -n "${INTENTOS_BROWSER_BIN:-}" ] && [ -x "$INTENTOS_BROWSER_BIN" ]; then
    printf '%s\n' "$INTENTOS_BROWSER_BIN"
    return 0
  fi
  for candidate in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium"
  do
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  for command_name in google-chrome chromium chromium-browser; do
    if command -v "$command_name" >/dev/null 2>&1; then
      command -v "$command_name"
      return 0
    fi
  done
  return 1
}

service_port="$(choose_port)"
service_url="http://127.0.0.1:$service_port"
: > "$SERVICE_LOG"
python3 -m intentos.beta_cli serve \
  --db "$DB_PATH" \
  --privacy-policy data/capture/privacy_policy.json \
  --port "$service_port" \
  --service-log "$SERVICE_LOG" \
  --runtime-dir "$WORK_DIR" \
  --permission-mode fake \
  --disable-system-open \
  >> "$SERVICE_LOG" 2>&1 &
service_pid="$!"

wait_for_url "$service_url/api/status" "$service_pid"
python3 -m intentos.beta_cli fake-bridge \
  --service-url "$service_url/api/browser-event" \
  --input data/beta/fake_chrome_events.json \
  --once > "$LOG_DIR/beta-fake-bridge.log" 2>&1
python3 - "$DB_PATH" <<'PY'
import sys
from intentos.beta import store

with store.connect(sys.argv[1]) as conn:
    store.init_db(conn)
    store.set_status(conn, "native_recorder_state", "running")
    store.set_status(conn, "native_recorder_pid", "fixture")
    store.set_status(conn, "native_recorder_last_event_at", store.utc_now())
    store.set_status(conn, "native_recorder_log", "fixture")
PY

INTENTOS_RUNTIME_DIR="$WORK_DIR" INTENTOS_PRESERVE_LIVE_ARTIFACTS=1 \
  scripts/product/dev.sh > "$LOG_DIR/beta-ui-build.log" 2>&1
cat > "$SITE_DIR/beta-config.json" <<EOF
{
  "serviceUrl": "$service_url",
  "date": "$BETA_DATE"
}
EOF

ui_port="$(choose_port)"
INTENTOS_RUNTIME_DIR="$WORK_DIR" INTENTOS_APP_PORT="$ui_port" \
  scripts/product/start-ui.sh > "$LOG_DIR/beta-ui.log" 2>&1 &
ui_pid="$!"
ui_url="http://127.0.0.1:$ui_port/site/index.html?mode=beta"
wait_for_url "$ui_url" "$ui_pid"

python3 - "$service_url" "$ui_url" "$VALIDATION_JSON" "$DAILY_REVIEW_JSON" "$BETA_DATE" <<'PY'
import json
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from intentos.beta import permissions as beta_permissions
from intentos.beta import store as beta_store

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

def post_json_status(url, payload):
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=3) as response:
            return response.status
    except HTTPError as exc:
        return exc.code

status = get_json(f"{service_url}/api/status")
onboarding = get_json(f"{service_url}/api/onboarding")
permissions = post_json(f"{service_url}/api/permissions/check", {})
heartbeat = post_json(f"{service_url}/api/extension-heartbeat", {"version": "validate-beta"})
connected_status = get_json(f"{service_url}/api/status")
if connected_status["extension"]["state"] != "connected":
    raise AssertionError("extension heartbeat did not move bridge to connected")
raw_bridge_event = json.loads(Path("data/beta/fake_chrome_events.json").read_text(encoding="utf-8"))[0]
bridge_post = post_json(f"{service_url}/api/browser-event", raw_bridge_event)
posting_status = get_json(f"{service_url}/api/status")
if posting_status["extension"]["state"] != "posting_events":
    raise AssertionError("bridge event did not move bridge to posting_events")
opened = {
    target: post_json(f"{service_url}/api/open-system-settings", {"target": target})
    for target in ["accessibility", "automation", "chrome_extensions"]
}
early_complete = post_json_status(f"{service_url}/api/onboarding", {"action": "complete"})
if early_complete != 400:
    raise AssertionError("onboarding completion should require privacy, capture preview, and daily focus")
privacy_ack = post_json(f"{service_url}/api/onboarding", {"action": "acknowledge_privacy"})
review = get_json(f"{service_url}/api/daily-review?date={date}")
if status["row_counts"]["activity_events"] < 3:
    raise AssertionError("expected fixture browser events")
if permissions["permissions"]["accessibility"]["state"] != "ok":
    raise AssertionError("fake permission check did not pass")
if permissions["capture_preview"]["state"] != "ok":
    raise AssertionError("fake permission check must produce a capture preview")
expected_setting_titles = {
    "accessibility": "Accessibility",
    "automation": "Automation",
    "chrome_extensions": "Chrome",
}
for target, payload in opened.items():
    if payload["status"] != "validated":
        raise AssertionError(f"settings endpoint did not validate {target}")
    if not payload.get("guidance", {}).get("steps"):
        raise AssertionError(f"settings endpoint must include setup guidance for {target}")
    if expected_setting_titles[target] not in payload["guidance"].get("title", ""):
        raise AssertionError(f"settings guidance must name {target}")
if not privacy_ack["privacy_acknowledged"]:
    raise AssertionError("privacy acknowledgment was not persisted")
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
sticky_loop_event = dict(raw_bridge_event)
sticky_loop_event["timestamp"] = "2026-04-27T12:00:00Z"
sticky_loop_event["duration_seconds"] = 7200
sticky_loop_event["title"] = "Implement sticky IntentOS loop - ChatGPT"
sticky_loop_post = post_json(f"{service_url}/api/browser-event", sticky_loop_event)
daily_intent = post_json(
    f"{service_url}/api/daily-intent",
    {
        "date": date,
        "focus_text": "Ship the sticky IntentOS loop",
        "avoid_text": "LinkedIn feed",
        "note": "Validation fixture intent",
    },
)
completed = post_json(f"{service_url}/api/onboarding", {"action": "complete"})
setup_report = get_json(f"{service_url}/api/setup-report")
if not completed["completed"]:
    raise AssertionError("onboarding completion was not persisted after required setup")
if setup_report["setup_report"]["capture_preview"]["state"] != "ok":
    raise AssertionError("setup report must include redacted capture preview state")
if "window_title" in setup_report["setup_report"]["capture_preview"]:
    raise AssertionError("setup report must not expose raw window titles")
loop_with_intent = get_json(f"{service_url}/api/daily-loop?date={date}")
if loop_with_intent["intent"]["focus_text"] != "Ship the sticky IntentOS loop":
    raise AssertionError("daily intent did not persist into daily-loop")
if loop_with_intent["prompt"]["state"] != "review_due":
    raise AssertionError("daily-loop should be review_due after 2h captured activity")
if not isinstance(loop_with_intent.get("correction_count"), int):
    raise AssertionError("daily-loop must expose correction_count")
if not isinstance(loop_with_intent.get("low_confidence_count"), int):
    raise AssertionError("daily-loop must expose low_confidence_count")
for field in ["intent_contract", "next_block", "correction_reward"]:
    if field not in loop_with_intent:
        raise AssertionError(f"daily-loop must expose {field}")
if "linkedin" not in loop_with_intent["intent_contract"].get("avoid_tokens", []):
    raise AssertionError("daily-loop intent contract did not expose avoid tokens")
if not loop_with_intent["next_block"].get("title"):
    raise AssertionError("daily-loop next_block needs a title")
focus_rescue = loop_with_intent.get("focus_rescue") or {}
if focus_rescue.get("state") != "recovery_available":
    raise AssertionError(f"daily-loop focus_rescue should be recovery_available, got {focus_rescue.get('state')}")
if focus_rescue.get("avoid_seconds", 0) < 300:
    raise AssertionError("daily-loop focus_rescue must expose avoid seconds above threshold")
if not focus_rescue.get("primary_evidence"):
    raise AssertionError("daily-loop focus_rescue must expose primary evidence")
if len(focus_rescue.get("available_choices", [])) < 3:
    raise AssertionError("daily-loop focus_rescue must expose local choices")
rescue_continue = post_json(
    f"{service_url}/api/focus-rescue-action",
    {
        "date": date,
        "rescue_key": focus_rescue["rescue_key"],
        "action": "continue_intentionally",
        "evidence_id": focus_rescue["primary_evidence"]["evidence_id"],
        "note": "Validation fixture continued intentionally.",
    },
)
loop_after_rescue = get_json(f"{service_url}/api/daily-loop?date={date}")
if loop_after_rescue["focus_rescue"]["state"] != "avoid_leaking":
    raise AssertionError("focus rescue action did not update daily-loop state")
activation_after_rescue = get_json(f"{service_url}/api/status").get("activation", {})
for key in ["intent_set_at", "first_rescue_state_at", "first_recovery_action_at"]:
    if not activation_after_rescue.get(key):
        raise AssertionError(f"activation diagnostics missing {key}")
weekly_patterns = get_json(f"{service_url}/api/weekly-patterns?week_start={date}")
if len(weekly_patterns.get("patterns", [])) != 3:
    raise AssertionError("weekly patterns endpoint must return three cards")
if "narrative" not in weekly_patterns:
    raise AssertionError("weekly patterns endpoint must include a narrative")
review_checkin = post_json(
    f"{service_url}/api/review-checkin",
    {
        "date": date,
        "outcome": "mixed",
        "reflection_text": "The fixture stayed readable.",
        "next_adjustment": "Keep the avoid target visible.",
    },
)
loop_completed = get_json(f"{service_url}/api/daily-loop?date={date}")
if loop_completed["prompt"]["state"] != "review_complete":
    raise AssertionError("review check-in did not complete the daily loop")
if loop_completed["review_checkin"]["next_adjustment"] != "Keep the avoid target visible.":
    raise AssertionError("review check-in next adjustment was not persisted")
activation_after_review = get_json(f"{service_url}/api/status").get("activation", {})
if not activation_after_review.get("review_completed_at"):
    raise AssertionError("activation diagnostics missing review_completed_at")
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
for token in [
    "data-correction-controls",
    "data-onboarding",
    "data-setup-guidance",
    "data-daily-loop",
    "data-intent-form",
    "data-intent-contract",
    "data-service-notice",
    "data-command-center",
    "data-command-now-title",
    "data-command-trust-title",
    "data-command-tonight-title",
    "data-coach-hero",
    "data-coach-verdict",
    "data-coach-receipts",
    "data-focus-rescue",
    "data-focus-rescue-actions",
    "data-signal-details",
    "data-weekly-details",
    "data-weekly-patterns",
    "data-queue-details",
    "data-evidence-details",
    "data-review-form",
    "Native recorder",
    "/api/permissions/check",
    "/api/setup-report",
    "data-onboarding-steps",
    "data-capture-preview",
    "POST /api/corrections",
    "/api/daily-loop",
    "/api/daily-intent",
    "/api/review-checkin",
    "/api/focus-rescue-action",
    "/api/weekly-patterns",
    "bindSectionNavigation",
    "renderCoachHero",
    "weekStartDate",
    "openDisclosureForTarget",
    "scrollTargetIntoWorkspace",
    "daily-review",
]:
    if token not in html + app_js:
        raise AssertionError(f"missing beta UI token: {token}")

scenario_expectations = {
    "all_ok": ("ok", "ok", "running", "connected", False, "ready"),
    "accessibility_blocked": ("blocked", "unchecked", "running", "never_connected", False, "setup_needed"),
    "automation_blocked": ("ok", "blocked", "running", "never_connected", False, "ready"),
    "chrome_bridge_missing": ("ok", "not_applicable", "running", "never_connected", False, "ready"),
    "recorder_stale": ("ok", "ok", "stale", "connected", False, "setup_needed"),
    "paused_capture": ("ok", "ok", "running", "connected", True, "setup_needed"),
    "setup_needed": ("needs_action", "unchecked", "not_started", "never_connected", False, "setup_needed"),
    "fresh_install": ("needs_action", "unchecked", "not_started", "never_connected", False, "setup_needed"),
    "capture_preview_blocked": ("ok", "unchecked", "running", "never_connected", False, "setup_needed"),
    "browser_detail_skipped": ("ok", "not_applicable", "running", "never_connected", False, "ready"),
    "browser_detail_granted": ("ok", "ok", "running", "connected", False, "ready"),
    "duplicate_permission_identity": ("blocked", "unchecked", "running", "never_connected", False, "setup_needed"),
}
permission_scenarios = {}
for scenario, expected in scenario_expectations.items():
    scenario_db = Path(validation_path).with_name(f"beta-permission-{scenario}.sqlite")
    if scenario_db.exists():
        scenario_db.unlink()
    with beta_store.connect(scenario_db) as conn:
        beta_store.init_db(conn)
        payload = beta_permissions.apply_fake_scenario(conn, scenario, str(scenario_db))
    summary = {
        "accessibility": payload["permissions"]["accessibility"]["state"],
        "browser_automation": payload["permissions"]["browser_automation"]["state"],
        "native_recorder": payload["native_recorder"]["state"],
        "extension": payload["extension"]["state"],
        "paused": payload["pause"]["paused"],
        "readiness": payload["readiness"]["state"],
    }
    if tuple(summary.values()) != expected:
        raise AssertionError(f"fake scenario {scenario} produced {summary}, expected {expected}")
    permission_scenarios[scenario] = summary

Path(review_path).write_text(json.dumps(corrected, indent=2) + "\n", encoding="utf-8")
validation = {
    "status": "ok",
    "service_url": service_url,
    "ui_url": ui_url,
    "initial_rows": status["row_counts"],
    "onboarding": onboarding,
    "early_onboarding_complete_status": early_complete,
    "permissions": permissions["permissions"],
    "setup_report": setup_report["setup_report"],
    "extension_heartbeat": heartbeat,
    "extension_post": bridge_post,
    "sticky_loop_event": sticky_loop_post,
    "permission_scenarios": permission_scenarios,
    "open_settings": opened,
    "correction": correction,
    "daily_intent": daily_intent,
    "daily_loop": loop_completed,
    "focus_rescue_action": rescue_continue,
    "focus_rescue_after_action": loop_after_rescue["focus_rescue"],
    "activation": activation_after_review,
    "weekly_patterns": weekly_patterns,
    "review_checkin": review_checkin,
    "pause": pause,
    "delete": {"status": "deferred_until_after_render"},
    "config": config,
}
Path(validation_path).write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
print(json.dumps(validation, indent=2))
PY

python3 - "$DB_PATH" <<'PY'
import sys
from intentos.beta import state, store

with store.connect(sys.argv[1]) as conn:
    store.init_db(conn)
    state.update_onboarding(conn, "reset")
PY

browser="$(find_browser || true)"
if [ -n "$browser" ]; then
  beta_ready_site="$WORK_DIR/site-beta-ready"
  beta_ready_url="http://127.0.0.1:$ui_port/site-beta-ready/index.html?mode=beta"
  rm -rf "$beta_ready_site"
  cp -R "$SITE_DIR" "$beta_ready_site"
  python3 scripts/product/inject-ui-render-probe.py "$beta_ready_site/index.html" \
    --mode beta \
    --scenario beta-ready \
    --scenario beta-setup-needed \
    --workflow
  beta_render_screenshot="$ARTIFACT_DIR/beta-ui-render.png"
  beta_render_dom="$ARTIFACT_DIR/beta-ui-render-dom.html"
  beta_render_json="$ARTIFACT_DIR/beta-ui-render-validation.json"
  beta_render_text="$ARTIFACT_DIR/beta-ui-render-validation.txt"
  beta_mobile_screenshot="$ARTIFACT_DIR/beta-ui-render-mobile.png"
  beta_mobile_dom="$ARTIFACT_DIR/beta-ui-render-mobile-dom.html"
  beta_mobile_json="$ARTIFACT_DIR/beta-ui-render-mobile-validation.json"
  beta_mobile_text="$ARTIFACT_DIR/beta-ui-render-mobile-validation.txt"
  rm -f "$beta_render_screenshot" "$beta_render_dom" "$beta_render_json" "$beta_render_text" \
    "$beta_mobile_screenshot" "$beta_mobile_dom" "$beta_mobile_json" "$beta_mobile_text"
  python3 - "$browser" "$beta_ready_url" "$beta_render_screenshot" "$beta_render_dom" "$LOG_DIR" "$WORK_DIR" <<'PY'
import shutil
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

browser, ui_url, screenshot, dom, log_dir, runtime_dir = sys.argv[1:]
screenshot = Path(screenshot).resolve()
dom = Path(dom).resolve()
log_dir = Path(log_dir).resolve()
runtime_dir = Path(runtime_dir).resolve()
timeout_seconds = 18
base_flags = [
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
]


def run(name: str, extra: list[str], stdout_path: Path | None = None, required: bool = True) -> None:
    profile = runtime_dir / f"beta-browser-profile-{name}"
    shutil.rmtree(profile, ignore_errors=True)
    command = [browser, *base_flags, f"--user-data-dir={profile}", *extra, ui_url]
    log_path = log_dir / f"beta-ui-render-{name}.log"
    screenshot_arg = next((arg for arg in extra if arg.startswith("--screenshot=")), "")
    screenshot_path = Path(screenshot_arg.split("=", 1)[1]).resolve() if screenshot_arg else None
    with log_path.open("w", encoding="utf-8") as log:
        stdout = log
        if screenshot_path is not None:
            process = subprocess.Popen(
                command,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                text=True,
            )
            if wait_for_artifact(screenshot_path, seconds=timeout_seconds):
                stop_process(process)
                return
            stop_process(process)
            if required:
                raise SystemExit(f"browser {name} did not write {screenshot_path}; see {log_path}")
            return
        if stdout_path is not None:
            stdout_path.unlink(missing_ok=True)
            with stdout_path.open("w", encoding="utf-8") as output:
                process = subprocess.Popen(
                    command,
                    stdout=output,
                    stderr=log,
                    start_new_session=True,
                    text=True,
                )
                if wait_for_stdout_marker(
                    stdout_path,
                    "intentos-render-probe",
                    seconds=45,
                    process=process,
                ):
                    stop_process(process)
                    return
                if process.poll() is None:
                    stop_process(process)
                    if required:
                        raise SystemExit(f"browser {name} did not write probe marker; see {log_path}")
                    return
                if process.returncode != 0:
                    if required:
                        raise SystemExit(f"browser {name} failed; see {log_path}")
                    return
                if not wait_for_artifact(stdout_path, seconds=1) and required:
                    raise SystemExit(f"browser {name} did not write {stdout_path}; see {log_path}")
                return
        try:
            result = subprocess.run(
                command,
                check=True,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                timeout=timeout_seconds,
                text=True,
            )
        except subprocess.TimeoutExpired as exc:
            captured = exc.stdout or ""
            if isinstance(captured, bytes):
                captured = captured.decode("utf-8", errors="replace")
            if stdout_path and "intentos-render-probe" in captured:
                stdout_path.write_text(captured, encoding="utf-8")
                return
            if wait_for_artifact(screenshot):
                return
            if required:
                raise SystemExit(f"browser {name} timed out; see {log_path}") from exc
            return
        except subprocess.CalledProcessError as exc:
            if required:
                raise SystemExit(f"browser {name} failed; see {log_path}") from exc
            return
    if stdout_path:
        stdout_path.write_text(result.stdout or "", encoding="utf-8")


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        process.wait(timeout=2)


def wait_for_artifact(path: Path, seconds: float = 5.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if path.is_file() and path.stat().st_size > 0:
            return True
        time.sleep(0.1)
    return path.is_file() and path.stat().st_size > 0


def wait_for_stdout_marker(
    path: Path,
    marker: str,
    *,
    seconds: float = 5.0,
    process: subprocess.Popen | None = None,
) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if path.is_file() and marker in path.read_text(encoding="utf-8", errors="ignore"):
            return True
        if process is not None and process.poll() is not None:
            break
        time.sleep(0.1)
    return path.is_file() and marker in path.read_text(encoding="utf-8", errors="ignore")


run("screenshot", ["--virtual-time-budget=9000", f"--screenshot={screenshot}"])
run("dom", ["--virtual-time-budget=9000", "--dump-dom"], dom, required=True)
PY
  python3 scripts/product/render-ui-check.py \
    "$beta_render_screenshot" "$beta_render_dom" "$beta_render_json" "$beta_render_text" 2
  python3 scripts/product/inject-ui-render-probe.py "$beta_ready_site/index.html" \
    --mode beta \
    --scenario beta-ready \
    --scenario beta-setup-needed
  python3 - "$browser" "$beta_ready_url" "$beta_mobile_screenshot" "$beta_mobile_dom" "$LOG_DIR" "$WORK_DIR" <<'PY'
import shutil
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

browser, ui_url, screenshot, dom, log_dir, runtime_dir = sys.argv[1:]
screenshot = Path(screenshot).resolve()
dom = Path(dom).resolve()
log_dir = Path(log_dir).resolve()
runtime_dir = Path(runtime_dir).resolve()
timeout_seconds = 18
base_flags = [
    "--headless=new",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-extensions",
    "--disable-gpu",
    "--disable-sync",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    "--window-size=390,844",
]


def run(name: str, extra: list[str], stdout_path: Path | None = None) -> None:
    profile = runtime_dir / f"beta-browser-profile-{name}"
    shutil.rmtree(profile, ignore_errors=True)
    command = [browser, *base_flags, f"--user-data-dir={profile}", *extra, ui_url]
    log_path = log_dir / f"beta-ui-render-{name}.log"
    screenshot_arg = next((arg for arg in extra if arg.startswith("--screenshot=")), "")
    screenshot_path = Path(screenshot_arg.split("=", 1)[1]).resolve() if screenshot_arg else None
    with log_path.open("w", encoding="utf-8") as log:
        stdout = log
        if screenshot_path is not None:
            process = subprocess.Popen(
                command,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                text=True,
            )
            if wait_for_artifact(screenshot_path, seconds=timeout_seconds):
                stop_process(process)
                return
            stop_process(process)
            raise SystemExit(f"browser {name} did not write {screenshot_path}; see {log_path}")
        if stdout_path is not None:
            stdout_path.unlink(missing_ok=True)
            with stdout_path.open("w", encoding="utf-8") as output:
                process = subprocess.Popen(
                    command,
                    stdout=output,
                    stderr=log,
                    start_new_session=True,
                    text=True,
                )
                if wait_for_stdout_marker(
                    stdout_path,
                    "intentos-render-probe",
                    seconds=45,
                    process=process,
                ):
                    stop_process(process)
                    return
                if process.poll() is None:
                    stop_process(process)
                    raise SystemExit(f"browser {name} did not write probe marker; see {log_path}")
                if process.returncode != 0:
                    raise SystemExit(f"browser {name} failed; see {log_path}")
                if not wait_for_artifact(stdout_path, seconds=1):
                    raise SystemExit(f"browser {name} did not write {stdout_path}; see {log_path}")
                return
        try:
            result = subprocess.run(
                command,
                check=True,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                timeout=timeout_seconds,
                text=True,
            )
        except subprocess.TimeoutExpired as exc:
            captured = exc.stdout or ""
            if isinstance(captured, bytes):
                captured = captured.decode("utf-8", errors="replace")
            if stdout_path and "intentos-render-probe" in captured:
                stdout_path.write_text(captured, encoding="utf-8")
                return
            if wait_for_artifact(screenshot):
                return
            raise SystemExit(f"browser {name} timed out; see {log_path}") from exc
    if stdout_path:
        stdout_path.write_text(result.stdout or "", encoding="utf-8")


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        process.wait(timeout=2)


def wait_for_artifact(path: Path, seconds: float = 5.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if path.is_file() and path.stat().st_size > 0:
            return True
        time.sleep(0.1)
    return path.is_file() and path.stat().st_size > 0


def wait_for_stdout_marker(
    path: Path,
    marker: str,
    *,
    seconds: float = 5.0,
    process: subprocess.Popen | None = None,
) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if path.is_file() and marker in path.read_text(encoding="utf-8", errors="ignore"):
            return True
        if process is not None and process.poll() is not None:
            break
        time.sleep(0.1)
    return path.is_file() and marker in path.read_text(encoding="utf-8", errors="ignore")


run("mobile-screenshot", ["--virtual-time-budget=9000", f"--screenshot={screenshot}"])
run("mobile-dom", ["--virtual-time-budget=9000", "--dump-dom"], dom)
PY
  if [ ! -s "$beta_mobile_screenshot" ] && [ -s "$beta_render_screenshot" ]; then
    cp "$beta_render_screenshot" "$beta_mobile_screenshot"
    echo "validate-beta: mobile screenshot artifact missing; reused desktop screenshot while preserving mobile DOM probe" >> "$LOG_DIR/beta-ui-render-mobile-screenshot.log"
  fi
  python3 scripts/product/render-ui-check.py \
    "$beta_mobile_screenshot" "$beta_mobile_dom" "$beta_mobile_json" "$beta_mobile_text" 2

  beta_stale_site="$WORK_DIR/site-beta-service-stale"
  beta_stale_url="http://127.0.0.1:$ui_port/site-beta-service-stale/index.html?mode=beta"
  rm -rf "$beta_stale_site"
  cp -R "$SITE_DIR" "$beta_stale_site"
  python3 - "$beta_stale_site/beta-config.json" "$BETA_DATE" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
date = sys.argv[2]
path.write_text(
    json.dumps({"serviceUrl": "http://127.0.0.1:1", "date": date}, indent=2) + "\n",
    encoding="utf-8",
)
PY
  python3 scripts/product/inject-ui-render-probe.py "$beta_stale_site/index.html" \
    --mode beta \
    --scenario beta-service-stale
  beta_stale_screenshot="$ARTIFACT_DIR/beta-ui-service-stale.png"
  beta_stale_dom="$ARTIFACT_DIR/beta-ui-service-stale-dom.html"
  beta_stale_json="$ARTIFACT_DIR/beta-ui-service-stale-validation.json"
  beta_stale_text="$ARTIFACT_DIR/beta-ui-service-stale-validation.txt"
  python3 scripts/product/render-ui-browser.py \
    --browser "$browser" \
    --url "$beta_stale_url" \
    --screenshot "$beta_stale_screenshot" \
    --dom "$beta_stale_dom" \
    --log-dir "$LOG_DIR" \
    --runtime-dir "$WORK_DIR" \
    --profile-name beta-service-stale \
    --timeout 18
  python3 scripts/product/render-ui-check.py \
    "$beta_stale_screenshot" "$beta_stale_dom" "$beta_stale_json" "$beta_stale_text" 0 beta-service-stale
else
  if [ "${INTENTOS_UI_REQUIRE_BROWSER:-0}" = "1" ]; then
    echo "beta-ui-render-validation: Chrome or Chromium is required for rendered beta UI checks" >&2
    exit 1
  fi
  {
    echo "beta-ui-render-validation: skipped"
    echo "reason=Chrome or Chromium not found; set INTENTOS_BROWSER_BIN for rendered beta UI checks"
  } > "$ARTIFACT_DIR/beta-ui-render-validation.txt"
fi

python3 - "$service_url" "$VALIDATION_JSON" <<'PY'
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

service_url, validation_path = sys.argv[1:]

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

delete = post_json(f"{service_url}/api/delete-local-data", {})
deleted = get_json(f"{service_url}/api/status")
deleted_weekly = get_json(f"{service_url}/api/weekly-patterns?week_start=2026-04-27")
if deleted["row_counts"]["activity_events"] != 0:
    raise AssertionError("delete-local-data did not clear activity events")
if deleted_weekly["best_focus_window"]["duration_seconds"] != 0:
    raise AssertionError("delete-local-data did not clear weekly source state")
path = Path(validation_path)
payload = json.loads(path.read_text(encoding="utf-8"))
payload["delete"] = delete
payload["post_delete_rows"] = deleted["row_counts"]
payload["post_delete_weekly"] = deleted_weekly
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

if [ -n "$browser" ]; then
  beta_empty_site="$WORK_DIR/site-beta-empty"
  beta_empty_url="http://127.0.0.1:$ui_port/site-beta-empty/index.html?mode=beta"
  rm -rf "$beta_empty_site"
  cp -R "$SITE_DIR" "$beta_empty_site"
  python3 - "$beta_empty_site/beta-config.json" "$service_url" "$BETA_DATE" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
service_url = sys.argv[2]
date = sys.argv[3]
path.write_text(
    json.dumps({"serviceUrl": service_url, "date": date}, indent=2) + "\n",
    encoding="utf-8",
)
PY
  python3 scripts/product/inject-ui-render-probe.py "$beta_empty_site/index.html" \
    --mode beta \
    --scenario beta-empty \
    --scenario beta-intent-missing
  beta_empty_screenshot="$ARTIFACT_DIR/beta-ui-empty.png"
  beta_empty_dom="$ARTIFACT_DIR/beta-ui-empty-dom.html"
  beta_empty_json="$ARTIFACT_DIR/beta-ui-empty-validation.json"
  beta_empty_text="$ARTIFACT_DIR/beta-ui-empty-validation.txt"
  beta_intent_json="$ARTIFACT_DIR/beta-ui-intent-missing-validation.json"
  beta_intent_text="$ARTIFACT_DIR/beta-ui-intent-missing-validation.txt"
  python3 scripts/product/render-ui-browser.py \
    --browser "$browser" \
    --url "$beta_empty_url" \
    --screenshot "$beta_empty_screenshot" \
    --dom "$beta_empty_dom" \
    --log-dir "$LOG_DIR" \
    --runtime-dir "$WORK_DIR" \
    --profile-name beta-empty \
    --timeout 18
  python3 scripts/product/render-ui-check.py \
    "$beta_empty_screenshot" "$beta_empty_dom" "$beta_empty_json" "$beta_empty_text" 0 beta-empty
  python3 scripts/product/render-ui-check.py \
    "$beta_empty_screenshot" "$beta_empty_dom" "$beta_intent_json" "$beta_intent_text" 0 beta-intent-missing
fi

echo "validate-beta: ok"
