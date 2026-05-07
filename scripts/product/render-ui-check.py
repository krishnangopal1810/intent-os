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


ROOT = Path(__file__).resolve().parents[2]
COPY_POLICY = ROOT / "data/ui/visible_copy_policy.json"


def read_png_dimensions(data: bytes) -> tuple[int, int]:
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 24:
        raise ValueError("not a valid PNG")
    return struct.unpack(">II", data[16:24])


def png_unique_sample_count(data: bytes, limit: int = 12000) -> int:
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
                row[x] = (row[x] + paeth(left, up, upper_left)) & 0xFF
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


def probe_int(payload: dict[str, object], key: str) -> int:
    try:
        return int(payload.get(key, 0))
    except (TypeError, ValueError):
        return 0


def load_copy_policy() -> dict[str, object]:
    if not COPY_POLICY.is_file():
        return {"version": 0, "forbidden_phrases": [], "raw_error_patterns": []}
    return json.loads(COPY_POLICY.read_text(encoding="utf-8"))


def validate_probe(
    probe: dict[str, object],
    *,
    min_stat_count: int = 3,
    scenario: str = "",
    copy_policy: dict[str, object] | None = None,
) -> list[str]:
    failures: list[str] = []
    scenarios = set(probe.get("scenarios") or [])
    if scenario:
        scenarios.add(scenario)
    is_stale = "beta-service-stale" in scenarios
    is_empty = "beta-empty" in scenarios
    is_intent_missing = "beta-intent-missing" in scenarios
    is_beta = probe.get("mode") == "beta" or any(
        str(scenario).startswith("beta-") for scenario in scenarios
    )

    if probe.get("schema_version") != 1:
        failures.append("render probe schema_version must be 1")
    for key in [
        "copy_policy",
        "first_viewport",
        "default_density",
        "text_layout",
        "section_nav",
        "intent_preview",
        "service_state",
        "workflow_probe",
    ]:
        if key not in probe:
            failures.append(f"render probe missing {key}")

    if not probe.get("root_present"):
        failures.append("missing data-ui-root")
    if int(probe.get("body_text_length", 0)) < 120:
        failures.append("rendered page has too little text")
    if not is_stale and not is_empty:
        if int(probe.get("panel_count", 0)) < 2:
            failures.append("expected rendered activity and timeline panels")
        if int(probe.get("stat_count", 0)) < min_stat_count:
            failures.append("expected rendered behavior stats")
        if int(probe.get("event_count", 0)) < 1:
            failures.append("expected rendered capture events")
        if len(str(probe.get("next_move_text", "")).strip()) < 4:
            failures.append("expected rendered next move text")
    if int(probe.get("decision_count", 0)) < 1 and not is_stale:
        failures.append("expected rendered next-step decision card")
    if not probe.get("coach_hero_present"):
        failures.append("expected rendered plan-vs-actual coach hero")
    if is_beta and not is_stale:
        if not probe.get("focus_rescue_present"):
            failures.append("expected rendered focus rescue state")
        if len(str(probe.get("focus_rescue_text", "")).strip()) < 12:
            failures.append("expected focus rescue copy")
        rescue_text = str(probe.get("focus_rescue_text", ""))
        rescue_needs_actions = "Recovery available" in rescue_text or "Avoid leaking" in rescue_text
        if rescue_needs_actions and int(probe.get("focus_rescue_action_count", 0)) < 3:
            failures.append("expected focus rescue action buttons")
    if not probe.get("weekly_details_present"):
        failures.append("expected weekly patterns disclosure")
    if not probe.get("daily_loop_present"):
        failures.append("expected rendered daily intent loop")
    if not is_stale and len(str(probe.get("daily_loop_text", "")).strip()) < 20:
        failures.append("expected rendered daily loop text")
    receipt_required = is_beta and not is_stale and not is_empty and not is_intent_missing
    if receipt_required and not probe.get("evening_receipt_present"):
        failures.append("expected rendered evening receipt")
    if receipt_required and len(str(probe.get("evening_receipt_text", "")).strip()) < 20:
        failures.append("expected evening receipt summary")
    if is_beta and not is_stale and int(probe.get("onboarding_step_count", 0)) < 5:
        failures.append("expected five-step onboarding stepper")
    step_text = str(probe.get("onboarding_step_text", ""))
    for phrase in ["Privacy", "App access", "Capture check", "Daily focus", "First block"]:
        if is_beta and not is_stale and phrase not in step_text:
            failures.append(f"onboarding stepper missing {phrase}")
    if is_beta and not is_stale and not str(probe.get("capture_preview_state", "")):
        failures.append("expected capture preview state")
    if not probe.get("command_center_present"):
        failures.append("expected rendered command center")
    if int(probe.get("command_step_count", 0)) < 3:
        failures.append("expected Now, Trust, and Tonight command steps")
    command_text = str(probe.get("command_center_text", ""))
    for phrase in ["Now", "Trust", "Tonight"]:
        if phrase not in command_text:
            failures.append(f"command center missing {phrase}")
    first_viewport = probe.get("first_viewport")
    if isinstance(first_viewport, dict):
        if not first_viewport.get("coach_hero_present"):
            failures.append("first viewport missing plan-vs-actual hero")
        if is_beta and not is_stale and not first_viewport.get("focus_rescue_present"):
            failures.append("first viewport missing focus rescue state")
        if int(first_viewport.get("coach_receipt_count", 0)) < 1 and not is_stale:
            failures.append("first viewport missing inline evidence receipts")
        if not first_viewport.get("weekly_details_present"):
            failures.append("weekly patterns disclosure disappeared")

    failures.extend(validate_copy_policy(probe, copy_policy or load_copy_policy()))
    failures.extend(validate_section_nav(probe))
    failures.extend(validate_layout(probe))
    failures.extend(validate_density(probe))
    failures.extend(validate_service_state(probe, is_stale=is_stale))
    failures.extend(validate_intent_preview(probe, required=is_intent_missing))
    failures.extend(validate_workflow(probe))
    if probe.get("youtube_visible"):
        failures.append("beta dashboard must hide the legacy YouTube panel")
    return failures


