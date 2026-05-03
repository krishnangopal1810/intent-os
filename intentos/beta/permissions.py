"""Permission probes and local repair actions for the dogfood beta."""

from __future__ import annotations

import sqlite3
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from intentos.beta import state, store
from intentos.capture import browser, macos


SETTINGS_TARGETS = {
    "accessibility": {
        "label": "Accessibility Settings",
        "command": ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"],
        "summary": "Grant access so IntentOS can read the current app and focused window title.",
        "steps": [
            "In Privacy & Security > Accessibility, enable IntentOSBeta if it is listed.",
            "If macOS lists Terminal, Python, osascript, or Codex instead, enable the entry that launched the beta.",
            "Return to IntentOS and run the permission check again.",
        ],
        "verify": "Accessibility should show Ready, and the native recorder should keep writing current app/window metadata.",
    },
    "automation": {
        "label": "Automation Settings",
        "command": ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation"],
        "summary": "Allow local browser title and URL enrichment when a supported browser is frontmost.",
        "steps": [
            "Put Chrome, Safari, Edge, Brave, or Arc in front, then run the permission check to trigger the macOS prompt.",
            "In Privacy & Security > Automation, find IntentOSBeta, Python, osascript, Terminal, or Codex and enable the browser entry.",
            "If no browser entry exists yet, switch to the browser and run the permission check again so macOS creates it.",
        ],
        "verify": "Browser Automation should show Ready when a supported browser tab is frontmost.",
    },
    "chrome_extensions": {
        "label": "Chrome Extensions",
        "command": ["open", "-a", "Google Chrome", "chrome://extensions/"],
        "summary": "Optional: install the local Chrome bridge for richer tab metadata.",
        "steps": [],
        "verify": "After loading the extension, the Chrome bridge status should move to Connected or Posting events.",
        "optional": True,
    },
}


def run_check(conn: sqlite3.Connection, mode: str, db_path: str | None = None) -> dict[str, Any]:
    if mode == "fake":
        apply_fake_scenario(conn, "all_ok", db_path)
    elif mode == "real":
        snapshot = check_accessibility(conn)
        check_browser_automation(conn, snapshot)
    else:
        raise ValueError("permission mode must be real or fake")
    state.mark_readiness_check(conn)
    return store.status(conn, db_path)


