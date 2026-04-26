#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PID_FILE=".harness/runtime/app.pid"

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
