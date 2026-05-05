#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

ARTIFACT_DIR=".harness/runtime/artifacts"
SOURCE_APP="$ARTIFACT_DIR/IntentOS.app"
LEGACY_SOURCE_APP="$ARTIFACT_DIR/IntentOSBeta.app"
INSTALL_DIR="${INTENTOS_BETA_INSTALL_DIR:-$HOME/Applications}"
INSTALLED_APP="$INSTALL_DIR/IntentOS.app"
INSTALL_JSON="$ARTIFACT_DIR/beta-install.json"

mkdir -p "$ARTIFACT_DIR"

if [ "$(uname -s)" != "Darwin" ]; then
  python3 - "$INSTALL_JSON" <<'PY'
import json
import sys
from pathlib import Path

payload = {
    "status": "skipped",
    "reason": "macOS is required to install and open the beta menu bar app",
}
Path(sys.argv[1]).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print("install-beta-app: skipped - macOS is required")
PY
  exit 0
fi

if [ ! -d "$SOURCE_APP" ] && [ -d "$LEGACY_SOURCE_APP" ]; then
  SOURCE_APP="$LEGACY_SOURCE_APP"
fi

if [ ! -d "$SOURCE_APP" ]; then
  scripts/product/package-beta.sh
fi

if [ ! -d "$SOURCE_APP" ]; then
  echo "install-beta-app: missing app bundle at $SOURCE_APP" >&2
  exit 2
fi

if pgrep -x IntentOSBeta >/dev/null 2>&1; then
  pkill -x IntentOSBeta >/dev/null 2>&1 || true
  sleep 1
fi

mkdir -p "$INSTALL_DIR"
rm -rf "$INSTALLED_APP"
rm -rf "$INSTALL_DIR/IntentOSBeta.app"
if command -v ditto >/dev/null 2>&1; then
  ditto "$SOURCE_APP" "$INSTALLED_APP"
else
  cp -R "$SOURCE_APP" "$INSTALLED_APP"
fi

opened=false
if [ "${INTENTOS_SKIP_OPEN:-0}" != "1" ]; then
  open "$INSTALLED_APP"
  opened=true
fi

python3 - "$INSTALL_JSON" "$INSTALLED_APP" "$opened" <<'PY'
import json
import sys
from pathlib import Path

payload = {
    "status": "installed",
    "app_bundle": sys.argv[2],
    "opened": sys.argv[3] == "true",
}
Path(sys.argv[1]).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"install-beta-app: installed {sys.argv[2]} opened={payload['opened']}")
PY