def validate_copy_policy(probe: dict[str, object], policy: dict[str, object]) -> list[str]:
    diagnostics = probe.get("copy_policy")
    if not isinstance(diagnostics, dict):
        return ["copy policy diagnostics did not run"]
    failures: list[str] = []
    if diagnostics.get("policy_version") != policy.get("version"):
        failures.append("copy policy version does not match fixture")
    forbidden_hits = diagnostics.get("forbidden_hits") or []
    raw_error_hits = diagnostics.get("raw_error_hits") or []
    if forbidden_hits:
        failures.append("visible copy includes forbidden product language: " + ", ".join(forbidden_hits))
    if raw_error_hits:
        failures.append("visible copy includes raw developer error text: " + ", ".join(raw_error_hits))
    return failures


def validate_section_nav(probe: dict[str, object]) -> list[str]:
    section_nav = probe.get("section_nav")
    if not isinstance(section_nav, dict):
        return ["section navigation probe did not run"]
    failures: list[str] = []
    if not section_nav.get("available"):
        failures.append("section navigation probe did not run")
    if not section_nav.get("nav_visible_after_activity"):
        failures.append("section navigation is not visible after Activity jump")
    if section_nav.get("activity_required_scroll") and not section_nav.get("workspace_scrolled_after_activity"):
        failures.append("Activity jump did not scroll the content pane")
    if int(section_nav.get("document_scroll_delta", 0)) > 2:
        failures.append("Activity jump scrolled the document instead of the content pane")
    if section_nav.get("active_href_after_activity") != "#activity-title":
        failures.append("Activity jump did not activate the Activity nav item")
    if not section_nav.get("evidence_open_after_activity"):
        failures.append("Activity jump did not open supporting evidence")
    if int(section_nav.get("visible_report_panels_after_activity", 0)) < 2:
        failures.append("Activity jump did not reveal activity and timeline evidence")
    if int(section_nav.get("cut_off_text_after_activity", 0)) > 0:
        failures.append("Activity jump leaves visible text cut off")
    if int(section_nav.get("clipped_text_after_activity", 0)) > 0:
        failures.append("Activity jump leaves visible text clipped")
    return failures


def validate_layout(probe: dict[str, object]) -> list[str]:
    failures: list[str] = []
    for key, label in [("text_layout", "default"), ("current_text_layout", "current")]:
        text_layout = probe.get(key)
        if isinstance(text_layout, dict):
            if probe_int(text_layout, "cut_off_text_count") > 0:
                failures.append(f"{label} visible text is cut off by the viewport")
            if probe_int(text_layout, "clipped_text_count") > 0:
                failures.append(f"{label} visible text is clipped inside its container")
    if probe.get("horizontal_overflow"):
        failures.append("page has horizontal overflow")
    if int(probe.get("out_of_view_count", 0)) > 0:
        failures.append("visible elements extend outside the viewport")
    if int(probe.get("clipped_text_count", 0)) > 0:
        failures.append("visible text is clipped")
    if int(probe.get("cut_off_text_count", 0)) > 0:
        failures.append("visible text is cut off")
    return failures


