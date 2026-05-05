#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

ARTIFACT_DIR=".harness/runtime/artifacts"
APP_BUNDLE="$ARTIFACT_DIR/IntentOS.app"
LEGACY_APP_BUNDLE="$ARTIFACT_DIR/IntentOSBeta.app"
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

rm -rf "$APP_BUNDLE" "$LEGACY_APP_BUNDLE"
mkdir -p "$APP_BUNDLE/Contents/MacOS" "$APP_BUNDLE/Contents/Resources" "$MODULE_CACHE"
swiftc macos/IntentOSBeta/IntentOSBeta.swift \
  -o "$EXECUTABLE" \
  -parse-as-library \
  -module-cache-path "$MODULE_CACHE" \
  -framework Cocoa
cp macos/IntentOSBeta/Info.plist "$APP_BUNDLE/Contents/Info.plist"
printf '%s\n' "$ROOT" > "$APP_BUNDLE/Contents/Resources/repo-root.txt"

signed="unsigned"
if command -v codesign >/dev/null 2>&1; then
  codesign --force --deep --sign - "$APP_BUNDLE" >/dev/null
  signed="ad-hoc"
fi

if command -v ditto >/dev/null 2>&1; then
  ditto "$APP_BUNDLE" "$LEGACY_APP_BUNDLE"
else
  cp -R "$APP_BUNDLE" "$LEGACY_APP_BUNDLE"
fi

python3 - "$PACKAGE_JSON" "$APP_BUNDLE" "$LEGACY_APP_BUNDLE" "$signed" <<'PY'
import json
import sys
from pathlib import Path

payload = {
    "status": "built",
    "app_bundle": sys.argv[2],
    "legacy_app_bundle": sys.argv[3],
    "bundle_id": "local.intentos.trusted",
    "display_name": "IntentOS",
    "signed": sys.argv[4],
}
Path(sys.argv[1]).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"package-beta: built {sys.argv[2]} signed={sys.argv[4]}")
PY
