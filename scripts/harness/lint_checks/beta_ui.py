"""Focused beta harness lint checks."""

from __future__ import annotations

from .common import ROOT


def check_beta_ui_contract(failures: list[str]) -> None:
    js_paths = sorted((ROOT / "web/js").glob("*.js"))
    if js_paths:
        text = "\n".join(path.read_text(encoding="utf-8") for path in js_paths)
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
                failures.append(f"web/js/*.js must support beta service mode phrase {phrase!r}")
        if "loadJson(apiUrl(betaConfig" in text:
            failures.append("web/js/*.js beta service reads must use loadBetaJson with API token headers")
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
    if js_paths:
        text = "\n".join(path.read_text(encoding="utf-8") for path in js_paths)
        for phrase in [
            "Start the dogfood beta",
            "Local beta service",
            "SQLite daily timeline",
            "Live beta configuration",
        ]:
            if phrase in text:
                failures.append(f"web/js/*.js must not expose internal UI phrase {phrase!r}")

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
