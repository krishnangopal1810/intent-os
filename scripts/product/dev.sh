#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

runtime_dir="${INTENTOS_RUNTIME_DIR:-.harness/runtime}"
artifact_dir="$runtime_dir/artifacts"
site_dir="$runtime_dir/site"
preserve_live_artifacts="${INTENTOS_PRESERVE_LIVE_ARTIFACTS:-0}"
mkdir -p "$artifact_dir" "$site_dir"
scripts/harness/runtime-log.py product artifact_build_start mode=fixture

if [ "$preserve_live_artifacts" != "1" ]; then
  rm -f \
    "$artifact_dir/live-capture-events.jsonl" \
    "$artifact_dir/live-capture-timeline-events.jsonl" \
    "$artifact_dir/live-capture-summary.txt" \
    "$artifact_dir/live-capture-summary.json" \
    "$artifact_dir/live-session-capture-events.jsonl" \
    "$artifact_dir/live-session-capture-summary.txt" \
    "$artifact_dir/live-session-capture-summary.json"
  echo "product-dev: data_mode=fixture"
  echo "product-dev: cleared live capture artifacts; run make dev-live or make observe-session for macOS data"
else
  echo "product-dev: data_mode=live_preferred"
  echo "product-dev: preserving live capture artifacts for UI preference"
fi

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
"$python_bin" -m intentos.capture_cli normalize-observations data/capture/fake_session_observations.json --merge-adjacent --output "$artifact_dir/session-capture-events.jsonl" > "$artifact_dir/session-capture-normalize.log"
"$python_bin" -m intentos.capture_cli replay "$artifact_dir/session-capture-events.jsonl" > "$artifact_dir/session-capture-summary.txt"
"$python_bin" -m intentos.capture_cli replay "$artifact_dir/session-capture-events.jsonl" --json > "$artifact_dir/session-capture-summary.json"
scripts/harness/runtime-log.py product report_written report=session-capture artifact_path="$artifact_dir/session-capture-summary.json"
cp web/index.html web/styles.css web/app.js "$site_dir/"
rm -f "$site_dir/beta-config.json"
scripts/harness/runtime-log.py product ui_shell_written artifact_path="$site_dir/index.html"

echo "product-dev: wrote $artifact_dir/youtube-summary.txt"
echo "product-dev: wrote $artifact_dir/youtube-summary.json"
echo "product-dev: wrote $artifact_dir/activity-summary.txt"
echo "product-dev: wrote $artifact_dir/activity-summary.json"
echo "product-dev: wrote $artifact_dir/capture-events.jsonl"
echo "product-dev: wrote $artifact_dir/capture-summary.txt"
echo "product-dev: wrote $artifact_dir/capture-summary.json"
echo "product-dev: wrote $artifact_dir/session-capture-events.jsonl"
echo "product-dev: wrote $artifact_dir/session-capture-summary.txt"
echo "product-dev: wrote $artifact_dir/session-capture-summary.json"
echo "product-dev: wrote $site_dir/index.html"
echo "product-dev: latest summary"
cat "$artifact_dir/session-capture-summary.txt"
