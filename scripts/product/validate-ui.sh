#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

runtime_dir="${INTENTOS_RUNTIME_DIR:-.harness/runtime}"
artifact_dir="$runtime_dir/artifacts"
log_dir="$runtime_dir/logs"
mkdir -p "$artifact_dir" "$log_dir"
scripts/harness/runtime-log.py ui validation_start mode=temporary_server

scripts/product/dev.sh > "$log_dir/ui-validate-build.log" 2>&1

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
app_js = fetch("/site/app.js")
activity = json.loads(fetch("/artifacts/activity-summary.json"))
capture = json.loads(fetch("/artifacts/capture-summary.json"))
youtube = json.loads(fetch("/artifacts/youtube-summary.json"))

required_html = ["IntentOS", "data-ui-root", "Behavior reports"]
for text in required_html:
    if text not in html:
        raise AssertionError(f"missing UI text: {text}")

for token in ["data-primary-narrative", "activity-summary.json", "capture-summary.json"]:
    if token not in app_js:
        raise AssertionError(f"missing app binding: {token}")

for name, report in [("activity", activity), ("capture", capture), ("youtube", youtube)]:
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
            f"youtube={validation['youtube_narrative']}",
            f"snapshot={snapshot_output}",
        ]
    )
    + "\n",
    encoding="utf-8",
)
print(output.read_text(encoding="utf-8"), end="")
PY

scripts/harness/runtime-log.py ui validation_completed \
  status=ok artifact_path="$artifact_dir/ui-validation.json"
