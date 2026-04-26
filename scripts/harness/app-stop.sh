#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PID_FILE=".harness/runtime/app.pid"
CAPTURE_PID_FILE=".harness/runtime/capture.pid"

if [ -f "$CAPTURE_PID_FILE" ]; then
  capture_pid="$(cat "$CAPTURE_PID_FILE")"
  if [ -n "$capture_pid" ] && kill -0 "$capture_pid" >/dev/null 2>&1; then
    kill "$capture_pid"
    echo "app-stop: stopped capture pid $capture_pid"
  else
    echo "app-stop: recorded capture process was not running"
  fi
  rm -f "$CAPTURE_PID_FILE"
fi

if [ ! -f "$PID_FILE" ]; then
  echo "app-stop: no app pid recorded"
  exit 0
fi

pid="$(cat "$PID_FILE")"
if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
  kill "$pid"
  echo "app-stop: stopped pid $pid"
else
  echo "app-stop: recorded app process was not running"
fi

rm -f "$PID_FILE"
