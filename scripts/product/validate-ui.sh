#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [ -n "${INTENTOS_RUNTIME_DIR:-}" ]; then
  runtime_dir="$INTENTOS_RUNTIME_DIR"
  report_dir="$runtime_dir/artifacts"
else
  runtime_dir="${INTENTOS_UI_VALIDATION_RUNTIME_DIR:-.harness/runtime/ui-validation}"
  report_dir="${INTENTOS_UI_VALIDATION_REPORT_DIR:-.harness/runtime/artifacts}"
fi
artifact_dir="$runtime_dir/artifacts"
log_dir="$runtime_dir/logs"
mkdir -p "$artifact_dir" "$log_dir" "$report_dir"
scripts/harness/runtime-log.py ui validation_start mode=temporary_server

INTENTOS_RUNTIME_DIR="$runtime_dir" \
  scripts/product/dev.sh > "$log_dir/ui-validate-build.log" 2>&1

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

port="$(
  python3 - <<'PY'
import socket
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
)"

INTENTOS_RUNTIME_DIR="$runtime_dir" INTENTOS_APP_PORT="$port" \
  scripts/product/start-ui.sh > "$log_dir/ui-validate-server.log" 2>&1 &
server_pid="$!"

cleanup() {
  if kill -0 "$server_pid" >/dev/null 2>&1; then
    kill "$server_pid" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

python3 - "$port" "$artifact_dir/ui-validation.txt" "$artifact_dir/ui-validation.json" "$artifact_dir/ui-snapshot.html" <<'PY'
import json
import sys
import time
from pathlib import Path
from urllib.request import urlopen

port = sys.argv[1]
output = Path(sys.argv[2])
json_output = Path(sys.argv[3])
snapshot_output = Path(sys.argv[4])
base = f"http://127.0.0.1:{port}"

def fetch(path: str) -> str:
    last_error = None
    for _ in range(30):
        try:
            with urlopen(base + path, timeout=1) as response:
                return response.read().decode("utf-8")
        except Exception as exc:  # pragma: no cover - shell smoke diagnostics
            last_error = exc
            time.sleep(0.1)
    raise RuntimeError(f"failed to fetch {path}: {last_error}")

html = fetch("/site/index.html")
app_js = "\n".join(
    fetch(path)
    for path in [
        "/site/js/state.js",
        "/site/js/api.js",
        "/site/js/navigation.js",
        "/site/js/format.js",
        "/site/js/render-summary.js",
        "/site/js/render-coach.js",
        "/site/js/render-review.js",
        "/site/js/render-daily-loop.js",
        "/site/js/render-beta-queues.js",
        "/site/js/render-onboarding.js",
        "/site/js/boot.js",
    ]
)
activity = json.loads(fetch("/artifacts/activity-summary.json"))
capture = json.loads(fetch("/artifacts/capture-summary.json"))
session_capture = json.loads(fetch("/artifacts/session-capture-summary.json"))
youtube = json.loads(fetch("/artifacts/youtube-summary.json"))

required_html = [
    "IntentOS",
    "data-ui-root",
    "Behavior reports",
    "Recommended",
    "Now",
    "Trust",
    "Tonight",
    "data-command-center",
    "data-command-now-title",
    "data-command-trust-title",
    "data-command-tonight-title",
    "data-signal-details",
    "data-queue-details",
    "data-evidence-details",
    "Next Block",
    "Did the day match your plan?",
    "data-coach-hero",
    "data-weekly-details",
    "Today's shape",
    "Today's Intent",
    "Tonight's review",
    "Reconnect IntentOS",
    "Capture Replay",
]
for text in required_html:
    if text not in html:
        raise AssertionError(f"missing UI text: {text}")

for token in ["youtube-title", ">YouTube<", "data-youtube-narrative"]:
    if token in html:
        raise AssertionError(f"legacy YouTube UI should not be present: {token}")

for token in [
    "data-primary-narrative",
    "activity-summary.json",
    "capture-summary.json",
    "session-capture-summary.json",
    "live-session-capture-summary.json",
    "live-capture-summary.json",
    "data-capture-source",
    "data-action-deck",
    "data-coach-hero",
    "data-weekly-details",
    "data-weekly-patterns",
    "data-next-move-title",
    "data-brief-moments",
    "data-daily-loop",
    "data-intent-form",
    "data-intent-contract",
    "data-service-notice",
    "data-review-form",
    "/api/daily-loop",
    "/api/daily-intent",
    "/api/review-checkin",
    "/api/weekly-patterns",
    "renderCoachHero",
    "weekStartDate",
    "bindSectionNavigation",
    "openDisclosureForTarget",
    "scrollTargetIntoWorkspace",
]:
    if token not in app_js:
        raise AssertionError(f"missing app binding: {token}")

for name, report in [
    ("activity", activity),
    ("capture", capture),
    ("session_capture", session_capture),
    ("youtube", youtube),
]:
    if "summary" not in report:
        raise AssertionError(f"{name} report missing summary")
    if not report["summary"].get("narrative"):
        raise AssertionError(f"{name} report missing narrative")

snapshot_output.write_text(html, encoding="utf-8")
validation = {
    "status": "ok",
    "url": f"{base}/site/index.html",
    "activity_narrative": activity["summary"]["narrative"],
    "capture_items": len(capture.get("items", [])),
    "session_capture_items": len(session_capture.get("items", [])),
    "youtube_narrative": youtube["summary"]["narrative"],
    "snapshot_path": str(snapshot_output),
}
json_output.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
output.write_text(
    "\n".join(
        [
            "ui-validation: ok",
            f"url={validation['url']}",
            f"activity={validation['activity_narrative']}",
            f"capture_items={validation['capture_items']}",
            f"session_capture_items={validation['session_capture_items']}",
            f"youtube={validation['youtube_narrative']}",
            f"snapshot={snapshot_output}",
        ]
    )
    + "\n",
    encoding="utf-8",
)
print(output.read_text(encoding="utf-8"), end="")
PY

browser="$(find_browser || true)"
if [ -n "$browser" ]; then
  python3 scripts/product/inject-ui-render-probe.py "$runtime_dir/site/index.html" \
    --mode fixture \
    --scenario fixture-default \
    --scenario fixture-long-text

  render_screenshot="$artifact_dir/ui-render.png"
  render_dom="$artifact_dir/ui-render-dom.html"
  render_json="$artifact_dir/ui-render-validation.json"
  render_text="$artifact_dir/ui-render-validation.txt"
  viewport="${INTENTOS_UI_RENDER_VIEWPORT:-1440,1000}"
  python3 - "$browser" "$render_screenshot" "$render_dom" \
    "http://127.0.0.1:$port/site/index.html" "$viewport" \
    "$log_dir" "$runtime_dir" <<'PY'
import subprocess
import shutil
import os
import signal
import sys
import time
from pathlib import Path

browser = sys.argv[1]
screenshot = Path(sys.argv[2])
dom = Path(sys.argv[3])
url = sys.argv[4]
viewport = sys.argv[5]
log_dir = Path(sys.argv[6])
runtime_dir = Path(sys.argv[7])

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
    f"--window-size={viewport}",
]

