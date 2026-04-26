#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

runtime_dir="${INTENTOS_RUNTIME_DIR:-.harness/runtime}"
artifact_dir="$runtime_dir/artifacts"
site_dir="$runtime_dir/site"
mkdir -p "$artifact_dir" "$site_dir"
scripts/harness/runtime-log.py product artifact_build_start mode=fixture

python_bin=""
if command -v python3 >/dev/null 2>&1; then
  python_bin="python3"
elif command -v python >/dev/null 2>&1; then
  python_bin="python"
else
  echo "product-dev: Python is required" >&2
  exit 1
fi

"$python_bin" -m intentos.cli data/youtube/sample_watch_history.json > "$artifact_dir/youtube-summary.txt"
"$python_bin" -m intentos.cli data/youtube/sample_watch_history.json --json > "$artifact_dir/youtube-summary.json"
scripts/harness/runtime-log.py product report_written report=youtube artifact_path="$artifact_dir/youtube-summary.json"
"$python_bin" -m intentos.activity_cli data/activity/multi_app_events.json > "$artifact_dir/activity-summary.txt"
"$python_bin" -m intentos.activity_cli data/activity/multi_app_events.json --json > "$artifact_dir/activity-summary.json"
scripts/harness/runtime-log.py product report_written report=activity artifact_path="$artifact_dir/activity-summary.json"
"$python_bin" -m intentos.capture_cli normalize-observations data/capture/fake_macos_observations.json --browser-tabs data/capture/fake_browser_tabs.json --output "$artifact_dir/capture-events.jsonl" > "$artifact_dir/capture-normalize.log"
"$python_bin" -m intentos.capture_cli replay "$artifact_dir/capture-events.jsonl" > "$artifact_dir/capture-summary.txt"
"$python_bin" -m intentos.capture_cli replay "$artifact_dir/capture-events.jsonl" --json > "$artifact_dir/capture-summary.json"
scripts/harness/runtime-log.py product report_written report=capture artifact_path="$artifact_dir/capture-summary.json"
cp web/index.html web/styles.css web/app.js "$site_dir/"
scripts/harness/runtime-log.py product ui_shell_written artifact_path="$site_dir/index.html"

echo "product-dev: wrote $artifact_dir/youtube-summary.txt"
echo "product-dev: wrote $artifact_dir/youtube-summary.json"
echo "product-dev: wrote $artifact_dir/activity-summary.txt"
echo "product-dev: wrote $artifact_dir/activity-summary.json"
echo "product-dev: wrote $artifact_dir/capture-events.jsonl"
echo "product-dev: wrote $artifact_dir/capture-summary.txt"
echo "product-dev: wrote $artifact_dir/capture-summary.json"
echo "product-dev: wrote $site_dir/index.html"
echo "product-dev: latest summary"
cat "$artifact_dir/capture-summary.txt"
