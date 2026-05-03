"""Permission probes and local repair actions for the dogfood beta."""

from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from intentos.beta import state, store
from intentos.capture import browser, macos


SETTINGS_TARGETS = {
    "accessibility": {
        "label": "Accessibility Settings",
        "command": ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"],
    },
    "automation": {
        "label": "Automation Settings",
        "command": ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation"],
    },
    "chrome_extensions": {
        "label": "Chrome Extensions",
        "command": ["open", "-a", "Google Chrome", "chrome://extensions/"],
    },
}


def run_check(conn: sqlite3.Connection, mode: str, db_path: str | None = None) -> dict[str, Any]:
    if mode == "fake":
        record(conn, "accessibility_permission", "ok", "Fake Accessibility probe passed.")
        record(conn, "browser_automation_permission", "ok", "Fake Browser Automation probe passed.")
    elif mode == "real":
        snapshot = check_accessibility(conn)
        check_browser_automation(conn, snapshot)
    else:
        raise ValueError("permission mode must be real or fake")
    state.mark_readiness_check(conn)
    return store.status(conn, db_path)


def check_accessibility(conn: sqlite3.Connection) -> macos.MacOSAppSnapshot | None:
    try:
        snapshot = macos.frontmost_app_snapshot()
    except macos.MacOSCaptureError as exc:
        record(conn, "accessibility_permission", "needs_action", clean_detail(str(exc)))
        return None
    record(
        conn,
        "accessibility_permission",
        "ok",
        f"Frontmost app metadata is available from {snapshot.app_name}.",
    )
    return snapshot


def check_browser_automation(
    conn: sqlite3.Connection, snapshot: macos.MacOSAppSnapshot | None
) -> None:
    if snapshot is None:
        record(
            conn,
            "browser_automation_permission",
            "unchecked",
            "Run this check again with Chrome, Safari, Edge, Brave, or Arc in front.",
        )
        return
    try:
        tab = browser.active_browser_tab(snapshot.app_name, snapshot.bundle_id)
    except browser.BrowserCaptureError as exc:
        record(conn, "browser_automation_permission", "needs_action", clean_detail(str(exc)))
        return
    if tab is None:
        record(
            conn,
            "browser_automation_permission",
            "not_applicable",
            "The frontmost app is not a supported browser, or no active tab URL is visible.",
        )
        return
    record(
        conn,
        "browser_automation_permission",
        "ok",
        f"Browser metadata fallback can read {tab.domain}.",
    )


def open_settings_target(target: str, runtime_dir: Path, allow_open: bool = True) -> dict[str, Any]:
    if target == "diagnostics":
        command = ["open", str(runtime_dir)]
        label = "Diagnostics"
    else:
        spec = SETTINGS_TARGETS.get(target)
        if spec is None:
            raise ValueError("unknown settings target")
        command = list(spec["command"])
        label = str(spec["label"])
    if allow_open:
        subprocess.run(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"status": "opened" if allow_open else "validated", "target": target, "label": label}


def record(conn: sqlite3.Connection, key: str, value: str, detail: str) -> None:
    store.set_status(conn, key, value)
    store.set_status(conn, f"{key}_detail", detail)


def clean_detail(value: str) -> str:
    return " ".join(value.split())
