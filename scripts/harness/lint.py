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
PYTHON_DISCOVERY_ROOTS = ("intentos", "tests")
EXPECTED_LAYERS = {
    "intentos/__init__.py",
    "intentos/activity.py",
    "intentos/classifier.py",
    "intentos/classifier_context.py",
    "intentos/reporting.py",
    "intentos/activity_cli.py",
    "intentos/activity_evaluate.py",
    "intentos/beta/__init__.py",
    "intentos/beta/daily_loop.py",
    "intentos/beta/daily_state.py",
    "intentos/beta/db_health.py",
    "intentos/beta/extension.py",
    "intentos/beta/focus_rescue.py",
    "intentos/beta/keys.py",
    "intentos/beta/loop_coach.py",
    "intentos/beta/native_recorder.py",
    "intentos/beta/permissions.py",
    "intentos/beta/recorder.py",
    "intentos/beta/review.py",
    "intentos/beta/schema.py",
    "intentos/beta/service.py",
    "intentos/beta/service_helpers.py",
    "intentos/beta/service_security.py",
    "intentos/beta/setup_diagnostics.py",
    "intentos/beta/setup_flow.py",
    "intentos/beta/state.py",
    "intentos/beta/store.py",
    "intentos/beta/weekly_patterns.py",
    "intentos/beta_cli.py",
    "intentos/capture/__init__.py",
    "intentos/capture/browser.py",
    "intentos/capture/core.py",
    "intentos/capture/jsonl.py",
    "intentos/capture/live.py",
    "intentos/capture/live_cli.py",
    "intentos/capture/macos.py",
    "intentos/capture/privacy.py",
    "intentos/capture/report_cli.py",
    "intentos/capture/session.py",
    "intentos/capture_cli.py",
    "intentos/capture_replay.py",
    "intentos/youtube.py",
    "intentos/cli.py",
    "intentos/evaluate.py",
    "tests/test_activity_classification.py",
    "tests/test_beta_activation.py",
    "tests/test_beta_daily_loop.py",
    "tests/test_beta_extension.py",
    "tests/test_beta_menu_app.py",
    "tests/test_beta_native_recorder.py",
    "tests/test_beta_permissions.py",
    "tests/test_beta_service.py",
    "tests/test_beta_store.py",
    "tests/test_capture_browser.py",
    "tests/test_capture_cli.py",
    "tests/test_capture_core.py",
    "tests/test_capture_live.py",
    "tests/test_capture_macos.py",
    "tests/test_capture_privacy.py",
    "tests/test_capture_replay.py",
    "tests/test_capture_session.py",
    "tests/test_harness_completion.py",
    "tests/test_render_ui_check.py",
    "tests/test_youtube_mvp.py",
}
ALLOWED_IMPORTS = {
    "intentos/__init__.py": set(),
    "intentos/cli.py": {"intentos.youtube"},
    "intentos/evaluate.py": {"intentos.youtube"},
    "intentos/classifier.py": {"intentos.activity", "intentos.classifier_context"},
    "intentos/classifier_context.py": {"intentos.activity"},
    "intentos/reporting.py": {
        "intentos.activity",
        "intentos.classifier",
        "intentos.youtube",
    },
    "intentos/activity_cli.py": {"intentos.activity", "intentos.reporting"},
    "intentos/activity_evaluate.py": {"intentos.activity", "intentos.classifier"},
    "intentos/beta/__init__.py": set(),
    "intentos/beta/daily_loop.py": {
        "intentos.beta",
        "intentos.youtube",
    },
    "intentos/beta/daily_state.py": {
        "intentos.beta",
    },
    "intentos/beta/db_health.py": set(),
    "intentos/beta/extension.py": {
        "intentos.activity",
        "intentos.capture.browser",
        "intentos.capture.privacy",
    },
    "intentos/beta/focus_rescue.py": {
        "intentos.beta",
        "intentos.youtube",
    },
    "intentos/beta/keys.py": set(),
    "intentos/beta/loop_coach.py": {
        "intentos.youtube",
    },
    "intentos/beta/native_recorder.py": {
        "intentos.activity",
        "intentos.beta",
        "intentos.capture.live",
        "intentos.capture.macos",
    },
    "intentos/beta/permissions.py": {
        "intentos.beta",
        "intentos.capture",
    },
    "intentos/beta/recorder.py": {
        "intentos.activity",
        "intentos.beta",
        "intentos.capture.core",
        "intentos.capture.session",
    },
    "intentos/beta/review.py": {
        "intentos.activity",
        "intentos.beta",
        "intentos.beta.keys",
        "intentos.classifier",
        "intentos.reporting",
        "intentos.youtube",
    },
    "intentos/beta/schema.py": set(),
    "intentos/beta/service.py": {
        "intentos.beta",
        "intentos.beta.extension",
        "intentos.beta.service_helpers",
        "intentos.capture.privacy",
    },
    "intentos/beta/service_helpers.py": set(),
    "intentos/beta/service_security.py": set(),
    "intentos/beta/setup_diagnostics.py": {
        "intentos.beta",
    },
    "intentos/beta/setup_flow.py": {
        "intentos.beta",
    },
    "intentos/beta/state.py": {
        "intentos.beta",
    },
    "intentos/beta/store.py": {
        "intentos.beta.db_health",
        "intentos.beta.keys",
        "intentos.beta.schema",
        "intentos.beta",
        "intentos.activity",
        "intentos.classifier",
        "intentos.reporting",
    },
    "intentos/beta/weekly_patterns.py": {
        "intentos.beta",
        "intentos.youtube",
    },
    "intentos/beta_cli.py": {
        "intentos.beta",
        "intentos.beta.extension",
        "intentos.beta.service",
        "intentos.capture.privacy",
    },
    "intentos/capture/__init__.py": {
        "intentos.capture.core",
        "intentos.capture.jsonl",
    },
    "intentos/capture/browser.py": set(),
    "intentos/capture/core.py": {"intentos.activity"},
    "intentos/capture/jsonl.py": {"intentos.activity"},
    "intentos/capture/live.py": {
        "intentos.activity",
        "intentos.capture.browser",
        "intentos.capture.core",
        "intentos.capture.jsonl",
        "intentos.capture.macos",
        "intentos.capture.privacy",
        "intentos.capture.session",
        "intentos.capture_replay",
    },
    "intentos/capture/live_cli.py": {
        "intentos.capture.live",
        "intentos.capture.macos",
    },
    "intentos/capture/macos.py": {"intentos.capture.core"},
    "intentos/capture/privacy.py": set(),
    "intentos/capture/report_cli.py": set(),
    "intentos/capture/session.py": {
        "intentos.activity",
        "intentos.capture.browser",
        "intentos.capture.core",
        "intentos.capture.macos",
    },
    "intentos/capture_replay.py": {"intentos.capture.jsonl", "intentos.reporting"},
    "intentos/capture_cli.py": {
        "intentos.capture.browser",
        "intentos.capture.core",
        "intentos.capture.jsonl",
        "intentos.capture.privacy",
        "intentos.capture.live_cli",
        "intentos.capture.macos",
        "intentos.capture.report_cli",
        "intentos.capture.session",
        "intentos.capture_replay",
    },
    "tests/test_activity_classification.py": {
        "intentos.activity",
        "intentos.activity_evaluate",
        "intentos.classifier",
        "intentos.reporting",
    },
    "tests/test_beta_activation.py": {
        "intentos.beta",
    },
    "tests/test_beta_daily_loop.py": {
        "intentos.activity",
        "intentos.beta",
    },
    "tests/test_beta_extension.py": {
        "intentos.beta.extension",
        "intentos.capture.privacy",
    },
    "tests/test_beta_menu_app.py": set(),
    "tests/test_beta_native_recorder.py": {
        "intentos.activity",
        "intentos.beta",
    },
    "tests/test_beta_permissions.py": {
        "intentos.beta",
    },
    "tests/test_beta_service.py": {
        "intentos.beta",
        "intentos.beta.service",
    },
    "tests/test_beta_store.py": {
        "intentos.activity",
        "intentos.beta",
    },
    "tests/test_capture_browser.py": {"intentos.capture.browser"},
    "tests/test_capture_cli.py": {
        "intentos.capture.browser",
        "intentos.capture.macos",
        "intentos.capture_cli",
    },
    "tests/test_capture_core.py": {
        "intentos.capture.core",
        "intentos.capture.jsonl",
    },
    "tests/test_capture_live.py": {
        "intentos.capture.browser",
        "intentos.capture.jsonl",
        "intentos.capture.live",
        "intentos.capture.macos",
    },
    "tests/test_capture_macos.py": {"intentos.capture.macos"},
    "tests/test_capture_privacy.py": {"intentos.capture.privacy"},
    "tests/test_capture_replay.py": {
        "intentos.capture_cli",
        "intentos.capture_replay",
    },
    "tests/test_capture_session.py": {
        "intentos.capture.browser",
        "intentos.capture.core",
        "intentos.capture.jsonl",
        "intentos.capture.macos",
        "intentos.capture.session",
        "intentos.capture_cli",
        "intentos.capture_replay",
    },
    "tests/test_harness_completion.py": {
        "intentos.activity",
        "intentos.beta",
    },
    "tests/test_render_ui_check.py": set(),
    "tests/test_youtube_mvp.py": {"intentos.youtube"},
}


