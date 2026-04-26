#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "dev-live: capturing a fresh bounded macOS metadata session"
echo "dev-live: set INTENTOS_LIVE_SESSION_SECONDS and INTENTOS_LIVE_SESSION_INTERVAL_SECONDS to tune the capture window"

scripts/harness/app-stop.sh >/dev/null 2>&1 || true
INTENTOS_RUNTIME_DIR=".harness/runtime" scripts/harness/observe-session.sh

echo "dev-live: starting UI with live session artifacts preserved"
INTENTOS_DEV_DATA_MODE="live_session" \
  INTENTOS_PRESERVE_LIVE_ARTIFACTS=1 \
  scripts/harness/dev.sh
