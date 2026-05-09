#!/usr/bin/env python3
"""Validate the trusted-tester package contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / ".harness/runtime/artifacts/onboarding-beta-package.json"
MENU_APP = ROOT / "macos/IntentOSBeta/IntentOSBeta.swift"


def main() -> int:
    failures: list[str] = []
    script = ROOT / "scripts/product/package-onboarding-beta.sh"
    text = script.read_text(encoding="utf-8") if script.is_file() else ""
    for phrase in [
        "IntentOS-trusted-beta.zip",
        "intent-os-runtime",
        "normal_path_requires_terminal",
        '"bundle_id": "local.intentos.trusted"',
        '"display_name": "IntentOS"',
        "codesign --force --deep --sign -",
    ]:
        if phrase not in text:
            failures.append(f"package-onboarding-beta.sh must include {phrase!r}")

    menu_text = MENU_APP.read_text(encoding="utf-8") if MENU_APP.is_file() else ""
    check_menu_app_stale_dashboard_guard(menu_text, failures)

    payload = read_payload(ARTIFACT)
    if payload and payload.get("status") == "built":
        if payload.get("normal_path_requires_terminal") is not False:
            failures.append("built tester package must not require Terminal")
        if payload.get("bundle_id") != "local.intentos.trusted":
            failures.append("built tester package must use stable IntentOS bundle id")
        if not str(payload.get("zip", "")).endswith("IntentOS-trusted-beta.zip"):
            failures.append("built tester package must emit IntentOS-trusted-beta.zip")
        runtime = payload.get("bundled_runtime")
        if runtime and not (ROOT / runtime).exists() and not Path(runtime).exists():
            failures.append("built tester package metadata points to a missing runtime")

    output = ROOT / ".harness/runtime/artifacts/package-onboarding-check.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "status": "failed" if failures else "ok",
        "checked_script": str(script.relative_to(ROOT)),
        "checked_menu_app": str(MENU_APP.relative_to(ROOT)),
        "artifact_present": ARTIFACT.is_file(),
        "failures": failures,
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if failures:
        for failure in failures:
            print(f"package-onboarding-check: {failure}", file=sys.stderr)
        return 1
    print(f"package-onboarding-check: ok ({output})")
    return 0


def check_menu_app_stale_dashboard_guard(swift: str, failures: list[str]) -> None:
    if not swift:
        failures.append("missing macOS menu app source for trusted tester package")
        return
    required_phrases = [
        'menu.addItem(item("Open Dashboard", #selector(openDashboard)))',
        "startBetaIfNeeded(openWhenReady: true)",
        'envValue("INTENTOS_BETA_STATUS") == "running"',
        'recordedProcessIsAlive("INTENTOS_BETA_SERVICE_PID")',
        'recordedProcessIsAlive("INTENTOS_BETA_UI_PID")',
        "private func recordedProcessIsAlive",
        "kill(pid, 0)",
        "return NSWorkspace.shared.open(dashboard)",
    ]
    for phrase in required_phrases:
        if phrase not in swift:
            failures.append(f"menu app stale-dashboard guard must include {phrase!r}")
    if re.search(r"NSWorkspace\.shared\.open\(dashboard\)\s+return true", swift):
        failures.append(
            "menu app must not report dashboard opened without checking NSWorkspace.open result"
        )
    status_index = swift.find('envValue("INTENTOS_BETA_STATUS") == "running"')
    service_index = swift.find('recordedProcessIsAlive("INTENTOS_BETA_SERVICE_PID")')
    ui_index = swift.find('recordedProcessIsAlive("INTENTOS_BETA_UI_PID")')
    if -1 not in [status_index, service_index, ui_index] and not (
        status_index < service_index < ui_index
    ):
        failures.append(
            "menu app must check running status before validating service and UI PIDs"
        )


def read_payload(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


if __name__ == "__main__":
    raise SystemExit(main())