def apply_fake_scenario(
    conn: sqlite3.Connection, scenario: str, db_path: str | None = None
) -> dict[str, Any]:
    """Apply deterministic permission and runtime states for harness checks."""

    store.set_setting(conn, "paused_until", "")
    store.set_status(conn, "capture_state", "ready")
    store.set_status(conn, "capture_note", "")
    store.set_status(conn, "native_recorder_interval_seconds", "5")
    store.set_status(conn, "native_recorder_pid", "fixture")
    store.set_status(conn, "native_recorder_log", "fixture")

    if scenario == "all_ok":
        record(conn, "accessibility_permission", "ok", "Fake Accessibility probe passed.")
        record(conn, "browser_automation_permission", "ok", "Fake Browser Automation probe passed.")
        store.set_status(conn, "native_recorder_state", "running")
        store.set_status(conn, "native_recorder_heartbeat_at", store.utc_now())
        store.set_status(conn, "extension_state", "connected")
        store.set_status(conn, "extension_last_seen_at", store.utc_now())
    elif scenario == "accessibility_blocked":
        record(conn, "accessibility_permission", "blocked", "Fake Accessibility probe is blocked.")
        record(
            conn,
            "browser_automation_permission",
            "unchecked",
            "Not tested because Accessibility is blocked.",
        )
        store.set_status(conn, "native_recorder_state", "running")
        store.set_status(conn, "native_recorder_heartbeat_at", store.utc_now())
        store.set_status(conn, "extension_state", "never_connected")
        store.set_status(conn, "extension_last_seen_at", "")
    elif scenario == "automation_blocked":
        record(conn, "accessibility_permission", "ok", "Fake Accessibility probe passed.")
        record(
            conn,
            "browser_automation_permission",
            "blocked",
            "Fake Browser Automation probe is blocked.",
        )
        store.set_status(conn, "native_recorder_state", "running")
        store.set_status(conn, "native_recorder_heartbeat_at", store.utc_now())
        store.set_status(conn, "extension_state", "never_connected")
        store.set_status(conn, "extension_last_seen_at", "")
    elif scenario == "chrome_bridge_missing":
        record(conn, "accessibility_permission", "ok", "Fake Accessibility probe passed.")
        record(conn, "browser_automation_permission", "ok", "Fake Browser Automation probe passed.")
        store.set_status(conn, "native_recorder_state", "running")
        store.set_status(conn, "native_recorder_heartbeat_at", store.utc_now())
        store.set_status(conn, "extension_state", "never_connected")
        store.set_status(conn, "extension_last_seen_at", "")
    elif scenario == "recorder_stale":
        record(conn, "accessibility_permission", "ok", "Fake Accessibility probe passed.")
        record(conn, "browser_automation_permission", "ok", "Fake Browser Automation probe passed.")
        stale = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
        store.set_status(conn, "native_recorder_state", "running")
        store.set_status(conn, "native_recorder_heartbeat_at", stale)
        store.set_status(conn, "extension_state", "connected")
        store.set_status(conn, "extension_last_seen_at", store.utc_now())
    elif scenario == "paused_capture":
        record(conn, "accessibility_permission", "ok", "Fake Accessibility probe passed.")
        record(conn, "browser_automation_permission", "ok", "Fake Browser Automation probe passed.")
        store.set_status(conn, "native_recorder_state", "running")
        store.set_status(conn, "native_recorder_heartbeat_at", store.utc_now())
        store.set_status(conn, "extension_state", "connected")
        store.set_status(conn, "extension_last_seen_at", store.utc_now())
        paused_until = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat().replace("+00:00", "Z")
        store.set_pause(conn, paused_until)
    elif scenario == "setup_needed":
        record(conn, "accessibility_permission", "needs_action", "Fake setup requires Accessibility.")
        record(conn, "browser_automation_permission", "unchecked", "Run checks after Accessibility is ready.")
        store.set_status(conn, "native_recorder_state", "not_started")
        store.set_status(conn, "native_recorder_heartbeat_at", "")
        store.set_status(conn, "extension_state", "never_connected")
        store.set_status(conn, "extension_last_seen_at", "")
    else:
        raise ValueError("unknown fake permission scenario")

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
            "Not tested because Accessibility is not ready; run this check again after frontmost app metadata works.",
        )
        return
    browser_name = browser.browser_application_name(snapshot.app_name, snapshot.bundle_id)
    if browser_name is None:
        record(
            conn,
            "browser_automation_permission",
            "not_applicable",
            f"Not tested because {snapshot.app_name} is frontmost. Switch to Chrome, Safari, Edge, Brave, or Arc and run checks again.",
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
            f"{browser_name} is frontmost, but no active http/https tab URL is visible.",
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
    return {
        "status": "opened" if allow_open else "validated",
        "target": target,
        "label": label,
        "guidance": setup_guidance(target, runtime_dir),
    }


def setup_guidance(target: str, runtime_dir: Path) -> dict[str, Any]:
    if target == "diagnostics":
        return {
            "title": "Diagnostics",
            "summary": "Use this folder when setup still looks blocked after granting permissions.",
            "steps": [
                "Open beta/app.env to confirm the dashboard and service URLs.",
                "Open logs/beta-native-recorder.log for recorder errors.",
                "Run make beta-status from the repo for the same status in text form.",
            ],
            "verify": "Send the diagnostics folder or beta-status output with any setup report.",
            "optional": False,
        }
    spec = SETTINGS_TARGETS.get(target)
    if spec is None:
        raise ValueError("unknown settings target")
    steps = list(spec.get("steps", []))
    if target == "chrome_extensions":
        steps = chrome_extension_steps()
    return {
        "title": str(spec["label"]),
        "summary": str(spec["summary"]),
        "steps": steps,
        "verify": str(spec["verify"]),
        "optional": bool(spec.get("optional", False)),
    }


def chrome_extension_steps() -> list[str]:
    extension_dir = Path(__file__).resolve().parents[2] / "extension/chrome"
    return [
        "Turn on Developer mode in the Chrome Extensions page.",
        f"Click Load unpacked and select {extension_dir}.",
        "Keep the IntentOS beta running; the bridge posts bounded active-tab metadata only to 127.0.0.1.",
        "Return to the dashboard and wait for Chrome bridge status to update.",
    ]


def record(conn: sqlite3.Connection, key: str, value: str, detail: str) -> None:
    store.set_status(conn, key, value)
    store.set_status(conn, f"{key}_detail", detail)


def clean_detail(value: str) -> str:
    return " ".join(value.split())