def main() -> int:
    failures: list[str] = []
    check_required_python_files(failures)
    check_python_syntax_and_imports(failures)
    check_file_sizes(failures)
    check_generated_files_not_tracked(failures)
    check_no_stale_active_plans(failures)
    check_public_harness_commands(failures)
    check_architecture_flow_rules(failures)
    check_quality_scorecard(failures)
    check_evaluation_set(failures)
    check_capture_adapter_fixtures(failures)
    check_live_observation_harness(failures)
    check_ui_harness(failures)
    check_live_capture_contract(failures)
    check_beta_harness_contract(failures)
    check_next_feature_harness_contract(failures)
    check_parallel_plan_contract(failures)

    if failures:
        for failure in failures:
            print(f"harness-lint: {failure}", file=sys.stderr)
        return 1

    print("harness-lint: ok")
    return 0


def check_required_python_files(failures: list[str]) -> None:
    discovered = discover_python_files()
    for path in sorted(discovered - EXPECTED_LAYERS):
        failures.append(
            f"unregistered Python file {path}; add it to EXPECTED_LAYERS and "
            "ALLOWED_IMPORTS so architecture and size checks apply"
        )
    for path in sorted(EXPECTED_LAYERS):
        if not (ROOT / path).is_file():
            failures.append(
                f"missing {path}; keep the MVP layer map in docs/ARCHITECTURE.md "
                "and scripts/harness/lint.py aligned"
            )


