#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

LOG_FILE=".harness/runtime/logs/app.log"

if [ ! -f "$LOG_FILE" ]; then
  echo "observe: no app log found at $LOG_FILE" >&2
  echo "observe: run make dev after product runtime exists" >&2
  exit 2
fi

echo "observe: recent app log"
tail -n 120 "$LOG_FILE"
