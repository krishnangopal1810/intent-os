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
onboarding = get_json(f"{service_url}/api/onboarding")
permissions = post_json(f"{service_url}/api/permissions/check", {})
opened = post_json(f"{service_url}/api/open-system-settings", {"target": "accessibility"})
completed = post_json(f"{service_url}/api/onboarding", {"action": "complete"})
review = get_json(f"{service_url}/api/daily-review?date={date}")
if status["row_counts"]["activity_events"] < 3:
    raise AssertionError("expected fixture browser events")
if permissions["permissions"]["accessibility"]["state"] != "ok":
    raise AssertionError("fake permission check did not pass")
if opened["status"] != "validated":
    raise AssertionError("settings endpoint did not validate target")
if not completed["completed"]:
    raise AssertionError("onboarding completion was not persisted")
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
for token in [
    "data-correction-controls",
    "data-onboarding",
    "Native recorder",
    "/api/permissions/check",
    "POST /api/corrections",
    "daily-review",
]:
    if token not in html + app_js:
        raise AssertionError(f"missing beta UI token: {token}")
Path(review_path).write_text(json.dumps(corrected, indent=2) + "\n", encoding="utf-8")
validation = {
    "status": "ok",
    "service_url": service_url,
    "ui_url": ui_url,
    "initial_rows": status["row_counts"],
    "onboarding": onboarding,
    "permissions": permissions["permissions"],
    "open_settings": opened,
    "correction": correction,
    "pause": pause,
    "delete": {"status": "deferred_until_after_render"},
    "config": config,
}
Path(validation_path).write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
print(json.dumps(validation, indent=2))
PY

browser="$(find_browser || true)"
if [ -n "$browser" ]; then
  python3 - "$SITE_DIR/index.html" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
html = path.read_text(encoding="utf-8")
probe = """
    <script>
      (function () {
        function writeProbe() {
          const root = document.querySelector("[data-ui-root]");
          const body = document.body;
          const state = {
            root_present: Boolean(root),
            body_text_length: body.innerText.trim().length,
            panel_count: document.querySelectorAll(".panel").length,
            stat_count: document.querySelectorAll(".stat").length,
            event_count: document.querySelectorAll("[data-capture-events] li").length,
            onboarding_visible:
              document.querySelector("[data-onboarding]")?.hidden === false,
            correction_controls:
              document.querySelectorAll(".event-correction").length,
            horizontal_overflow:
              document.documentElement.scrollWidth >
              document.documentElement.clientWidth + 1,
            out_of_view_count: Array.from(document.querySelectorAll("body *"))
              .filter((element) => {
                const text = element.textContent.trim();
                if (!text || element.offsetParent === null) {
                  return false;
                }
                const rect = element.getBoundingClientRect();
                return rect.left < -1 || rect.right > window.innerWidth + 1;
              }).length,
            clipped_text_count: Array.from(document.querySelectorAll("body *"))
              .filter((element) => {
                const text = element.textContent.trim();
                if (!text || element.children.length > 0) {
                  return false;
                }
                const style = window.getComputedStyle(element);
                return ["hidden", "clip"].includes(style.overflowX) &&
                  element.scrollWidth > element.clientWidth + 1;
              }).length,
          };
          let node = document.getElementById("intentos-render-probe");
          if (!node) {
            node = document.createElement("script");
            node.id = "intentos-render-probe";
            node.type = "application/json";
            document.body.appendChild(node);
          }
          node.textContent = JSON.stringify(state);
        }
        window.addEventListener("load", () => {
          window.setTimeout(writeProbe, 700);
          window.setTimeout(writeProbe, 1800);
        });
      })();
    </script>
"""
if "intentos-render-probe" not in html:
    html = html.replace("</body>", probe + "\n  </body>")
path.write_text(html, encoding="utf-8")
PY
  beta_render_screenshot="$ARTIFACT_DIR/beta-ui-render.png"
  beta_render_dom="$ARTIFACT_DIR/beta-ui-render-dom.html"
  beta_render_json="$ARTIFACT_DIR/beta-ui-render-validation.json"
  beta_render_text="$ARTIFACT_DIR/beta-ui-render-validation.txt"
  python3 - "$browser" "$ui_url" "$beta_render_screenshot" "$beta_render_dom" "$LOG_DIR" "$WORK_DIR" <<'PY'
import shutil
import subprocess
import sys
from pathlib import Path

browser, ui_url, screenshot, dom, log_dir, runtime_dir = sys.argv[1:]
screenshot = Path(screenshot)
dom = Path(dom)
log_dir = Path(log_dir)
runtime_dir = Path(runtime_dir)
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
    with log_path.open("w", encoding="utf-8") as log:
        stdout = subprocess.PIPE if stdout_path else log
        try:
            result = subprocess.run(
                command,
                check=True,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                timeout=25,
                text=True,
            )
        except subprocess.TimeoutExpired as exc:
            captured = exc.stdout or ""
            if isinstance(captured, bytes):
                captured = captured.decode("utf-8", errors="replace")
            if stdout_path and "intentos-render-probe" in captured:
                stdout_path.write_text(captured, encoding="utf-8")
                return
            if screenshot.is_file() and screenshot.stat().st_size > 0:
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


run("screenshot", [f"--screenshot={screenshot}"])
run("dom", ["--virtual-time-budget=5000", "--dump-dom"], dom, required=False)
PY
  python3 scripts/product/render-ui-check.py \
    "$beta_render_screenshot" "$beta_render_dom" "$beta_render_json" "$beta_render_text" 2
else
  cat > "$ARTIFACT_DIR/beta-ui-render-validation.txt" <<'EOF'
beta-ui-render-validation: skipped
reason=Chrome or Chromium not found; set INTENTOS_BROWSER_BIN for rendered beta UI checks
EOF
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
if deleted["row_counts"]["activity_events"] != 0:
    raise AssertionError("delete-local-data did not clear activity events")
path = Path(validation_path)
payload = json.loads(path.read_text(encoding="utf-8"))
payload["delete"] = delete
payload["post_delete_rows"] = deleted["row_counts"]
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

echo "validate-beta: ok"
