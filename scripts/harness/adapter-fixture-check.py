#!/usr/bin/env python3
"""Validate adapter fixture manifests and deterministic replay artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FORBIDDEN_PRIVATE_FIELDS = {
    "authorization",
    "body",
    "content",
    "cookie",
    "cookies",
    "page_body",
    "password",
    "token",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default="data/capture/adapter_fixture_manifest.json",
        help="Adapter fixture manifest JSON path.",
    )
    parser.add_argument(
        "--runtime-dir",
        default=".harness/runtime",
        help="Runtime directory for generated fixture evidence.",
    )
    args = parser.parse_args()

    manifest_path = ROOT / args.manifest
    artifact_dir = ROOT / args.runtime_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifact_dir / "adapter-fixture-check.json"
    failures: list[str] = []
    results: list[dict[str, Any]] = []

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"adapter-fixture-check: failed to read manifest: {exc}", file=sys.stderr)
        return 1

    if not isinstance(manifest, dict):
        failures.append("manifest must be a JSON object")
        adapters: list[Any] = []
    else:
        adapters = manifest.get("adapters", [])
        if manifest.get("version") != 1:
            failures.append("manifest version must be 1")
        if not isinstance(adapters, list) or not adapters:
            failures.append("manifest adapters must be a non-empty array")
            adapters = []

    for index, adapter in enumerate(adapters):
        if not isinstance(adapter, dict):
            failures.append(f"adapter {index} must be an object")
            continue
        results.append(validate_adapter(adapter, artifact_dir, failures))

    payload = {
        "status": "failed" if failures else "ok",
        "manifest": str(manifest_path.relative_to(ROOT)),
        "adapters": results,
        "failures": failures,
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if failures:
        for failure in failures:
            print(f"adapter-fixture-check: {failure}", file=sys.stderr)
        print(f"adapter-fixture-check: wrote {output_path}")
        return 1

    print(f"adapter-fixture-check: ok ({len(results)} adapter fixtures)")
    print(f"adapter-fixture-check: wrote {output_path}")
    return 0


def validate_adapter(
    adapter: dict[str, Any], artifact_dir: Path, failures: list[str]
) -> dict[str, Any]:
    name = required_text(adapter, "name", failures) or "unnamed"
    kind = required_text(adapter, "kind", failures) or "unknown"
    fixture_path = path_value(adapter, "raw_fixture", failures)
    result: dict[str, Any] = {"name": name, "kind": kind}
    if fixture_path is None:
        return result
    result["raw_fixture"] = str(fixture_path.relative_to(ROOT))

    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except Exception as exc:
        failures.append(f"{name}: {fixture_path.relative_to(ROOT)} is invalid JSON: {exc}")
        return result

    if kind in {"macos_stdout_snapshot", "browser_tab_snapshot"}:
        validate_snapshot_fixture(name, adapter, fixture, failures)
        result["status"] = "checked"
        return result
    if kind == "normalization":
        result.update(validate_normalization_fixture(name, adapter, artifact_dir, failures))
        return result

    failures.append(f"{name}: unknown adapter fixture kind {kind!r}")
    return result


def validate_snapshot_fixture(
    name: str, adapter: dict[str, Any], fixture: object, failures: list[str]
) -> None:
    if not isinstance(fixture, dict):
        failures.append(f"{name}: snapshot fixture must be an object")
        return
    if not isinstance(fixture.get("stdout"), str) or not fixture["stdout"].strip():
        failures.append(f"{name}: snapshot fixture must include non-empty stdout")
    expected = fixture.get("expected")
    if not isinstance(expected, dict):
        failures.append(f"{name}: snapshot fixture must include expected object")
        return
    required_fields = adapter.get("required_expected_fields", [])
    if not isinstance(required_fields, list):
        failures.append(f"{name}: required_expected_fields must be an array")
        return
    for field in required_fields:
        if not isinstance(field, str) or field not in expected:
            failures.append(f"{name}: expected is missing {field!r}")


def validate_normalization_fixture(
    name: str, adapter: dict[str, Any], artifact_dir: Path, failures: list[str]
) -> dict[str, Any]:
    from intentos.capture.jsonl import read_events_jsonl
    from intentos.capture_cli import normalize_observations
    from intentos.capture_replay import replay_capture

    raw_path = path_value(adapter, "raw_fixture", failures)
    policy_path = path_value(adapter, "privacy_policy", failures)
    browser_tabs = optional_path_value(adapter, "browser_tabs", failures)
    if raw_path is None or policy_path is None:
        return {"status": "failed"}

    output_jsonl = artifact_dir / f"adapter-fixture-{name}.jsonl"
    merge_adjacent = bool(adapter.get("merge_adjacent", False))
    try:
        count = normalize_observations(
            raw_path,
            output_jsonl,
            policy_path,
            browser_tabs,
            merge_adjacent=merge_adjacent,
        )
        events = read_events_jsonl(output_jsonl, allow_empty=True)
    except Exception as exc:
        failures.append(f"{name}: normalization failed: {exc}")
        return {"status": "failed", "output": rel(output_jsonl)}

    expected_min = adapter.get("expected_min_events", 1)
    if not isinstance(expected_min, int) or expected_min < 0:
        failures.append(f"{name}: expected_min_events must be a non-negative integer")
    elif count < expected_min:
        failures.append(f"{name}: expected at least {expected_min} events, got {count}")

    check_private_fields(name, [asdict(event) for event in events], failures)
    check_excluded_urls(name, adapter, events, failures)

    replay_payload: dict[str, Any] | None = None
    if adapter.get("replay_required", False):
        try:
            replay_payload = replay_capture(output_jsonl, allow_empty=(expected_min == 0))
        except Exception as exc:
            failures.append(f"{name}: replay failed: {exc}")

    return {
        "status": "checked",
        "output": rel(output_jsonl),
        "event_count": count,
        "merge_adjacent": merge_adjacent,
        "replay_status": (replay_payload or {}).get("status", "not_required"),
    }


def check_private_fields(
    name: str, event_dicts: list[dict[str, Any]], failures: list[str]
) -> None:
    for index, event in enumerate(event_dicts):
        top_level = {key.lower() for key in event}
        metadata = event.get("metadata") or {}
        metadata_keys = set(metadata) if isinstance(metadata, dict) else set()
        found = sorted((top_level | {key.lower() for key in metadata_keys}) & FORBIDDEN_PRIVATE_FIELDS)
        if found:
            failures.append(
                f"{name}: event {index} contains unsupported private field(s): "
                + ", ".join(found)
            )


def check_excluded_urls(name: str, adapter: dict[str, Any], events: list[Any], failures: list[str]) -> None:
    substrings = adapter.get("excluded_url_substrings", [])
    if not isinstance(substrings, list):
        failures.append(f"{name}: excluded_url_substrings must be an array")
        return
    for substring in substrings:
        if not isinstance(substring, str):
            failures.append(f"{name}: excluded URL substring must be text")
            continue
        for event in events:
            if substring and substring in (event.url or ""):
                failures.append(f"{name}: excluded URL substring {substring!r} survived privacy filtering")


def required_text(adapter: dict[str, Any], key: str, failures: list[str]) -> str | None:
    value = adapter.get(key)
    if not isinstance(value, str) or not value.strip():
        failures.append(f"adapter is missing non-empty {key}")
        return None
    return value.strip()


def path_value(adapter: dict[str, Any], key: str, failures: list[str]) -> Path | None:
    value = required_text(adapter, key, failures)
    if value is None:
        return None
    path = ROOT / value
    if not path.is_file():
        failures.append(f"{adapter.get('name', 'adapter')}: missing {key} {value}")
        return None
    return path


def optional_path_value(adapter: dict[str, Any], key: str, failures: list[str]) -> Path | None:
    value = adapter.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        failures.append(f"{adapter.get('name', 'adapter')}: {key} must be text")
        return None
    path = ROOT / value
    if not path.is_file():
        failures.append(f"{adapter.get('name', 'adapter')}: missing {key} {value}")
        return None
    return path


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
