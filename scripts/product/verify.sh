#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

python_bin=""
if command -v python3 >/dev/null 2>&1; then
  python_bin="python3"
elif command -v python >/dev/null 2>&1; then
  python_bin="python"
else
  echo "product-verify: Python is required" >&2
  exit 1
fi

echo "+ $python_bin -m unittest discover -s tests"
"$python_bin" -m unittest discover -s tests

echo "+ $python_bin -m intentos.cli data/youtube/sample_watch_history.json"
"$python_bin" -m intentos.cli data/youtube/sample_watch_history.json

echo "+ $python_bin -m intentos.evaluate data/youtube/evaluation_set.json --min-accuracy 90"
"$python_bin" -m intentos.evaluate data/youtube/evaluation_set.json --min-accuracy 90

echo "+ $python_bin -m intentos.activity_cli data/activity/multi_app_events.json"
"$python_bin" -m intentos.activity_cli data/activity/multi_app_events.json

echo "+ $python_bin -m intentos.activity_evaluate data/activity/evaluation_set.json --min-accuracy 85"
"$python_bin" -m intentos.activity_evaluate data/activity/evaluation_set.json --min-accuracy 85

capture_jsonl=".harness/runtime/artifacts/capture-events.jsonl"
mkdir -p "$(dirname "$capture_jsonl")"

echo "+ $python_bin -m intentos.capture_cli normalize-observations data/capture/fake_macos_observations.json --browser-tabs data/capture/fake_browser_tabs.json --output $capture_jsonl"
"$python_bin" -m intentos.capture_cli normalize-observations data/capture/fake_macos_observations.json --browser-tabs data/capture/fake_browser_tabs.json --output "$capture_jsonl"

echo "+ $python_bin -m intentos.capture_cli replay $capture_jsonl"
"$python_bin" -m intentos.capture_cli replay "$capture_jsonl"

session_jsonl=".harness/runtime/artifacts/session-capture-events.jsonl"
echo "+ $python_bin -m intentos.capture_cli normalize-observations data/capture/fake_session_observations.json --merge-adjacent --output $session_jsonl"
"$python_bin" -m intentos.capture_cli normalize-observations data/capture/fake_session_observations.json --merge-adjacent --output "$session_jsonl"

echo "+ $python_bin -m intentos.capture_cli replay $session_jsonl"
"$python_bin" -m intentos.capture_cli replay "$session_jsonl"

echo "+ scripts/harness/adapter-fixture-check.py"
scripts/harness/adapter-fixture-check.py

echo "+ scripts/harness/package-onboarding-check.py"
scripts/harness/package-onboarding-check.py

echo "+ scripts/harness/cohort-evidence-check.py"
scripts/harness/cohort-evidence-check.py

echo "+ scripts/product/validate-beta.sh"
scripts/product/validate-beta.sh

echo "+ scripts/product/validate-ui.sh"
scripts/product/validate-ui.sh