for artifact in [screenshot, dom]:
    artifact.unlink(missing_ok=True)


def run_browser(
    name: str,
    extra: list[str],
    stdout_path: Path | None = None,
    timeout_artifact: Path | None = None,
    required: bool = True,
) -> bool:
    log_path = log_dir / f"ui-render-{name}.log"
    profile_dir = runtime_dir / f"browser-profile-{name}"
    shutil.rmtree(profile_dir, ignore_errors=True)
    command = [
        browser,
        *base_flags,
        f"--user-data-dir={profile_dir}",
        "--virtual-time-budget=9000",
        *extra,
        url,
    ]
    with log_path.open("w", encoding="utf-8") as log:
        stdout = log
        if timeout_artifact is not None:
            process = subprocess.Popen(
                command,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                text=True,
            )
            if wait_for_artifact(timeout_artifact, seconds=25):
                stop_process(process)
                return True
            stop_process(process)
            if not required:
                log.write(f"\nvalidate-ui: optional browser {name} did not write artifact\n")
                return False
            raise SystemExit(f"browser {name} did not write {timeout_artifact}; see {log_path}")
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
                    seconds=25,
                    process=process,
                ):
                    stop_process(process)
                    return True
                if process.poll() is None:
                    stop_process(process)
                    if not required:
                        log.write(f"\nvalidate-ui: optional browser {name} did not write probe marker\n")
                        return False
                    raise SystemExit(f"browser {name} did not write probe marker; see {log_path}")
                if process.returncode != 0:
                    if not required:
                        log.write(f"\nvalidate-ui: optional browser {name} failed\n")
                        return False
                    raise SystemExit(f"browser {name} failed; see {log_path}")
                return wait_for_artifact(stdout_path, seconds=1)
        try:
            result = subprocess.run(
                command,
                check=True,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                timeout=25,
                text=True,
            )
        except subprocess.TimeoutExpired as exc:
            captured = exc.stdout or ""
            if isinstance(captured, bytes):
                captured = captured.decode("utf-8", errors="replace")
            if stdout_path is not None and "intentos-render-probe" in captured:
                stdout_path.write_text(captured, encoding="utf-8")
                log.write(f"\nvalidate-ui: browser {name} timed out after writing stdout\n")
                return True
            if timeout_artifact and timeout_artifact.is_file() and timeout_artifact.stat().st_size > 0:
                log.write(f"\nvalidate-ui: browser {name} timed out after writing artifact\n")
                return True
            if not required:
                log.write(f"\nvalidate-ui: optional browser {name} timed out\n")
                return False
            raise SystemExit(f"browser {name} timed out; see {log_path}") from exc
        except subprocess.CalledProcessError as exc:
            if not required:
                log.write(f"\nvalidate-ui: optional browser {name} failed: {exc}\n")
                return False
            raise SystemExit(f"browser {name} failed; see {log_path}") from exc
    if stdout_path is not None:
        stdout_path.write_text(result.stdout or "", encoding="utf-8")
    return True


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


