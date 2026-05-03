#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

ARTIFACT_DIR=".harness/runtime/artifacts"
EXTENSION_DIR="extension/chrome"
PACKAGE_PATH="$ARTIFACT_DIR/IntentOSChromeBridge.zip"
PACKAGE_JSON="$ARTIFACT_DIR/beta-extension-package.json"

mkdir -p "$ARTIFACT_DIR"

python3 - "$EXTENSION_DIR" "$PACKAGE_PATH" "$PACKAGE_JSON" <<'PY'
import json
import sys
import zipfile
from pathlib import Path

extension_dir = Path(sys.argv[1])
package_path = Path(sys.argv[2])
package_json = Path(sys.argv[3])
manifest_path = extension_dir / "manifest.json"

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
if manifest.get("manifest_version") != 3:
    raise SystemExit("package-extension: Chrome extension must use Manifest V3")
if "background" not in manifest or "service_worker" not in manifest["background"]:
    raise SystemExit("package-extension: Chrome extension requires a service worker")

with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(extension_dir.rglob("*")):
        if path.is_file() and "__MACOSX" not in path.parts:
            archive.write(path, path.relative_to(extension_dir))

payload = {
    "status": "packaged",
    "extension_dir": str(extension_dir),
    "package": str(package_path),
    "version": manifest.get("version"),
}
package_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"package-extension: wrote {package_path}")
PY