def discover_python_files() -> set[str]:
    paths: set[str] = set()
    for root_name in PYTHON_DISCOVERY_ROOTS:
        for path in (ROOT / root_name).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            paths.add(str(path.relative_to(ROOT)))
    return paths


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
        if "## Harness Impact" not in text:
            failures.append(
                f"{plan.relative_to(ROOT)} must include ## Harness Impact so "
                "future runtime, fixture, UI, diagnostics, and privacy work is explicit"
            )
        if "## Acceptance Criteria" not in text:
            failures.append(
                f"{plan.relative_to(ROOT)} must include ## Acceptance Criteria so "
                "implementation and review have a concrete completion gate"
            )
        else:
            for phrase in [
                "Runtime commands and artifacts",
                "Fixtures or fakes",
                "UI validation",
                "Structured logs",
                "Privacy, permission",
                "Docs or harness checks",
            ]:
                if phrase not in text:
                    failures.append(
                        f"{plan.relative_to(ROOT)} Harness Impact must mention {phrase!r}"
                    )


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


def check_ui_harness(failures: list[str]) -> None:
    required_paths = [
        "web/index.html",
        "web/styles.css",
        "web/app.js",
        "scripts/product/start-ui.sh",
        "scripts/product/validate-ui.sh",
        "scripts/product/inject-ui-render-probe.py",
        "scripts/product/ui-render-probe.js",
        "scripts/product/render-ui-browser.py",
        "scripts/product/render-ui-check.py",
        "scripts/product/update-ui-screenshot.sh",
        "scripts/product/check-ui-screenshot.sh",
        "scripts/product/ui-screenshot-manifest.py",
        "data/ui/visible_copy_policy.json",
        "docs/assets/screenshots/intent-os-ui.png",
        "docs/assets/screenshots/intent-os-ui.json",
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
            "ui-render-validation.txt",
            "ui-render-mobile-validation.txt",
            "render-ui-check.py",
            "inject-ui-render-probe.py",
            "fixture-long-text",
            "check-ui-screenshot.sh",
            "data-action-deck",
            "data-next-move-title",
            "data-coach-hero",
            "data-weekly-details",
            "data-daily-loop",
            "data-intent-form",
            "data-intent-contract",
            "data-service-notice",
            "data-review-form",
            "activity-summary.json",
            "capture-summary.json",
            "session-capture-summary.json",
            "live-session-capture-summary.json",
            "live-capture-summary.json",
        ]:
            if phrase not in text:
                failures.append(f"scripts/product/validate-ui.sh must mention {phrase}")

    render_probe = ROOT / "scripts/product/ui-render-probe.js"
    if render_probe.is_file():
        text = render_probe.read_text(encoding="utf-8")
        for phrase in [
            "default_density",
            "copy_policy",
            "first_viewport",
            "coach_hero_present",
            "weekly_details_present",
            "intent_preview",
            "service_state",
            "visible_decision_cards",
            "cut_off_text_count",
            "evidence_open_after_activity",
            "workflowProbe",
            "evening_receipt_present",
            "onboarding_step_count",
            "browser_detail_action_visible",
        ]:
            if phrase not in text:
                failures.append(f"scripts/product/ui-render-probe.js must emit UX probe {phrase!r}")

    render_checker = ROOT / "scripts/product/render-ui-check.py"
    if render_checker.is_file():
        text = render_checker.read_text(encoding="utf-8")
        for phrase in [
            "default_density",
            "schema_version",
            "copy_policy",
            "first_viewport",
            "coach_hero_present",
            "weekly_details_present",
            "intent_preview",
            "service_state",
            "visible_decision_cards",
            "cut_off_text_count",
            "evidence_open_after_activity",
            "visible_word_count",
            "evening_receipt_present",
            "onboarding_step_count",
            "capture_preview_state",
        ]:
            if phrase not in text:
                failures.append(f"scripts/product/render-ui-check.py must enforce UX probe {phrase!r}")

    makefile = ROOT / "Makefile"
    if makefile.is_file():
        makefile_text = makefile.read_text(encoding="utf-8")
        for phrase in ["update-ui-screenshot:", "check-ui-screenshot:"]:
            if phrase not in makefile_text:
                failures.append(f"Makefile must expose {phrase}")

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


