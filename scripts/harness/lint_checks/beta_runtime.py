"""Focused beta harness lint checks."""

from __future__ import annotations

from .common import ROOT


def check_beta_runtime_contract(failures: list[str]) -> None:
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
    validate_sources = [
        validate_beta,
        ROOT / "scripts/product/validate_beta.py",
        *sorted((ROOT / "scripts/product/beta_validation").glob("*.py")),
    ]
    if validate_beta.is_file():
        wrapper_text = validate_beta.read_text(encoding="utf-8")
        if len(wrapper_text.splitlines()) > 40:
            failures.append("scripts/product/validate-beta.sh must stay a thin wrapper under 40 lines")
        if "python3 - <<'PY'" in wrapper_text or 'python3 - << "PY"' in wrapper_text:
            failures.append("scripts/product/validate-beta.sh must not embed Python blocks")
        for path in validate_sources[1:]:
            if path.is_file() and len(path.read_text(encoding="utf-8").splitlines()) > 320:
                failures.append(f"{path.relative_to(ROOT)} is too large; split beta validation modules under 320 lines")
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in validate_sources
            if path.is_file()
        )
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
            '"apiToken"',
            "sticky_loop_future_correction",
            "apply_to_future correction did not match a future segment key",
            "apply_to_future correction matched an unrelated same-domain segment",
            "redacted_config",
        ]:
            if phrase not in text:
                failures.append(
                    "scripts/product/validate-beta.sh and beta_validation modules must lock and verify the "
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
