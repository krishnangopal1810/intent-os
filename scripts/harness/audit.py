#!/usr/bin/env python3
"""Repository drift audit for agent-first maintenance."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    failures: list[str] = []
    check_stale_plans(failures)
    check_stale_docs(failures)
    check_fixture_drift(failures)
    check_ui_shell(failures)
    check_quality_gaps(failures)

    if failures:
        for failure in failures:
            print(f"harness-audit: {failure}", file=sys.stderr)
        return 1

    print("harness-audit: ok")
    return 0


def check_stale_plans(failures: list[str]) -> None:
    active_dir = ROOT / "docs/plans/active"
    completed_dir = ROOT / "docs/plans/completed"

    for path in sorted(active_dir.glob("*.md")):
        text = read(path)
        if "Status: Completed" in text:
            failures.append(
                f"{rel(path)} is completed but still active; move it to "
                "docs/plans/completed/"
            )
        for section in ["## Scope", "## Acceptance Criteria", "## Verification", "## Progress Log"]:
            if section not in text:
                failures.append(f"{rel(path)} is missing {section}")

    for path in sorted(completed_dir.glob("*.md")):
        text = read(path)
        if "Status: Completed" not in text:
            failures.append(f"{rel(path)} is in completed plans but is not marked completed")
        if "## Verification" not in text:
            failures.append(f"{rel(path)} should preserve verification evidence")


def check_stale_docs(failures: list[str]) -> None:
    stale_phrases = {
        "There is no live capture yet": "manual macOS frontmost capture now exists",
        "Live capture and UI are not implemented yet": "manual macOS frontmost capture now exists",
        "Live multi-app capture is not implemented": "manual macOS frontmost capture now exists",
        "`make dev` is fixture-only": (
            "make dev builds fixture artifacts and then starts the visible "
            "background metadata sampler"
        ),
        "make dev is fixture-only": (
            "make dev builds fixture artifacts and then starts the visible "
            "background metadata sampler"
        ),
        "It does not capture current macOS activity": (
            "make dev starts the visible background metadata sampler after "
            "fixture artifacts are built"
        ),
        "The planned live capture slice is metadata-first": (
            "metadata-first live capture has shipped through manual commands "
            "and the visible background sampler"
        ),
        "The current product processes local fixture data only": (
            "manual live commands and the make dev background sampler can "
            "process local macOS metadata"
        ),
        "live macOS capture, or external network calls": (
            "manual live commands and the make dev background sampler can "
            "process local macOS metadata"
        ),
        "No product UI has been specified yet": "the local UI shell now exists",
        "browser screenshot automation are not implemented": "checked-in screenshot evidence now exists",
        "browser screenshot validation remain future extensions": "checked-in screenshot evidence now exists",
        "when browser metadata capture lands": (
            "browser active-tab metadata capture now exists; refer to future "
            "metadata adapters instead"
        ),
        "Add cleanup/audit scripts that scan stale plans, stale docs, fixture drift": (
            "cleanup/audit scripts now exist; describe expanding them instead"
        ),
        "Expand cleanup/audit scripts so stale plans, stale docs, fixture drift": (
            "cleanup/audit scripts now exist; describe keeping or extending "
            "them current instead"
        ),
    }

    doc_paths = sorted((ROOT / "docs").rglob("*.md")) + [ROOT / "README.md"]
    for path in doc_paths:
        text = read(path)
        for phrase, reason in stale_phrases.items():
            if phrase in text:
                failures.append(f"{rel(path)} contains stale phrase {phrase!r}; {reason}")

    required_doc_phrases = {
        "README.md": ["make dev-live", "make observe-live", "make observe-session", "Manual metadata-only macOS"],
        "docs/APP_RUNTIME.md": [
            "make validate-ui",
            "make dev-live",
            "make observe-live",
            "make observe-session",
            "make update-ui-screenshot",
            "structured",
            "local app shell",
        ],
        "docs/HARNESS_AUDIT.md": [
            "local app shell",
            "deterministic capture fixtures",
            "structured",
            "cleanup/audit scripts",
            "docs/HARNESS_FEATURES.md",
        ],
        "docs/HARNESS_FEATURES.md": [
            "Manual real-data import",
            "Browser history import",
            "ChatGPT export parser",
            "ScreenCaptureKit and Vision OCR fallback",
            "Local model second-pass classifier",
            "Richer DOM automation",
        ],
        "docs/NEXT_STEPS.md": [
            "Manual real-data import",
            "HARNESS_FEATURES.md",
            "product/imports.md",
            "Harness Upgrades To Keep Current",
            "stale plans",
            "fixture drift",
            "quality scorecard gaps",
        ],
        "docs/RELIABILITY.md": [
            "make dev-live",
            "make observe-live",
            "make observe-session",
            "make check-ui-screenshot",
            "structured",
            "ui-validation.json",
        ],
        "docs/DESIGN.md": ["IntentOS UI shell", "daily behavior review"],
        "docs/product/imports.md": [
            "Manual CSV/JSON Import",
            "Browser History Import",
            "ChatGPT Export Parser",
            "Privacy Rules",
        ],
    }
    for relative_path, phrases in required_doc_phrases.items():
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing {relative_path}")
            continue
        text = read(path)
        for phrase in phrases:
            if phrase not in text:
                failures.append(f"{relative_path} must mention {phrase!r}")


def check_fixture_drift(failures: list[str]) -> None:
    valid_json: dict[Path, object] = {}
    for path in sorted((ROOT / "data").rglob("*.json")):
        try:
            valid_json[path] = json.loads(read(path))
        except json.JSONDecodeError as exc:
            failures.append(f"{rel(path)} is invalid JSON: {exc}")

    required_fixtures = [
        "data/activity/evaluation_set.json",
        "data/activity/multi_app_events.json",
        "data/capture/fake_browser_tabs.json",
        "data/capture/fake_macos_observations.json",
        "data/capture/fake_session_observations.json",
        "data/capture/browser_active_tab_snapshot.json",
        "data/capture/macos_frontmost_snapshot.json",
        "data/capture/privacy_policy.json",
        "data/youtube/evaluation_set.json",
        "data/youtube/sample_watch_history.json",
    ]
    for relative_path in required_fixtures:
        if not (ROOT / relative_path).is_file():
            failures.append(f"missing required fixture {relative_path}")

    macos_fixture = ROOT / "data/capture/macos_frontmost_snapshot.json"
    if macos_fixture in valid_json:
        fixture = valid_json[macos_fixture]
        if not isinstance(fixture, dict):
            failures.append(f"{rel(macos_fixture)} must be a JSON object")
            return
        stdout = fixture.get("stdout", "")
        expected = fixture.get("expected", {})
        lines = stdout.splitlines()
        if len(lines) < 4:
            failures.append(f"{rel(macos_fixture)} stdout must contain four lines")
        elif isinstance(expected, dict):
            comparisons = {
                "app_name": lines[0],
                "bundle_id": lines[1],
                "process_id": int(lines[2]) if lines[2].isdigit() else lines[2],
                "window_title": lines[3],
            }
            for field, value in comparisons.items():
                if expected.get(field) != value:
                    failures.append(
                        f"{rel(macos_fixture)} expected.{field} does not match stdout"
                    )

    browser_fixture = ROOT / "data/capture/browser_active_tab_snapshot.json"
    if browser_fixture in valid_json:
        fixture = valid_json[browser_fixture]
        if not isinstance(fixture, dict):
            failures.append(f"{rel(browser_fixture)} must be a JSON object")
            return
        stdout = fixture.get("stdout", "")
        expected = fixture.get("expected", {})
        lines = stdout.splitlines()
        if len(lines) < 2:
            failures.append(f"{rel(browser_fixture)} stdout must contain two lines")
        elif isinstance(expected, dict):
            if expected.get("title") != lines[0]:
                failures.append(f"{rel(browser_fixture)} expected.title does not match stdout")
            if expected.get("url") != lines[1]:
                failures.append(f"{rel(browser_fixture)} expected.url does not match stdout")


def check_ui_shell(failures: list[str]) -> None:
    required_files = [
        "web/index.html",
        "web/styles.css",
        "web/app.js",
        "scripts/product/start-ui.sh",
        "scripts/product/validate-ui.sh",
        "scripts/product/render-ui-check.py",
        "scripts/product/update-ui-screenshot.sh",
        "scripts/product/check-ui-screenshot.sh",
        "docs/assets/screenshots/intent-os-ui.png",
        "docs/assets/screenshots/intent-os-ui.json",
        "scripts/harness/runtime-log.py",
        "scripts/harness/diagnose.sh",
    ]
    for relative_path in required_files:
        if not (ROOT / relative_path).is_file():
            failures.append(f"missing UI harness file {relative_path}")

    app_html = ROOT / "web/index.html"
    if app_html.is_file():
        text = read(app_html)
        for phrase in ["data-ui-root", "IntentOS", "Behavior reports"]:
            if phrase not in text:
                failures.append(f"web/index.html must mention {phrase!r}")

    app_js = ROOT / "web/app.js"
    if app_js.is_file():
        text = read(app_js)
        for phrase in [
            "activity-summary.json",
            "capture-summary.json",
            "session-capture-summary.json",
            "live-session-capture-summary.json",
            "live-capture-summary.json",
            "youtube-summary.json",
        ]:
            if phrase not in text:
                failures.append(f"web/app.js must load {phrase}")

    validate = ROOT / "scripts/product/validate-ui.sh"
    if validate.is_file():
        text = read(validate)
        for phrase in ["ui-validation.json", "ui-snapshot.html", "runtime-log.py"]:
            if phrase not in text:
                failures.append(f"scripts/product/validate-ui.sh must mention {phrase}")


def check_quality_gaps(failures: list[str]) -> None:
    path = ROOT / "docs/QUALITY.md"
    if not path.is_file():
        failures.append("missing docs/QUALITY.md")
        return

    text = read(path)
    if "## Known Gaps" not in text:
        failures.append("docs/QUALITY.md must include ## Known Gaps")
    if "## Cleanup Process" not in text:
        failures.append("docs/QUALITY.md must include ## Cleanup Process")
    if "Live multi-app capture is not implemented" in text:
        failures.append(
            "docs/QUALITY.md has a stale live-capture gap; manual macOS capture exists"
        )
    for area in ["Product definition", "Architecture", "Verification", "Security", "Reliability", "UX"]:
        if f"| {area} |" not in text:
            failures.append(f"docs/QUALITY.md is missing scorecard area {area}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
