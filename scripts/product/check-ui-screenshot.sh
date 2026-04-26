#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

SCREENSHOT="${INTENTOS_UI_SCREENSHOT:-docs/assets/screenshots/intent-os-ui.png}"
METADATA="${INTENTOS_UI_SCREENSHOT_METADATA:-docs/assets/screenshots/intent-os-ui.json}"

python3 - "$SCREENSHOT" "$METADATA" <<'PY'
import json
import importlib.util
import sys
from pathlib import Path

screenshot = Path(sys.argv[1])
metadata_path = Path(sys.argv[2])
manifest_path = Path("scripts/product/ui-screenshot-manifest.py")
png_validation_path = Path("scripts/product/png_validation.py")
spec = importlib.util.spec_from_file_location("ui_screenshot_manifest", manifest_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
png_spec = importlib.util.spec_from_file_location("png_validation", png_validation_path)
png_module = importlib.util.module_from_spec(png_spec)
assert png_spec.loader is not None
png_spec.loader.exec_module(png_module)

if not screenshot.is_file():
    raise SystemExit(f"missing UI screenshot {screenshot}; run make update-ui-screenshot")
if not metadata_path.is_file():
    raise SystemExit(f"missing UI screenshot metadata {metadata_path}; run make update-ui-screenshot")

try:
    stats = png_module.assert_useful_png(screenshot, min_width=1024, min_height=700)
except Exception as exc:
    raise SystemExit(str(exc)) from exc
width = stats["width"]
height = stats["height"]

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

print(
    "ui-screenshot-check: ok "
    f"({width}x{height}, colors={stats['unique_color_count']}, "
    f"luminance_range={stats['luminance_range']})"
)
PY
