"""Focused beta harness lint checks."""

from __future__ import annotations

import json

from .common import ROOT


def check_beta_security_contract(failures: list[str]) -> None:
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
        "tests/test_beta_api_security.py": [
            "unauthorized_read",
            "unauthorized_write",
            "blocked_origin",
        ],
        "tests/test_beta_corrections.py": [
            "future_raw",
            "corrected_future",
            "future_item",
            "unrelated_future_raw",
            "unrelated_item",
        ],
        "tests/test_beta_delete_data.py": [
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
