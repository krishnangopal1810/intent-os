#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

ARTIFACT_DIR=".harness/runtime/artifacts"
APP_BUNDLE="$ARTIFACT_DIR/IntentOS.app"
RUNTIME_DIR="$APP_BUNDLE/Contents/Resources/intent-os-runtime"
ZIP_PATH="$ARTIFACT_DIR/IntentOS-trusted-beta.zip"
PACKAGE_JSON="$ARTIFACT_DIR/onboarding-beta-package.json"

mkdir -p "$ARTIFACT_DIR"

scripts/product/package-beta.sh

if [ "$(uname -s)" != "Darwin" ] || [ ! -d "$APP_BUNDLE" ]; then
  python3 - "$PACKAGE_JSON" <<'PY'
import json
import sys
from pathlib import Path

payload = {
    "status": "skipped",
    "reason": "macOS Swift packaging is required for the trusted tester app artifact",
}
Path(sys.argv[1]).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print("package-onboarding-beta: skipped - macOS app bundle is unavailable")
PY
  exit 0
fi

rm -rf "$RUNTIME_DIR"
mkdir -p "$RUNTIME_DIR"

copy_path() {
  local source="$1"
  local target="$RUNTIME_DIR/$source"
  mkdir -p "$(dirname "$target")"
  if command -v ditto >/dev/null 2>&1; then
    ditto "$source" "$target"
  else
    cp -R "$source" "$target"
  fi
}

for path in \
  Makefile \
  README.md \
  data \
  docs/APP_RUNTIME.md \
  docs/SECURITY.md \
  docs/product \
  extension \
  intentos \
  scripts \
  web
do
  copy_path "$path"
done

rm -rf "$RUNTIME_DIR/.harness" "$RUNTIME_DIR/__pycache__"
find "$RUNTIME_DIR" -name "__pycache__" -type d -prune -exec rm -rf {} +
printf '%s\n' "bundled-runtime" > "$APP_BUNDLE/Contents/Resources/repo-root.txt"

signed="unsigned"
if command -v codesign >/dev/null 2>&1; then
  codesign --force --deep --sign - "$APP_BUNDLE" >/dev/null
  signed="ad-hoc"
fi

rm -f "$ZIP_PATH"
(
  cd "$ARTIFACT_DIR"
  ditto -c -k --keepParent "IntentOS.app" "IntentOS-trusted-beta.zip"
)

python3 - "$PACKAGE_JSON" "$APP_BUNDLE" "$ZIP_PATH" "$RUNTIME_DIR" "$signed" <<'PY'
import json
import sys
from pathlib import Path

payload = {
    "status": "built",
    "app_bundle": sys.argv[2],
    "zip": sys.argv[3],
    "bundled_runtime": sys.argv[4],
    "signed": sys.argv[5],
    "normal_path_requires_terminal": False,
    "bundle_id": "local.intentos.trusted",
    "display_name": "IntentOS",
}
Path(sys.argv[1]).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"package-onboarding-beta: built {sys.argv[3]} signed={sys.argv[5]}")
PY
