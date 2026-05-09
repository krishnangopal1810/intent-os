"""Focused harness lint checks."""

from __future__ import annotations

import ast

from .common import ROOT, import_targets


def check_public_harness_commands(failures: list[str]) -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    required_targets = {
        "new-feature:": "scripts/harness/new-feature.sh",
        "adapter-fixture-check:": "scripts/harness/adapter-fixture-check.py",
        "chrome-bridge-smoke:": "scripts/product/chrome-bridge-smoke.sh",
        "diagnose-json:": "scripts/harness/diagnose-json.py",
        "feedback-fixture-candidates:": "scripts/harness/feedback-fixture-candidates.py",
        "package-onboarding-check:": "scripts/harness/package-onboarding-check.py",
        "cohort-evidence-check:": "scripts/harness/cohort-evidence-check.py",
        "review-status:": "scripts/harness/review-status.py",
    }
    for target, script in required_targets.items():
        if target not in makefile:
            failures.append(f"Makefile must expose {target}")
        path = ROOT / script
        if not path.is_file():
            failures.append(f"missing harness command {script}")
        elif not path.stat().st_mode & 0o111:
            failures.append(f"{script} must be executable")

    verify = ROOT / "scripts/product/verify.sh"
    if verify.is_file():
        verify_text = verify.read_text(encoding="utf-8")
        for phrase in [
            "adapter-fixture-check.py",
            "package-onboarding-check.py",
            "cohort-evidence-check.py",
        ]:
            if phrase not in verify_text:
                failures.append(f"scripts/product/verify.sh must run {phrase}")

    docs = {
        "docs/APP_RUNTIME.md": [
            "make new-feature",
            "make adapter-fixture-check",
            "make chrome-bridge-smoke",
            "make diagnose-json",
            "make feedback-fixture-candidates",
            "make package-onboarding-check",
            "make cohort-evidence-check",
            "make review-status",
        ],
        "docs/OPERATING_MODEL.md": ["make review-status", "make diagnose-json"],
        "docs/QUALITY.md": [
            "adapter fixture manifest",
            "installed Chrome bridge smoke",
            "cohort evidence",
        ],
    }
    for relative_path, phrases in docs.items():
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing {relative_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                failures.append(f"{relative_path} must mention {phrase!r}")


def check_architecture_flow_rules(failures: list[str]) -> None:
    rules = [
        (
            "capture adapters must not classify or report",
            sorted((ROOT / "intentos/capture").glob("*.py")),
            ("intentos.classifier", "intentos.reporting", "intentos.beta"),
        ),
        (
            "classifiers must not call live sensors or beta runtime",
            [ROOT / "intentos/classifier.py", ROOT / "intentos/classifier_context.py"],
            ("intentos.capture", "intentos.beta"),
        ),
        (
            "reports must not bypass normalized events",
            [ROOT / "intentos/reporting.py"],
            ("intentos.capture", "intentos.beta"),
        ),
    ]
    for message, paths, forbidden_prefixes in rules:
        for path in paths:
            if not path.is_file():
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported = import_targets(tree)
            forbidden = sorted(
                target
                for target in imported
                if any(target == prefix or target.startswith(prefix + ".") for prefix in forbidden_prefixes)
            )
            if forbidden:
                failures.append(
                    f"{path.relative_to(ROOT)} violates flow rule: {message}; "
                    f"remove {', '.join(forbidden)}"
                )

    store_path = ROOT / "intentos/beta/store.py"
    if store_path.is_file() and "UPDATE ACTIVITY_EVENTS" in store_path.read_text(encoding="utf-8").upper():
        failures.append(
            "intentos/beta/store.py must not UPDATE activity_events; corrections must layer over raw events"
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


def check_next_feature_harness_contract(failures: list[str]) -> None:
    """Keep upcoming feature harness requirements explicit and indexed."""
    required_docs = {
        "docs/HARNESS_FEATURES.md": [
            "Manual real-data import",
            "not the preferred roadmap",
            "Browser history import",
            "ChatGPT export parser",
            "Daily behavior narratives",
            "ScreenCaptureKit and Vision OCR fallback",
            "Local model second-pass classifier",
            "Richer DOM automation",
            "Universal Use-Case Classes",
            "New data source or adapter",
            "New permissioned live capability",
            "New long-running process",
            "New export or integration",
            "Completion Checklist",
            "Harness Impact",
            "make verify",
            "deterministic fixtures",
            "structured runtime events",
            "privacy exclusions",
        ],
        "docs/product/imports.md": [
            "Manual CSV/JSON Fixture Import",
            "Browser History Fixtures",
            "ChatGPT Parser Fixtures",
            "ActivityEvent",
            "import-events.jsonl",
            "import-validation.json",
            "Privacy Rules",
            "Verification",
        ],
        "docs/NEXT_STEPS.md": [
            "Automated background timeline",
            "HARNESS_FEATURES.md",
            "Browser extension capture",
            "Calendar or planned-intent integration",
            "Accessibility visible-text excerpts",
            "ScreenCaptureKit",
            "Local model second-pass classifier",
        ],
        "docs/APP_RUNTIME.md": [
            "Future Feature Runtime Contract",
            "automated background timeline",
            "deterministic fixtures",
            "HARNESS_FEATURES.md",
            "Harness Impact",
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
                    f"{relative_path} must mention {phrase!r} for next-feature "
                    "harness readiness"
                )

    timeline_plan = ROOT / "docs/plans/active/2026-04-27-automated-background-timeline.md"
    if timeline_plan.is_file():
        text = timeline_plan.read_text(encoding="utf-8")
        for phrase in [
            "HARNESS_FEATURES.md",
            "live-capture-timeline-events.jsonl",
            "deterministic tests",
            "structured runtime events",
            "privacy",
        ]:
            if phrase not in text:
                failures.append(
                    f"{timeline_plan.relative_to(ROOT)} must mention {phrase!r} "
                    "before background timeline implementation starts"
                )
