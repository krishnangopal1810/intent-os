#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

SCREENSHOT="${INTENTOS_UI_SCREENSHOT:-docs/assets/screenshots/intent-os-ui.png}"
METADATA="${INTENTOS_UI_SCREENSHOT_METADATA:-docs/assets/screenshots/intent-os-ui.json}"

python3 - "$SCREENSHOT" "$METADATA" <<'PY'
import json
import importlib.util
import struct
import sys
from pathlib import Path

screenshot = Path(sys.argv[1])
metadata_path = Path(sys.argv[2])
manifest_path = Path("scripts/product/ui-screenshot-manifest.py")
spec = importlib.util.spec_from_file_location("ui_screenshot_manifest", manifest_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

if not screenshot.is_file():
    raise SystemExit(f"missing UI screenshot {screenshot}; run make update-ui-screenshot")
if not metadata_path.is_file():
    raise SystemExit(f"missing UI screenshot metadata {metadata_path}; run make update-ui-screenshot")

data = screenshot.read_bytes()
if not data.startswith(b"\x89PNG\r\n\x1a\n"):
    raise SystemExit(f"{screenshot} is not a PNG")
if len(data) < 24:
    raise SystemExit(f"{screenshot} is too small to be a valid PNG")

width, height = struct.unpack(">II", data[16:24])
if width < 1024 or height < 700:
    raise SystemExit(f"{screenshot} dimensions are too small: {width}x{height}")

metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
current = module.manifest()
if metadata.get("source_hash") != current["source_hash"]:
    raise SystemExit(
        "checked-in UI screenshot is stale; run make update-ui-screenshot"
    )
if metadata.get("width") != width or metadata.get("height") != height:
    raise SystemExit(f"{metadata_path} dimensions do not match {screenshot}")
if metadata.get("path") != str(screenshot):
    raise SystemExit(f"{metadata_path} path does not match {screenshot}")

print(f"ui-screenshot-check: ok ({width}x{height})")
PY