run_browser("screenshot", [f"--screenshot={screenshot}"], timeout_artifact=screenshot)
if not wait_for_artifact(screenshot):
    raise SystemExit(f"browser screenshot did not produce {screenshot}")
run_browser("dom", ["--dump-dom"], dom, required=False)
PY
  python3 scripts/product/render-ui-check.py \
    "$render_screenshot" "$render_dom" "$render_json" "$render_text"
  mobile_screenshot="$artifact_dir/ui-render-mobile.png"
  mobile_dom="$artifact_dir/ui-render-mobile-dom.html"
  mobile_json="$artifact_dir/ui-render-mobile-validation.json"
  mobile_text="$artifact_dir/ui-render-mobile-validation.txt"
  mobile_viewport="${INTENTOS_UI_RENDER_MOBILE_VIEWPORT:-390,844}"
  python3 - "$browser" "$mobile_screenshot" "$mobile_dom" \
    "http://127.0.0.1:$port/site/index.html" "$mobile_viewport" \
    "$log_dir" "$runtime_dir" <<'PY'
import subprocess
import shutil
import os
import signal
import sys
import time
from pathlib import Path

browser = sys.argv[1]
screenshot = Path(sys.argv[2])
dom = Path(sys.argv[3])
url = sys.argv[4]
viewport = sys.argv[5]
log_dir = Path(sys.argv[6])
runtime_dir = Path(sys.argv[7])

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
    f"--window-size={viewport}",
]

for artifact in [screenshot, dom]:
    artifact.unlink(missing_ok=True)


