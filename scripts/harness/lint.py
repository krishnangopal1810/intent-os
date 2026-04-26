#!/usr/bin/env python3
"""Repository structural checks for agent-legible development."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAX_PYTHON_LINES = 320
EXPECTED_LAYERS = {
    "intentos/activity.py",
    "intentos/classifier.py",
    "intentos/reporting.py",
    "intentos/activity_cli.py",
    "intentos/activity_evaluate.py",
    "intentos/capture/__init__.py",
    "intentos/capture/browser.py",
    "intentos/capture/core.py",
    "intentos/capture/jsonl.py",
    "intentos/capture/macos.py",
    "intentos/capture/privacy.py",
    "intentos/capture_cli.py",
    "intentos/capture_replay.py",
    "intentos/youtube.py",
    "intentos/cli.py",
    "intentos/evaluate.py",
    "tests/test_activity_classification.py",
    "tests/test_capture_browser.py",
    "tests/test_capture_core.py",
    "tests/test_capture_macos.py",
    "tests/test_capture_privacy.py",
    "tests/test_capture_replay.py",
    "tests/test_youtube_mvp.py",
}
ALLOWED_IMPORTS = {
    "intentos/cli.py": {"intentos.youtube"},
    "intentos/evaluate.py": {"intentos.youtube"},
    "intentos/classifier.py": {"intentos.activity"},
    "intentos/reporting.py": {
        "intentos.activity",
        "intentos.classifier",
        "intentos.youtube",
    },
    "intentos/activity_cli.py": {"intentos.activity", "intentos.reporting"},
    "intentos/activity_evaluate.py": {"intentos.activity", "intentos.classifier"},
    "intentos/capture/__init__.py": {
        "intentos.capture.core",
        "intentos.capture.jsonl",
    },
    "intentos/capture/browser.py": set(),
    "intentos/capture/core.py": {"intentos.activity"},
    "intentos/capture/jsonl.py": {"intentos.activity"},
    "intentos/capture/macos.py": {"intentos.capture.core"},
    "intentos/capture/privacy.py": set(),
    "intentos/capture_replay.py": {"intentos.capture.jsonl", "intentos.reporting"},
    "intentos/capture_cli.py": {
        "intentos.capture.browser",
        "intentos.capture.core",
        "intentos.capture.jsonl",
        "intentos.capture.macos",
        "intentos.capture.privacy",
        "intentos.capture_replay",
    },
    "tests/test_activity_classification.py": {
        "intentos.activity",
        "intentos.activity_evaluate",
        "intentos.classifier",
        "intentos.reporting",
    },
    "tests/test_capture_browser.py": {"intentos.capture.browser"},
    "tests/test_capture_core.py": {
        "intentos.capture.core",
        "intentos.capture.jsonl",
    },
    "tests/test_capture_macos.py": {"intentos.capture.macos"},
    "tests/test_capture_privacy.py": {"intentos.capture.privacy"},
    "tests/test_capture_replay.py": {
        "intentos.capture_cli",
        "intentos.capture_replay",
    },
    "tests/test_youtube_mvp.py": {"intentos.youtube"},
}


def main() -> int:
    failures: list[str] = []
    check_required_python_files(failures)
    check_python_syntax_and_imports(failures)
    check_file_sizes(failures)
    check_generated_files_not_tracked(failures)
    check_no_stale_active_plans(failures)
    check_quality_scorecard(failures)
    check_evaluation_set(failures)
    check_capture_adapter_fixtures(failures)
    check_live_observation_harness(failures)
    check_ui_harness(failures)
    check_live_capture_contract(failures)
    check_parallel_plan_contract(failures)

    if failures:
        for failure in failures:
            print(f"harness-lint: {failure}", file=sys.stderr)
        return 1

    print("harness-lint: ok")
    return 0


def check_required_python_files(failures: list[str]) -> None:
    for path in sorted(EXPECTED_LAYERS):
        if not (ROOT / path).is_file():
            failures.append(
                f"missing {path}; keep the MVP layer map in docs/ARCHITECTURE.md "
                "and scripts/harness/lint.py aligned"
            )


def check_python_syntax_and_imports(failures: list[str]) -> None:
    for path in sorted(EXPECTED_LAYERS):
        full_path = ROOT / path
        if not full_path.is_file():
            continue
        try:
            tree = ast.parse(full_path.read_text(encoding="utf-8"), filename=path)
        except SyntaxError as exc:
            failures.append(f"{path} has invalid Python syntax: {exc}")
            continue

        imported = import_targets(tree)
        if path in {"intentos/youtube.py", "intentos/activity.py"}:
            forbidden = sorted(
                target
                for target in imported
                if target.startswith("intentos.") and target != path.removesuffix(".py").replace("/", ".")
            )
            if forbidden:
                failures.append(
                    f"{path} is the domain layer and must not import other "
                    f"IntentOS layers; remove {', '.join(forbidden)}"
                )
            continue

        allowed = ALLOWED_IMPORTS.get(path, set())
        forbidden = sorted(
            target
            for target in imported
            if target.startswith("intentos.") and target not in allowed
        )
        if forbidden:
            failures.append(
                f"{path} imports disallowed IntentOS layer(s): {', '.join(forbidden)}; "
                "update the architecture doc and linter if this boundary is intentional"
            )


def import_targets(tree: ast.AST) -> set[str]:
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                targets.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            targets.add(node.module)
    return targets


def check_file_sizes(failures: list[str]) -> None:
    for path in sorted(EXPECTED_LAYERS):
        full_path = ROOT / path
        if not full_path.is_file():
            continue
        line_count = len(full_path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_PYTHON_LINES:
            failures.append(
                f"{path} is {line_count} lines; split it before it exceeds "
                f"the {MAX_PYTHON_LINES}-line agent-legibility limit"
            )


def check_generated_files_not_tracked(failures: list[str]) -> None:
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.splitlines()
    generated = [
        path
        for path in tracked
        if "__pycache__/" in path
        or path.endswith(".pyc")
        or path.startswith(".harness/runtime/")
    ]
    if generated:
        failures.append(
            "generated runtime/cache files are tracked: "
            + ", ".join(sorted(generated))
            + "; remove them from git"
        )


def check_no_stale_active_plans(failures: list[str]) -> None:
    active_dir = ROOT / "docs/plans/active"
    for plan in sorted(active_dir.glob("*.md")):
        text = plan.read_text(encoding="utf-8")
        if "Status: Completed" in text:
            failures.append(
                f"{plan.relative_to(ROOT)} is completed but still active; move it "
                "to docs/plans/completed/"
            )
        if "TBD" in text:
            failures.append(
                f"{plan.relative_to(ROOT)} still contains TBD; resolve or narrow "
                "the plan before implementation"
            )


def check_quality_scorecard(failures: list[str]) -> None:
    text = (ROOT / "docs/QUALITY.md").read_text(encoding="utf-8")
    required_rows = [
        "| Product definition |",
        "| Architecture |",
        "| Verification |",
        "| Security |",
        "| Reliability |",
        "| UX |",
    ]
    for row in required_rows:
        if row not in text:
            failures.append(f"docs/QUALITY.md is missing scorecard row {row}")
    if "| Verification | Green |" not in text:
        failures.append(
            "docs/QUALITY.md should mark verification Green once make verify "
            "runs product tests and evaluation"
        )


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


def check_capture_adapter_fixtures(failures: list[str]) -> None:
    path = ROOT / "data/capture/macos_frontmost_snapshot.json"
    if not path.is_file():
        failures.append(
            "missing data/capture/macos_frontmost_snapshot.json; real adapters "
            "need deterministic fixtures for CI"
        )
        return

    try:
        fixture = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"data/capture/macos_frontmost_snapshot.json is invalid JSON: {exc}")
        return

    if not isinstance(fixture.get("stdout"), str) or not fixture["stdout"].strip():
        failures.append("data/capture/macos_frontmost_snapshot.json must include stdout")
    expected = fixture.get("expected")
    if not isinstance(expected, dict):
        failures.append("data/capture/macos_frontmost_snapshot.json must include expected")
        return
    for field in ["app_name", "bundle_id", "process_id", "window_title"]:
        if field not in expected:
            failures.append(
                "data/capture/macos_frontmost_snapshot.json expected is missing "
                f"{field}"
            )


def check_live_observation_harness(failures: list[str]) -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    script = ROOT / "scripts/harness/observe-live.sh"
    if "observe-live:" not in makefile:
        failures.append("Makefile must expose make observe-live for manual sensor diagnostics")
    if not script.is_file():
        failures.append("missing scripts/harness/observe-live.sh")
        return
    text = script.read_text(encoding="utf-8")
    for phrase in ["capture-macos", "live-capture-events.jsonl", "live-capture.log"]:
        if phrase not in text:
            failures.append(f"scripts/harness/observe-live.sh must mention {phrase}")


def check_ui_harness(failures: list[str]) -> None:
    required_paths = [
        "web/index.html",
        "web/styles.css",
        "web/app.js",
        "scripts/product/start-ui.sh",
        "scripts/product/validate-ui.sh",
        "scripts/harness/runtime-log.py",
        "scripts/harness/diagnose.sh",
    ]
    for path in required_paths:
        if not (ROOT / path).is_file():
            failures.append(f"missing {path}; keep the UI shell runnable by Codex")

    validate = ROOT / "scripts/product/validate-ui.sh"
    if validate.is_file():
        text = validate.read_text(encoding="utf-8")
        for phrase in [
            "ui-validation.txt",
            "ui-validation.json",
            "ui-snapshot.html",
            "activity-summary.json",
            "capture-summary.json",
        ]:
            if phrase not in text:
                failures.append(f"scripts/product/validate-ui.sh must mention {phrase}")

    observe = ROOT / "scripts/harness/observe.sh"
    if observe.is_file() and "events.jsonl" not in observe.read_text(encoding="utf-8"):
        failures.append("scripts/harness/observe.sh must expose structured events.jsonl")

    diagnose = ROOT / "scripts/harness/diagnose.sh"
    if diagnose.is_file():
        text = diagnose.read_text(encoding="utf-8")
        for phrase in ["app-status.sh", "events.jsonl", "ui-validation.txt"]:
            if phrase not in text:
                failures.append(f"scripts/harness/diagnose.sh must mention {phrase}")


def check_live_capture_contract(failures: list[str]) -> None:
    """Keep privacy-sensitive live-capture policy visible to future agents."""
    required_docs = {
        "docs/product/live-capture.md": [
            "NSWorkspace",
            "Accessibility",
            "browser adapters",
            "ScreenCaptureKit",
            "Vision OCR",
            "No keylogging",
            "Raw screenshots are disabled by default",
            "ActivityEvent",
        ],
        "docs/product/on-device-inference.md": [
            "rules first",
            "Foundation Models",
            "Core ML",
            "MLX",
            "local-only",
            "confidence",
            "evaluation",
        ],
        "docs/SECURITY.md": [
            "No keylogging",
            "Raw screenshots are disabled by default",
            "Screen Recording",
            "Accessibility permission",
            "local-only",
        ],
    }

    for relative_path, required_phrases in required_docs.items():
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing {relative_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in required_phrases:
            if phrase not in text:
                failures.append(
                    f"{relative_path} must mention {phrase!r} to preserve the "
                    "live-capture privacy and inference contract"
                )


def check_parallel_plan_contract(failures: list[str]) -> None:
    """Validate multi-agent plans have a tracker and disjoint ownership."""
    base = ROOT / "docs/plans/parallel/macos-live-capture"
    tracker = base / "TRACKER.md"
    task_files = [
        base / "agent-1-capture-core.md",
        base / "agent-2-browser-redaction.md",
        base / "agent-3-replay-runtime.md",
    ]

    if not tracker.is_file():
        failures.append("missing docs/plans/parallel/macos-live-capture/TRACKER.md")
        return

    tracker_text = tracker.read_text(encoding="utf-8")
    for required in [
        "Integration Contract",
        "Merge Order",
        "Shared Interfaces",
        "Coordination Rules",
        "Agent 1",
        "Agent 2",
        "Agent 3",
    ]:
        if required not in tracker_text:
            failures.append(
                "docs/plans/parallel/macos-live-capture/TRACKER.md must "
                f"mention {required!r}"
            )

    ownership: dict[str, str] = {}
    required_sections = [
        "## Objective",
        "## Owned Files",
        "## Inputs",
        "## Required Implementation",
        "## Out of Scope",
        "## Verification",
        "## Handoff",
    ]
    for task in task_files:
        if not task.is_file():
            failures.append(f"missing {task.relative_to(ROOT)}")
            continue
        text = task.read_text(encoding="utf-8")
        for section in required_sections:
            if section not in text:
                failures.append(f"{task.relative_to(ROOT)} is missing {section}")
        owned = extract_owned_files(text)
        if not owned:
            failures.append(f"{task.relative_to(ROOT)} must list owned files")
        for path in owned:
            previous = ownership.get(path)
            if previous:
                failures.append(
                    f"parallel ownership conflict: {path} is owned by both "
                    f"{previous} and {task.relative_to(ROOT)}"
                )
            ownership[path] = str(task.relative_to(ROOT))


def extract_owned_files(text: str) -> list[str]:
    owned: list[str] = []
    in_section = False
    for line in text.splitlines():
        if line == "## Owned Files":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section or not line.startswith("- `"):
            continue
        end = line.find("`", 3)
        if end != -1:
            owned.append(line[3:end])
    return owned


def check_labeled_fixture(
    failures: list[str], path: Path, required_labels: set[str], minimum: int
) -> None:
    if not path.is_file():
        failures.append(f"missing {path.relative_to(ROOT)}")
        return

    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"{path.relative_to(ROOT)} is invalid JSON: {exc}")
        return

    if not isinstance(rows, list) or len(rows) < minimum:
        failures.append(
            f"{path.relative_to(ROOT)} must contain at least {minimum} labeled examples"
        )
        return

    labels = {row.get("expected_label") for row in rows if isinstance(row, dict)}
    for required in sorted(required_labels):
        if required not in labels:
            failures.append(
                f"{path.relative_to(ROOT)} must include at least one {required} example"
            )


if __name__ == "__main__":
    raise SystemExit(main())
