"""Focused harness lint checks."""

from __future__ import annotations

from .common import ROOT


def check_ui_harness(failures: list[str]) -> None:
    dashboard_scripts = [
        "web/js/state.js",
        "web/js/api.js",
        "web/js/navigation.js",
        "web/js/format.js",
        "web/js/render-summary.js",
        "web/js/render-coach.js",
        "web/js/render-review.js",
        "web/js/render-daily-loop.js",
        "web/js/render-beta-queues.js",
        "web/js/render-onboarding.js",
        "web/js/boot.js",
    ]
    required_paths = [
        "web/index.html",
        "web/styles.css",
        "web/app.js",
        *dashboard_scripts,
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
    for path in dashboard_scripts:
        full_path = ROOT / path
        if full_path.is_file() and len(full_path.read_text(encoding="utf-8").splitlines()) > 350:
            failures.append(f"{path} is too large; keep split dashboard scripts under 350 lines")
    html = ROOT / "web/index.html"
    if html.is_file():
        html_text = html.read_text(encoding="utf-8")
        for path in dashboard_scripts:
            script = "./" + path.removeprefix("web/")
            if script not in html_text:
                failures.append(f"web/index.html must load split dashboard script {script}")

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
