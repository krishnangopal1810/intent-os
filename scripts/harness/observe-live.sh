#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_DIR="${INTENTOS_RUNTIME_DIR:-.harness/runtime}"
ARTIFACT_DIR="$RUNTIME_DIR/artifacts"
LOG_DIR="$RUNTIME_DIR/logs"
OUTPUT="${INTENTOS_LIVE_CAPTURE_OUTPUT:-$ARTIFACT_DIR/live-capture-events.jsonl}"
SUMMARY_TEXT="$ARTIFACT_DIR/live-capture-summary.txt"
SUMMARY_JSON="$ARTIFACT_DIR/live-capture-summary.json"
DURATION="${INTENTOS_LIVE_CAPTURE_SECONDS:-5}"
LOG_FILE="$LOG_DIR/live-capture.log"

mkdir -p "$ARTIFACT_DIR" "$LOG_DIR"

{
  echo "observe-live: mode=manual_live_sensor"
  echo "observe-live: output=$OUTPUT"
  echo "observe-live: duration_seconds=$DURATION"
  python3 -m intentos.capture_cli capture-macos \
    --duration-seconds "$DURATION" \
    --output "$OUTPUT"
  echo "observe-live: latest event"
  tail -n 5 "$OUTPUT"
  echo "observe-live: replay summary"
  python3 -m intentos.capture_cli replay "$OUTPUT" --allow-empty | tee "$SUMMARY_TEXT"
  python3 -m intentos.capture_cli replay "$OUTPUT" --json --allow-empty > "$SUMMARY_JSON"
  echo "observe-live: wrote $SUMMARY_JSON"
} 2>&1 | tee "$LOG_FILE"
