#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

ARTIFACT_DIR=".harness/runtime/artifacts"
APP_BUNDLE="$ARTIFACT_DIR/IntentOSBeta.app"
EXECUTABLE="$APP_BUNDLE/Contents/MacOS/IntentOSBeta"
PACKAGE_JSON="$ARTIFACT_DIR/beta-package.json"
mkdir -p "$ARTIFACT_DIR"
MODULE_CACHE="$ARTIFACT_DIR/swift-module-cache"

if [ "$(uname -s)" != "Darwin" ] || ! command -v swiftc >/dev/null 2>&1; then
  python3 - "$PACKAGE_JSON" <<'PY'
import json
import sys
from pathlib import Path

payload = {
    "status": "skipped",
    "reason": "macOS swiftc is required to build the beta menu bar app",
}
Path(sys.argv[1]).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print("package-beta: skipped - macOS swiftc is required")
PY
  exit 0
fi

rm -rf "$APP_BUNDLE"
mkdir -p "$APP_BUNDLE/Contents/MacOS" "$APP_BUNDLE/Contents/Resources" "$MODULE_CACHE"
swiftc macos/IntentOSBeta/IntentOSBeta.swift \
  -o "$EXECUTABLE" \
  -parse-as-library \
  -module-cache-path "$MODULE_CACHE" \
  -framework Cocoa
cp macos/IntentOSBeta/Info.plist "$APP_BUNDLE/Contents/Info.plist"

python3 - "$PACKAGE_JSON" "$APP_BUNDLE" <<'PY'
import json
import sys
from pathlib import Path

payload = {
    "status": "built",
    "app_bundle": sys.argv[2],
    "signed": "ad-hoc/unsigned local dogfood artifact",
}
Path(sys.argv[1]).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"package-beta: built {sys.argv[2]}")
PY
