#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RUNTIME_DIR="${INTENTOS_RUNTIME_DIR:-.harness/runtime}"
ARTIFACT_DIR="$RUNTIME_DIR/artifacts"
LOG_DIR="$RUNTIME_DIR/logs"
OUTPUT="${INTENTOS_LIVE_SESSION_OUTPUT:-$ARTIFACT_DIR/live-session-capture-events.jsonl}"
SUMMARY_TEXT="$ARTIFACT_DIR/live-session-capture-summary.txt"
SUMMARY_JSON="$ARTIFACT_DIR/live-session-capture-summary.json"
DURATION="${INTENTOS_LIVE_SESSION_SECONDS:-30}"
INTERVAL="${INTENTOS_LIVE_SESSION_INTERVAL_SECONDS:-5}"
LOG_FILE="$LOG_DIR/live-session-capture.log"

mkdir -p "$ARTIFACT_DIR" "$LOG_DIR"

{
  scripts/harness/runtime-log.py capture session_start \
    mode=manual_live_session duration_seconds="$DURATION" interval_seconds="$INTERVAL" \
    artifact_path="$OUTPUT"
  echo "observe-session: mode=manual_live_session"
  echo "observe-session: output=$OUTPUT"
  echo "observe-session: duration_seconds=$DURATION"
  echo "observe-session: interval_seconds=$INTERVAL"
  python3 -m intentos.capture_cli capture-session \
    --duration-seconds "$DURATION" \
    --interval-seconds "$INTERVAL" \
    --output "$OUTPUT"
  echo "observe-session: timeline events"
  tail -n 10 "$OUTPUT"
  echo "observe-session: replay summary"
  python3 -m intentos.capture_cli replay "$OUTPUT" --allow-empty | tee "$SUMMARY_TEXT"
  python3 -m intentos.capture_cli replay "$OUTPUT" --json --allow-empty > "$SUMMARY_JSON"
  scripts/harness/runtime-log.py capture session_completed \
    mode=manual_live_session artifact_path="$SUMMARY_JSON" status=ok
  echo "observe-session: wrote $SUMMARY_JSON"
} 2>&1 | tee "$LOG_FILE"