def validate_density(probe: dict[str, object]) -> list[str]:
    default_density = probe.get("default_density")
    if not isinstance(default_density, dict):
        return ["default density diagnostics did not run"]
    failures: list[str] = []
    if probe_int(default_density, "visible_decision_cards") > 1:
        failures.append("default dashboard shows too many decision cards")
    if probe_int(default_density, "visible_stats") > 0:
        failures.append("default dashboard exposes metric stats instead of hiding them")
    if probe_int(default_density, "visible_insights") > 0:
        failures.append("default dashboard exposes insight lists instead of hiding them")
    if probe_int(default_density, "visible_queue_panels") > 0:
        failures.append("default dashboard exposes queue panels instead of hiding them")
    if probe_int(default_density, "visible_report_panels") > 0:
        failures.append("default dashboard exposes raw evidence panels instead of hiding them")
    if probe_int(default_density, "supporting_detail_count") < 2:
        failures.append("default dashboard needs supporting-detail disclosure rows")
    if probe_int(default_density, "collapsed_supporting_detail_count") < 2:
        failures.append("supporting details should be collapsed by default")
    if probe_int(default_density, "visible_word_count") > 360:
        failures.append("default dashboard has too much visible text")
    return failures


def validate_service_state(probe: dict[str, object], *, is_stale: bool) -> list[str]:
    service_state = probe.get("service_state")
    if not isinstance(service_state, dict):
        return ["service state diagnostics did not run"]
    if not is_stale:
        return []
    if not service_state.get("notice_visible"):
        return ["stale service scenario did not show the service notice"]
    if not service_state.get("reconnect_visible"):
        return ["stale service scenario did not show Reconnect IntentOS"]
    return []


def validate_intent_preview(probe: dict[str, object], *, required: bool) -> list[str]:
    intent_preview = probe.get("intent_preview")
    if not isinstance(intent_preview, dict):
        return ["intent preview diagnostics did not run"]
    if required and not intent_preview.get("form_visible"):
        return ["missing-intent scenario did not show the daily intent form"]
    if required and not intent_preview.get("typed"):
        return ["missing-intent scenario did not type into the intent form"]
    if not intent_preview.get("typed"):
        return []
    failures = []
    if not intent_preview.get("focus_preview_mentions_input"):
        failures.append("intent preview did not reflect typed focus text")
    if not intent_preview.get("avoid_preview_mentions_input"):
        failures.append("intent preview did not reflect typed avoid text")
    if not intent_preview.get("review_preview_mentions_note"):
        failures.append("intent preview did not reflect typed note text")
    return failures


def validate_workflow(probe: dict[str, object]) -> list[str]:
    workflow = probe.get("workflow_probe")
    workflow_expected = bool(probe.get("workflow_expected"))
    if not isinstance(workflow, dict):
        return ["required beta workflow probe did not run"] if workflow_expected else []
    if not workflow.get("clicked"):
        return ["required beta workflow probe did not click any visible controls"] if workflow_expected else []
    failures: list[str] = []
    clicked = set(workflow.get("clicked") or [])
    if not clicked.intersection({"[data-onboarding-privacy]", "[data-onboarding-check]"}):
        failures.append("beta workflow probe did not exercise first-run setup controls")
    if not clicked.intersection(
        {
            "[data-open-accessibility]",
            "[data-open-automation]",
            "[data-open-chrome]",
            "[data-copy-setup-report]",
        }
    ):
        failures.append("beta workflow probe did not exercise setup support controls")
    if not workflow.get("setup_guidance_visible"):
        failures.append("beta workflow probe did not render setup guidance")
    if int(probe.get("correction_controls", 0)) < 1 or not workflow.get("correction_changed"):
        failures.append("beta workflow probe did not exercise correction controls")
    return failures


def main() -> int:
    screenshot = Path(sys.argv[1])
    dom_path = Path(sys.argv[2])
    json_output = Path(sys.argv[3])
    text_output = Path(sys.argv[4])
    min_stat_count = int(sys.argv[5]) if len(sys.argv) > 5 else 3
    scenario = sys.argv[6] if len(sys.argv) > 6 else ""

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
        failures.extend(
            validate_probe(
                probe,
                min_stat_count=min_stat_count,
                scenario=scenario,
                copy_policy=load_copy_policy(),
            )
        )
    elif dom_path.is_file() and dom_path.stat().st_size > 0:
        failures.append("rendered DOM did not include the shared UI probe")
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
        "scenario": scenario,
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
                f"scenario={scenario or 'default'}",
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
