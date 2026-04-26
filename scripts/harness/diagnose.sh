#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_DIR=".harness/runtime"
APP_ENV="$RUNTIME_DIR/app.env"
EVENT_LOG="$RUNTIME_DIR/logs/events.jsonl"
APP_LOG="$RUNTIME_DIR/logs/app.log"
LIVE_CAPTURE_LOG="$RUNTIME_DIR/logs/live-capture.log"
UI_VALIDATION="$RUNTIME_DIR/artifacts/ui-validation.txt"

echo "diagnose: runtime state"
scripts/harness/app-status.sh || true

echo
echo "diagnose: recent structured events"
if [ -f "$EVENT_LOG" ]; then
  tail -n 40 "$EVENT_LOG"
else
  echo "diagnose: no structured events found at $EVENT_LOG"
fi

echo
echo "diagnose: UI validation"
if [ -f "$UI_VALIDATION" ]; then
  cat "$UI_VALIDATION"
else
  echo "diagnose: no UI validation artifact found at $UI_VALIDATION"
fi

echo
echo "diagnose: recent live capture log"
if [ -f "$LIVE_CAPTURE_LOG" ]; then
  tail -n 80 "$LIVE_CAPTURE_LOG"
else
  echo "diagnose: no live capture log found at $LIVE_CAPTURE_LOG"
fi

echo
echo "diagnose: recent app log"
if [ -f "$APP_LOG" ]; then
  tail -n 80 "$APP_LOG"
else
  echo "diagnose: no app log found at $APP_LOG"
fi