def run_browser(
    name: str,
    extra: list[str],
    stdout_path: Path | None = None,
    timeout_artifact: Path | None = None,
    required: bool = True,
) -> bool:
    log_path = log_dir / f"ui-render-mobile-{name}.log"
    profile_dir = runtime_dir / f"browser-profile-mobile-{name}"
    shutil.rmtree(profile_dir, ignore_errors=True)
    command = [
        browser,
        *base_flags,
        f"--user-data-dir={profile_dir}",
        "--virtual-time-budget=9000",
        *extra,
        url,
    ]
    with log_path.open("w", encoding="utf-8") as log:
        stdout = log
        if timeout_artifact is not None:
            process = subprocess.Popen(
                command,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                text=True,
            )
            if wait_for_artifact(timeout_artifact, seconds=25):
                stop_process(process)
                return True
            stop_process(process)
            if not required:
                log.write(f"\nvalidate-ui: optional browser {name} did not write artifact\n")
                return False
            raise SystemExit(f"browser {name} did not write {timeout_artifact}; see {log_path}")
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
                    seconds=25,
                    process=process,
                ):
                    stop_process(process)
                    return True
                if process.poll() is None:
                    stop_process(process)
                    if not required:
                        log.write(f"\nvalidate-ui: optional browser {name} did not write probe marker\n")
                        return False
                    raise SystemExit(f"browser {name} did not write probe marker; see {log_path}")
                if process.returncode != 0:
                    if not required:
                        log.write(f"\nvalidate-ui: optional browser {name} failed\n")
                        return False
                    raise SystemExit(f"browser {name} failed; see {log_path}")
                return wait_for_artifact(stdout_path, seconds=1)
        try:
            result = subprocess.run(
                command,
                check=True,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                timeout=25,
                text=True,
            )
        except subprocess.TimeoutExpired as exc:
            captured = exc.stdout or ""
            if isinstance(captured, bytes):
                captured = captured.decode("utf-8", errors="replace")
            if stdout_path is not None and "intentos-render-probe" in captured:
                stdout_path.write_text(captured, encoding="utf-8")
                log.write(f"\nvalidate-ui: browser {name} timed out after writing stdout\n")
                return True
            if timeout_artifact and timeout_artifact.is_file() and timeout_artifact.stat().st_size > 0:
                log.write(f"\nvalidate-ui: browser {name} timed out after writing artifact\n")
                return True
            if not required:
                log.write(f"\nvalidate-ui: optional browser {name} timed out\n")
                return False
            raise SystemExit(f"browser {name} timed out; see {log_path}") from exc
        except subprocess.CalledProcessError as exc:
            if not required:
                log.write(f"\nvalidate-ui: optional browser {name} failed: {exc}\n")
                return False
            raise SystemExit(f"browser {name} failed; see {log_path}") from exc
    if stdout_path is not None:
        stdout_path.write_text(result.stdout or "", encoding="utf-8")
    return True


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


run_browser("screenshot", [f"--screenshot={screenshot}"], timeout_artifact=screenshot)
if not wait_for_artifact(screenshot):
    raise SystemExit(f"browser screenshot did not produce {screenshot}")
run_browser("dom", ["--dump-dom"], dom, required=False)
PY
  python3 scripts/product/render-ui-check.py \
    "$mobile_screenshot" "$mobile_dom" "$mobile_json" "$mobile_text"
else
  if [ "${INTENTOS_UI_REQUIRE_BROWSER:-0}" = "1" ]; then
    echo "ui-render-validation: Chrome or Chromium is required for rendered UI checks" >&2
    exit 1
  fi
  {
    echo "ui-render-validation: skipped"
    echo "reason=Chrome or Chromium not found; set INTENTOS_BROWSER_BIN for rendered UI checks"
  } > "$artifact_dir/ui-render-validation.txt"
fi

scripts/harness/runtime-log.py ui validation_completed \
  status=ok artifact_path="$artifact_dir/ui-validation.json"

scripts/product/check-ui-screenshot.sh

if [ "$artifact_dir" != "$report_dir" ]; then
  for artifact in "$artifact_dir"/ui-*; do
    [ -e "$artifact" ] || continue
    cp "$artifact" "$report_dir/"
  done
fi