def check_beta_harness_contract(failures: list[str]) -> None:
    """Keep the dogfood beta runnable, inspectable, and local-only."""
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in [
        "beta-dev:",
        "beta-status:",
        "beta-stop:",
        "validate-beta:",
        "package-beta:",
        "install-beta-app:",
        "package-extension:",
    ]:
        if target not in makefile:
            failures.append(f"Makefile must expose {target}")
    if "dogfood-smoke:" not in makefile:
        failures.append("Makefile must expose dogfood-smoke:")

    required_paths = [
        "intentos/beta/store.py",
        "intentos/beta/db_health.py",
        "intentos/beta/service.py",
        "intentos/beta/state.py",
        "intentos/beta/permissions.py",
        "intentos/beta/extension.py",
        "intentos/beta/native_recorder.py",
        "intentos/beta/recorder.py",
        "intentos/beta/review.py",
        "intentos/beta/service_security.py",
        "intentos/beta/setup_diagnostics.py",
        "intentos/beta_cli.py",
        "scripts/harness/beta-dev.sh",
        "scripts/harness/beta-status.sh",
        "scripts/harness/beta-stop.sh",
        "scripts/product/validate-beta.sh",
        "scripts/product/package-beta.sh",
        "scripts/product/package-onboarding-beta.sh",
        "scripts/product/install-beta-app.sh",
        "scripts/product/package-extension.sh",
        "scripts/harness/package-onboarding-check.py",
        "scripts/harness/cohort-evidence-check.py",
        "data/beta/cohort_evidence_template.json",
        "scripts/product/dogfood-smoke.sh",
        "data/beta/fake_chrome_events.json",
        "extension/chrome/background.js",
        "extension/chrome/content.js",
        "extension/chrome/manifest.json",
        "macos/IntentOSBeta/IntentOSBeta.swift",
        ".github/workflows/trusted-beta-artifact.yml",
    ]
    for path in required_paths:
        if not (ROOT / path).is_file():
            failures.append(f"missing beta harness file {path}")

    validate_beta = ROOT / "scripts/product/validate-beta.sh"
    if validate_beta.is_file():
        text = validate_beta.read_text(encoding="utf-8")
        for phrase in [
            "inject-ui-render-probe.py",
            "--workflow",
            "render-ui-browser.py",
            "beta-ready",
            "beta-service-stale",
            "beta-empty",
            "beta-intent-missing",
            "beta-setup-needed",
            "evening_receipt",
            "first_live_state_at",
        ]:
            if phrase not in text:
                failures.append(
                    f"scripts/product/validate-beta.sh must include beta UI UX probe {phrase!r}"
                )
        for phrase in [
            "--api-token",
            "--allowed-origin",
            "X-IntentOS-Token",
            '"apiToken": "$api_token"',
            "sticky_loop_future_correction",
            "apply_to_future correction did not match a future segment key",
            "apply_to_future correction matched an unrelated same-domain segment",
            'config_for_artifact["apiToken"] = "<redacted>"',
        ]:
            if phrase not in text:
                failures.append(
                    "scripts/product/validate-beta.sh must lock and verify the "
                    f"authenticated beta API path with phrase {phrase!r}"
                )

    package_check = ROOT / "scripts/harness/package-onboarding-check.py"
    if package_check.is_file():
        text = package_check.read_text(encoding="utf-8")
        for phrase in [
            "check_menu_app_stale_dashboard_guard",
            'recordedProcessIsAlive("INTENTOS_BETA_SERVICE_PID")',
            'recordedProcessIsAlive("INTENTOS_BETA_UI_PID")',
            "kill(pid, 0)",
            r"NSWorkspace\.shared\.open\(dashboard\)\s+return true",
        ]:
            if phrase not in text:
                failures.append(
                    f"scripts/harness/package-onboarding-check.py must enforce "
                    f"stale dashboard guard phrase {phrase!r}"
                )

    artifact_workflow = ROOT / ".github/workflows/trusted-beta-artifact.yml"
    if artifact_workflow.is_file():
        text = artifact_workflow.read_text(encoding="utf-8")
        for phrase in [
            "runs-on: macos-latest",
            "make package-onboarding-beta",
            "make package-onboarding-check",
            "actions/upload-artifact@v4",
            ".harness/runtime/artifacts/IntentOS-trusted-beta.zip",
            "github.event_name != 'pull_request'",
            "if-no-files-found: error",
            "retention-days:",
        ]:
            if phrase not in text:
                failures.append(
                    ".github/workflows/trusted-beta-artifact.yml must publish "
                    f"trusted beta artifact phrase {phrase!r}"
                )
        if "pull_request" in text and "if: github.event_name != 'pull_request'" not in text:
            failures.append(
                ".github/workflows/trusted-beta-artifact.yml must not upload "
                "tester-facing artifacts from pull_request builds"
            )

    service_security = ROOT / "intentos/beta/service_security.py"
    if service_security.is_file():
        text = service_security.read_text(encoding="utf-8")
        for phrase in [
            'API_TOKEN_HEADER = "X-IntentOS-Token"',
            "MAX_JSON_BODY_BYTES",
            "hmac.compare_digest",
            "origin_allowed",
            "cors_origin",
        ]:
            if phrase not in text:
                failures.append(f"intentos/beta/service_security.py must enforce {phrase!r}")

    service_py = ROOT / "intentos/beta/service.py"
    if service_py.is_file():
        text = service_py.read_text(encoding="utf-8")
        for phrase in [
            "if not self.authorize_request():",
            "IntentOS beta service requires a runtime API token",
            "service_security.send_json",
        ]:
            if phrase not in text:
                failures.append(f"intentos/beta/service.py must enforce API auth phrase {phrase!r}")
        if 'Access-Control-Allow-Origin", "*"' in text:
            failures.append("intentos/beta/service.py must not use wildcard CORS")

    beta_dev = ROOT / "scripts/harness/beta-dev.sh"
    if beta_dev.is_file():
        text = beta_dev.read_text(encoding="utf-8")
        for phrase in [
            "INTENTOS_BETA_API_TOKEN",
            "--api-token",
            "--allowed-origin",
            '"apiToken": "$api_token"',
            "X-IntentOS-Token",
            "INTENTOS_BETA_API_TOKEN=<redacted>",
        ]:
            if phrase not in text:
                failures.append(f"scripts/harness/beta-dev.sh must preserve API token wiring {phrase!r}")

    beta_status = ROOT / "scripts/harness/beta-status.sh"
    if beta_status.is_file():
        text = beta_status.read_text(encoding="utf-8")
        for phrase in ["INTENTOS_BETA_API_TOKEN", "X-IntentOS-Token", "INTENTOS_BETA_API_TOKEN=<redacted>"]:
            if phrase not in text:
                failures.append(f"scripts/harness/beta-status.sh must preserve token-aware diagnostics {phrase!r}")

    review_py = ROOT / "intentos/beta/review.py"
    if review_py.is_file():
        text = review_py.read_text(encoding="utf-8")
        for phrase in [
            "future_correction_for_event",
            "future_correction_matches",
            "apply_to_future = 1",
            "CORRECTION_REASON",
            "domain_only_future_match",
        ]:
            if phrase not in text:
                failures.append(f"intentos/beta/review.py must preserve future correction matching {phrase!r}")
        if 'if row["domain"] and row["domain"] == domain:' in text:
            failures.append(
                "intentos/beta/review.py must not apply future corrections by domain alone"
            )

    content_js = ROOT / "extension/chrome/content.js"
    if content_js.is_file():
        text = content_js.read_text(encoding="utf-8")
        for phrase in [
            "isIntentOSDashboard",
            'candidate.pathname === "/site/index.html"',
            'candidate.searchParams.get("mode") === "beta"',
            "dashboardOrigin",
        ]:
            if phrase not in text:
                failures.append(f"extension/chrome/content.js must restrict localhost bridge config {phrase!r}")

    background_js = ROOT / "extension/chrome/background.js"
    if background_js.is_file():
        text = background_js.read_text(encoding="utf-8")
        for phrase in [
            "isTrustedDashboardSender",
            'url.pathname === "/site/index.html"',
            'url.searchParams.get("mode") === "beta"',
            "message?.dashboardOrigin === url.origin",
        ]:
            if phrase not in text:
                failures.append(f"extension/chrome/background.js must restrict localhost bridge config {phrase!r}")

    manifest_json = ROOT / "extension/chrome/manifest.json"
    if manifest_json.is_file():
        manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
        matches = [
            match
            for script in manifest.get("content_scripts", [])
            for match in script.get("matches", [])
        ]
        if "http://127.0.0.1:*/*" in matches:
            failures.append(
                "extension/chrome/manifest.json must not inject config code into every localhost page"
            )
        if "http://127.0.0.1:*/site/index.html*" not in matches:
            failures.append(
                "extension/chrome/manifest.json must restrict localhost injection to the beta dashboard"
            )

    extension_py = ROOT / "intentos/beta/extension.py"
    if extension_py.is_file():
        text = extension_py.read_text(encoding="utf-8")
        for phrase in ["storage_safe_url", 'query=""', 'fragment=""']:
            if phrase not in text:
                failures.append(f"intentos/beta/extension.py must strip raw URL detail with {phrase!r}")

    store_py = ROOT / "intentos/beta/store.py"
    if store_py.is_file():
        text = store_py.read_text(encoding="utf-8")
        for phrase in [
            "clear_private_runtime_state",
            "PRIVATE_RUNTIME_STATUS_KEYS",
            "PRIVATE_RUNTIME_STATUS_PREFIXES",
            "PRIVATE_SETTING_KEYS",
        ]:
            if phrase not in text:
                failures.append(f"intentos/beta/store.py must scrub delete-local-data metadata {phrase!r}")

    service_helpers = ROOT / "intentos/beta/service_helpers.py"
    if service_helpers.is_file():
        text = service_helpers.read_text(encoding="utf-8")
        for phrase in ['"beta-*.json"', '"beta-*.png"', '"beta-*.html"', '"beta-*.txt"']:
            if phrase not in text:
                failures.append(f"intentos/beta/service_helpers.py must clear beta artifacts {phrase!r}")

    regression_tests = {
        "tests/test_beta_service.py": [
            "unauthorized_read",
            "unauthorized_write",
            "blocked_origin",
            "future_raw",
            "corrected_future",
            "future_item",
            "unrelated_future_raw",
            "unrelated_item",
            'deleted["capture_preview"]["state"]',
            'deleted["permissions"]["accessibility"]["state"]',
        ],
        "tests/test_beta_extension.py": [
            "test_browser_url_strips_query_and_fragment_before_persistence",
            "?email=person@example.com#private",
            "isIntentOSDashboard",
            "isTrustedDashboardSender",
            'candidate.pathname === "/site/index.html"',
        ],
        "tests/test_harness_completion.py": [
            "test_harness_lint_guards_review_finding_regressions",
            "must not use wildcard CORS",
            "must scrub delete-local-data metadata",
        ],
    }
    for relative_path, phrases in regression_tests.items():
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing beta regression test file {relative_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                failures.append(f"{relative_path} must keep beta regression coverage phrase {phrase!r}")

    app_js = ROOT / "web/app.js"
    if app_js.is_file():
        text = app_js.read_text(encoding="utf-8")
        for phrase in [
            "beta-config.json",
            "apiHeaders",
            "X-IntentOS-Token",
            "loadBetaJson",
            "/api/daily-review",
            "/api/daily-loop",
            "/api/daily-intent",
            "/api/review-checkin",
            "/api/weekly-patterns",
            "/api/corrections",
            "/api/permissions/check",
            "bindSectionNavigation",
            "openDisclosureForTarget",
            "scrollTargetIntoWorkspace",
            "renderCommandCenter",
            "renderCoachHero",
            "weekStartDate",
        ]:
            if phrase not in text:
                failures.append(f"web/app.js must support beta service mode phrase {phrase!r}")
        if "loadJson(apiUrl(betaConfig" in text:
            failures.append("web/app.js beta service reads must use loadBetaJson with API token headers")
    styles = ROOT / "web/styles.css"
    if styles.is_file():
        text = styles.read_text(encoding="utf-8")
        for phrase in [
            ".workspace",
            "overflow-y: auto",
            "scroll-padding-top",
            "grid-template-rows: auto minmax(0, 1fr)",
        ]:
            if phrase not in text:
                failures.append(f"web/styles.css must keep app-style section navigation phrase {phrase!r}")
    app_html = ROOT / "web/index.html"
    if app_html.is_file():
        html = app_html.read_text(encoding="utf-8")
        if "data-correction-controls" not in html:
            failures.append("web/index.html must expose beta correction controls")
        if "data-onboarding" not in html:
            failures.append("web/index.html must expose beta onboarding controls")
        if "data-daily-loop" not in html:
            failures.append("web/index.html must expose the sticky daily loop")
        if "data-intent-contract" not in html:
            failures.append("web/index.html must expose the intent tracking contract")
        if "data-service-notice" not in html:
            failures.append("web/index.html must expose the user-facing service notice")
        if "data-command-center" not in html:
            failures.append("web/index.html must expose the review command center")
        if "data-coach-hero" not in html:
            failures.append("web/index.html must expose the plan-vs-actual coach hero")
        if "data-weekly-details" not in html or "data-weekly-patterns" not in html:
            failures.append("web/index.html must expose weekly pattern disclosure bindings")
        for phrase in ["data-command-now-title", "data-command-trust-title", "data-command-tonight-title"]:
            if phrase not in html:
                failures.append(f"web/index.html must expose command center binding {phrase!r}")
        for phrase in ["data-signal-details", "data-queue-details", "data-evidence-details"]:
            if phrase not in html:
                failures.append(f"web/index.html must expose progressive detail binding {phrase!r}")
        for phrase in [
            "Sticky loop",
            "Beta only",
            "dogfood beta",
            "Tracking contract",
            "Local beta setup",
        ]:
            if phrase in html:
                failures.append(f"web/index.html must not expose internal UI phrase {phrase!r}")
    if app_js.is_file():
        text = app_js.read_text(encoding="utf-8")
        for phrase in [
            "Start the dogfood beta",
            "Local beta service",
            "SQLite daily timeline",
            "Live beta configuration",
        ]:
            if phrase in text:
                failures.append(f"web/app.js must not expose internal UI phrase {phrase!r}")

    docs = {
        "docs/APP_RUNTIME.md": ["make beta-dev", "beta-validation.json", "make dogfood-smoke"],
        "docs/SECURITY.md": ["Chrome extension bridge", "delete all local user data"],
        "docs/ARCHITECTURE.md": ["intentos/beta/store.py", "intentos/beta/permissions.py", "extension/chrome/"],
    }
    for relative_path, phrases in docs.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                failures.append(f"{relative_path} must mention {phrase!r}")


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
