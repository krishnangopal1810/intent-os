#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

LOG_FILE=".harness/runtime/logs/app.log"
LIVE_CAPTURE_LOG=".harness/runtime/logs/live-capture.log"
EVENT_LOG=".harness/runtime/logs/events.jsonl"

if [ ! -f "$LOG_FILE" ]; then
  echo "observe: no app log found at $LOG_FILE" >&2
  echo "observe: run make dev after product runtime exists" >&2
  exit 2
fi

if [ -f "$EVENT_LOG" ]; then
  echo "observe: recent structured events"
  tail -n 40 "$EVENT_LOG"
  echo
fi

echo "observe: recent app log"
tail -n 120 "$LOG_FILE"

if [ -f "$LIVE_CAPTURE_LOG" ]; then
  echo
  echo "observe: recent live capture log"
  tail -n 120 "$LIVE_CAPTURE_LOG"
fi
