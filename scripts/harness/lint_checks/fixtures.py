"""Focused harness lint checks."""

from __future__ import annotations

import json

from .common import ROOT, check_labeled_fixture


def check_evaluation_set(failures: list[str]) -> None:
    check_labeled_fixture(
        failures,
        ROOT / "data/youtube/evaluation_set.json",
        {"learning", "entertainment", "unknown"},
        minimum=6,
    )
    check_labeled_fixture(
        failures,
        ROOT / "data/activity/evaluation_set.json",
        {
            "deep_work",
            "learning",
            "communication",
            "admin",
            "passive_consumption",
            "active_creation",
            "entertainment",
            "unknown",
        },
        minimum=10,
    )
    check_feedback_regression_examples(failures)


def check_feedback_regression_examples(failures: list[str]) -> None:
    activity_path = ROOT / "data/activity/evaluation_set.json"
    taxonomy_path = ROOT / "docs/product/TAXONOMY.md"
    try:
        items = json.loads(activity_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"cannot read feedback regression activity fixtures: {exc}")
        return
    haystacks = [json.dumps(item, sort_keys=True).lower() for item in items]
    required_examples = {
        "developer docs": ["bazel.build"],
        "local IntentOS review": ["127.0.0.1", "intentos"],
        "GitHub repositories": ["github.com", "intent-os"],
        "sports videos": ["youtube.com", "asia cup"],
        "product research": ["linkedin.com/in/example-founder"],
        "personal logistics": ["cravebyleena.com"],
        "shopping": ["amazon.in", "instant pot"],
        "social feed/status": ["x.com", "/status/"],
    }
    for label, needles in required_examples.items():
        if not any(all(needle in haystack for needle in needles) for haystack in haystacks):
            failures.append(
                "data/activity/evaluation_set.json must keep feedback-derived "
                f"{label} coverage"
            )

    text = taxonomy_path.read_text(encoding="utf-8")
    for phrase in [
        "Feedback Regression Checklist",
        "make feedback-fixture-candidates",
        "labeled activity fixture",
    ]:
        if phrase not in text:
            failures.append(f"docs/product/TAXONOMY.md must mention {phrase!r}")


def check_capture_adapter_fixtures(failures: list[str]) -> None:
    manifest = ROOT / "data/capture/adapter_fixture_manifest.json"
    if not manifest.is_file():
        failures.append("missing data/capture/adapter_fixture_manifest.json")
    else:
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"data/capture/adapter_fixture_manifest.json is invalid JSON: {exc}")
        else:
            adapters = payload.get("adapters") if isinstance(payload, dict) else None
            if not isinstance(adapters, list) or len(adapters) < 4:
                failures.append(
                    "data/capture/adapter_fixture_manifest.json must list current adapter fixtures"
                )

    required = {
        "data/capture/macos_frontmost_snapshot.json": [
            "app_name",
            "bundle_id",
            "process_id",
            "window_title",
        ],
        "data/capture/browser_active_tab_snapshot.json": [
            "browser_name",
            "domain",
            "source",
            "title",
            "url",
        ],
    }
    for relative_path, fields in required.items():
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(
                f"missing {relative_path}; real adapters need deterministic fixtures for CI"
            )
            continue

        try:
            fixture = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"{relative_path} is invalid JSON: {exc}")
            continue

        if not isinstance(fixture.get("stdout"), str) or not fixture["stdout"].strip():
            failures.append(f"{relative_path} must include stdout")
        expected = fixture.get("expected")
        if not isinstance(expected, dict):
            failures.append(f"{relative_path} must include expected")
            continue
        for field in fields:
            if field not in expected:
                failures.append(f"{relative_path} expected is missing {field}")


def check_live_observation_harness(failures: list[str]) -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    script = ROOT / "scripts/harness/observe-live.sh"
    session_script = ROOT / "scripts/harness/observe-session.sh"
    dev_live_script = ROOT / "scripts/harness/dev-live.sh"
    if "observe-live:" not in makefile:
        failures.append("Makefile must expose make observe-live for manual sensor diagnostics")
    if "observe-session:" not in makefile:
        failures.append("Makefile must expose make observe-session for session diagnostics")
    if "dev-live:" not in makefile:
        failures.append("Makefile must expose make dev-live for live session UI diagnostics")
    if not script.is_file():
        failures.append("missing scripts/harness/observe-live.sh")
    else:
        text = script.read_text(encoding="utf-8")
        for phrase in ["capture-macos", "live-capture-events.jsonl", "live-capture.log"]:
            if phrase not in text:
                failures.append(f"scripts/harness/observe-live.sh must mention {phrase}")
    if not session_script.is_file():
        failures.append("missing scripts/harness/observe-session.sh")
    else:
        text = session_script.read_text(encoding="utf-8")
        for phrase in [
            "capture-session",
            "live-session-capture-events.jsonl",
            "live-session-capture.log",
        ]:
            if phrase not in text:
                failures.append(f"scripts/harness/observe-session.sh must mention {phrase}")
    if not dev_live_script.is_file():
        failures.append("missing scripts/harness/dev-live.sh")
    else:
        text = dev_live_script.read_text(encoding="utf-8")
        for phrase in [
            "observe-session.sh",
            "INTENTOS_PRESERVE_LIVE_ARTIFACTS=1",
            "INTENTOS_DEV_DATA_MODE=\"live_session\"",
        ]:
            if phrase not in text:
                failures.append(f"scripts/harness/dev-live.sh must mention {phrase}")
