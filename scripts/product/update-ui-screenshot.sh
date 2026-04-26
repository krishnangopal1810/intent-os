#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_ROOT="${INTENTOS_SCREENSHOT_RUNTIME_DIR:-.harness/runtime/ui-screenshot}"
RUNTIME_DIR="$RUNTIME_ROOT/run-$(date -u +%Y%m%dT%H%M%SZ)-$$"
ARTIFACT_DIR="$RUNTIME_DIR/artifacts"
LOG_DIR="$RUNTIME_DIR/logs"
SCREENSHOT="${INTENTOS_UI_SCREENSHOT:-docs/assets/screenshots/intent-os-ui.png}"
METADATA="${INTENTOS_UI_SCREENSHOT_METADATA:-docs/assets/screenshots/intent-os-ui.json}"
VIEWPORT="${INTENTOS_UI_SCREENSHOT_VIEWPORT:-1440,1000}"

mkdir -p "$ARTIFACT_DIR" "$LOG_DIR" "$(dirname "$SCREENSHOT")"

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
  python3 - "$url" <<'PY'
import sys
import time
from urllib.request import urlopen

url = sys.argv[1]
last_error = None
for _ in range(40):
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

browser="$(find_browser || true)"
if [ -z "$browser" ]; then
  echo "update-ui-screenshot: Chrome or Chromium is required" >&2
  echo "update-ui-screenshot: set INTENTOS_BROWSER_BIN to a compatible browser binary" >&2
  exit 2
fi

INTENTOS_RUNTIME_DIR="$RUNTIME_DIR" scripts/product/dev.sh > "$LOG_DIR/screenshot-build.log" 2>&1

port="$(choose_port)"
url="http://127.0.0.1:$port/site/index.html"
INTENTOS_RUNTIME_DIR="$RUNTIME_DIR" INTENTOS_APP_PORT="$port" \
  scripts/product/start-ui.sh > "$LOG_DIR/screenshot-server.log" 2>&1 &
server_pid="$!"

cleanup() {
  if kill -0 "$server_pid" >/dev/null 2>&1; then
    kill "$server_pid" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

wait_for_url "$url"

runtime_screenshot="$ARTIFACT_DIR/intent-os-ui.png"
python3 - "$browser" "$runtime_screenshot" "$url" "$VIEWPORT" "$LOG_DIR/screenshot-browser.log" "$RUNTIME_DIR/browser-profile" <<'PY'
import subprocess
import sys
from pathlib import Path

browser = sys.argv[1]
screenshot = Path(sys.argv[2])
url = sys.argv[3]
viewport = sys.argv[4]
log_path = Path(sys.argv[5])
profile_dir = sys.argv[6]
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
    f"--user-data-dir={profile_dir}",
    f"--window-size={viewport}",
    f"--screenshot={screenshot}",
    url,
]

with log_path.open("w", encoding="utf-8") as log:
    try:
        subprocess.run(
            command,
            check=True,
            stdout=log,
            stderr=subprocess.STDOUT,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        if not screenshot.is_file() or screenshot.stat().st_size == 0:
            raise
        log.write("\nupdate-ui-screenshot: browser timed out after writing PNG\n")
PY

cp "$runtime_screenshot" "$SCREENSHOT"

python3 - "$SCREENSHOT" "$METADATA" "$url" "$VIEWPORT" "$browser" <<'PY'
import importlib.util
import json
import struct
import sys
from pathlib import Path

screenshot = Path(sys.argv[1])
metadata_path = Path(sys.argv[2])
url = sys.argv[3]
viewport = sys.argv[4]
browser = sys.argv[5]
manifest_path = Path("scripts/product/ui-screenshot-manifest.py")
spec = importlib.util.spec_from_file_location("ui_screenshot_manifest", manifest_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

data = screenshot.read_bytes()
if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 24:
    raise SystemExit(f"{screenshot} is not a valid PNG")
width, height = struct.unpack(">II", data[16:24])
manifest = module.manifest()
metadata = {
    **manifest,
    "path": str(screenshot),
    "source_url": "/site/index.html",
    "viewport": viewport,
    "width": width,
    "height": height,
    "browser": browser,
}
metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
PY

scripts/product/check-ui-screenshot.sh
echo "update-ui-screenshot: wrote $SCREENSHOT"
