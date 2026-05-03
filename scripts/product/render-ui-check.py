#!/usr/bin/env python3
"""Validate rendered UI evidence from a headless browser run."""

from __future__ import annotations

import json
import math
import re
import struct
import sys
import time
import zlib
from pathlib import Path


def read_png_dimensions(data: bytes) -> tuple[int, int]:
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 24:
        raise ValueError("not a valid PNG")
    return struct.unpack(">II", data[16:24])


def png_unique_sample_count(data: bytes, limit: int = 12000) -> int:
    """Return an approximate unique pixel count for simple PNG screenshots."""

    width, height = read_png_dimensions(data)
    offset = 8
    color_type = None
    bit_depth = None
    idat = bytearray()

    while offset + 8 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if chunk_type == b"IHDR":
            bit_depth = payload[8]
            color_type = payload[9]
        elif chunk_type == b"IDAT":
            idat.extend(payload)
        elif chunk_type == b"IEND":
            break

    if bit_depth != 8 or color_type not in {0, 2, 6}:
        return max(2, len(set(data[:: max(1, len(data) // limit)])))

    channels = {0: 1, 2: 3, 6: 4}[color_type]
    stride = width * channels
    raw = zlib.decompress(bytes(idat))
    previous = bytearray(stride)
    pixels: set[bytes] = set()
    row_size = stride + 1
    grid = max(1, int(math.sqrt(limit)))
    row_step = max(1, height // grid)
    col_step = max(1, width // grid)

    for y in range(height):
        start = y * row_size
        filter_type = raw[start]
        row = bytearray(raw[start + 1 : start + row_size])
        for x in range(stride):
            left = row[x - channels] if x >= channels else 0
            up = previous[x]
            upper_left = previous[x - channels] if x >= channels else 0
            if filter_type == 1:
                row[x] = (row[x] + left) & 0xFF
            elif filter_type == 2:
                row[x] = (row[x] + up) & 0xFF
            elif filter_type == 3:
                row[x] = (row[x] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                predictor = paeth(left, up, upper_left)
                row[x] = (row[x] + predictor) & 0xFF
            elif filter_type != 0:
                raise ValueError(f"unsupported PNG filter {filter_type}")

        if y % row_step == 0:
            for x in range(0, width, col_step):
                index = x * channels
                pixels.add(bytes(row[index : index + channels]))
                if len(pixels) >= limit:
                    break
        previous = row
        if len(pixels) >= limit:
            break

    return len(pixels)


def paeth(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    left_distance = abs(estimate - left)
    up_distance = abs(estimate - up)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= up_distance and left_distance <= upper_left_distance:
        return left
    if up_distance <= upper_left_distance:
        return up
    return upper_left


def extract_probe(dom: str) -> dict[str, object] | None:
    match = re.search(
        r'<script id="intentos-render-probe" type="application/json">(.+?)</script>',
        dom,
        re.DOTALL,
    )
    if not match:
        return None
    return json.loads(match.group(1).replace("&quot;", '"').replace("&amp;", "&"))


def wait_for_stable_file(path: Path) -> None:
    last_size = -1
    stable_reads = 0
    for _ in range(50):
        if path.is_file():
            size = path.stat().st_size
            if size > 0 and size == last_size:
                stable_reads += 1
                if stable_reads >= 2:
                    return
            else:
                stable_reads = 0
            last_size = size
        time.sleep(0.1)
    raise SystemExit(f"missing rendered UI artifact: {path}")


def main() -> int:
    screenshot = Path(sys.argv[1])
    dom_path = Path(sys.argv[2])
    json_output = Path(sys.argv[3])
    text_output = Path(sys.argv[4])
    min_stat_count = int(sys.argv[5]) if len(sys.argv) > 5 else 3

    wait_for_stable_file(screenshot)
    if dom_path.exists():
        wait_for_stable_file(dom_path)

    png = screenshot.read_bytes()
    width, height = read_png_dimensions(png)
    unique_pixels = png_unique_sample_count(png)
    if width < 320 or height < 480:
        raise SystemExit(f"rendered screenshot is too small: {width}x{height}")
    if screenshot.stat().st_size < 20000 or unique_pixels < 20:
        raise SystemExit("rendered screenshot appears blank or visually empty")

    probe = None
    if dom_path.is_file() and dom_path.stat().st_size > 0:
        probe = extract_probe(dom_path.read_text(encoding="utf-8"))
    failures = []
    if probe is not None:
        if not probe.get("root_present"):
            failures.append("missing data-ui-root")
        if int(probe.get("body_text_length", 0)) < 200:
            failures.append("rendered page has too little text")
        if int(probe.get("panel_count", 0)) < 2:
            failures.append("expected rendered activity and timeline panels")
        if int(probe.get("stat_count", 0)) < min_stat_count:
            failures.append("expected rendered behavior stats")
        if int(probe.get("decision_count", 0)) < 4:
            failures.append("expected rendered daily decision cards")
        if int(probe.get("event_count", 0)) < 1:
            failures.append("expected rendered capture events")
        if len(str(probe.get("next_move_text", "")).strip()) < 4:
            failures.append("expected rendered next move text")
        if probe.get("horizontal_overflow"):
            failures.append("page has horizontal overflow")
        if int(probe.get("out_of_view_count", 0)) > 0:
            failures.append("visible elements extend outside the viewport")
        if int(probe.get("clipped_text_count", 0)) > 0:
            failures.append("visible text is clipped")
        if probe.get("youtube_visible"):
            failures.append("beta dashboard must hide the legacy YouTube panel")
        workflow = probe.get("workflow_probe")
        if isinstance(workflow, dict):
            clicked = set(workflow.get("clicked") or [])
            for selector in [
                "[data-onboarding-check]",
                "[data-open-accessibility]",
                "[data-open-automation]",
                "[data-open-chrome]",
            ]:
                if selector not in clicked:
                    failures.append(f"beta workflow probe did not click {selector}")
            if not workflow.get("setup_guidance_visible"):
                failures.append("beta workflow probe did not render setup guidance")
            if int(probe.get("correction_controls", 0)) < 1 or not workflow.get(
                "correction_changed"
            ):
                failures.append("beta workflow probe did not exercise correction controls")
    if failures:
        raise SystemExit("; ".join(failures))

    validation = {
        "status": "ok",
        "screenshot": str(screenshot),
        "dom": str(dom_path),
        "width": width,
        "height": height,
        "unique_pixel_sample_count": unique_pixels,
        "probe_available": probe is not None,
        "min_stat_count": min_stat_count,
        "probe": probe or {},
    }
    json_output.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    text_output.write_text(
        "\n".join(
            [
                "ui-render-validation: ok",
                f"screenshot={screenshot}",
                f"dimensions={width}x{height}",
                f"unique_pixel_sample_count={unique_pixels}",
                f"probe_available={str(probe is not None).lower()}",
                f"panel_count={(probe or {}).get('panel_count')}",
                f"decision_count={(probe or {}).get('decision_count')}",
                f"event_count={(probe or {}).get('event_count')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(text_output.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
