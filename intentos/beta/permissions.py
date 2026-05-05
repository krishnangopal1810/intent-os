"""Permission probes and local repair actions for the dogfood beta."""

from __future__ import annotations

import sqlite3
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from intentos.beta import setup_flow, state, store
from intentos.capture import browser, macos


SETTINGS_TARGETS = {
    "accessibility": {
        "label": "Accessibility Settings",
        "command": ["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"],
        "summary": "Grant access so IntentOS can read the current app and focused window title.",
        "steps": [
            "In Privacy & Security > Accessibility, enable IntentOS if it is listed.",
            "If macOS also lists an older Terminal, Python, osascript, or Codex entry, leave it alone unless IntentOS still cannot verify capture.",
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
            "In Privacy & Security > Automation, find IntentOS and enable the browser entry.",
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

    if scenario in {"all_ok", "accessibility_granted", "capture_preview_success", "browser_detail_granted"}:
        record(conn, "accessibility_permission", "ok", "Fake Accessibility probe passed.")
        record(conn, "browser_automation_permission", "ok", "Fake Browser Automation probe passed.")
        fake_capture_preview(conn, browser=scenario == "browser_detail_granted")
        store.set_status(conn, "native_recorder_state", "running")
        store.set_status(conn, "native_recorder_heartbeat_at", store.utc_now())
        store.set_status(conn, "extension_state", "connected")
        store.set_status(conn, "extension_last_seen_at", store.utc_now())
        if scenario == "browser_detail_granted":
            state.update_onboarding(conn, "enable_browser_detail")
    elif scenario in {"accessibility_blocked", "accessibility_missing", "duplicate_permission_identity"}:
        detail = "Fake Accessibility probe is blocked."
        if scenario == "accessibility_missing":
            detail = "IntentOS is not enabled in Accessibility yet."
        elif scenario == "duplicate_permission_identity":
            detail = "An older Terminal/Python permission may exist; enable IntentOS for the stable app identity."
        record(conn, "accessibility_permission", "blocked", "Fake Accessibility probe is blocked.")
        record(
            conn,
            "browser_automation_permission",
            "unchecked",
            "Not tested because Accessibility is blocked.",
        )
        record(conn, "accessibility_permission", "blocked", detail)
        setup_flow.record_capture_preview_blocked(conn, detail)
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
        fake_capture_preview(conn)
        store.set_status(conn, "native_recorder_state", "running")
        store.set_status(conn, "native_recorder_heartbeat_at", store.utc_now())
        store.set_status(conn, "extension_state", "never_connected")
        store.set_status(conn, "extension_last_seen_at", "")
    elif scenario in {"chrome_bridge_missing", "browser_detail_skipped"}:
        record(conn, "accessibility_permission", "ok", "Fake Accessibility probe passed.")
        record(conn, "browser_automation_permission", "not_applicable", "Browser detail was skipped for first value.")
        fake_capture_preview(conn)
        store.set_status(conn, "native_recorder_state", "running")
        store.set_status(conn, "native_recorder_heartbeat_at", store.utc_now())
        store.set_status(conn, "extension_state", "never_connected")
        store.set_status(conn, "extension_last_seen_at", "")
        if scenario == "browser_detail_skipped":
            state.update_onboarding(conn, "skip_browser_detail")
    elif scenario == "capture_preview_blocked":
        record(conn, "accessibility_permission", "ok", "Fake Accessibility probe passed.")
        record(conn, "browser_automation_permission", "unchecked", "Browser detail waits until capture is verified.")
        setup_flow.mark_milestone(conn, "accessibility_verified")
        setup_flow.record_capture_preview_blocked(conn, "Fake capture preview could not read the current window.")
        store.set_status(conn, "capture_state", "blocked")
        store.set_status(conn, "capture_note", "Capture preview failed.")
        store.set_status(conn, "native_recorder_state", "running")
        store.set_status(conn, "native_recorder_heartbeat_at", store.utc_now())
        store.set_status(conn, "extension_state", "never_connected")
        store.set_status(conn, "extension_last_seen_at", "")
    elif scenario == "recorder_stale":
        record(conn, "accessibility_permission", "ok", "Fake Accessibility probe passed.")
        record(conn, "browser_automation_permission", "ok", "Fake Browser Automation probe passed.")
        fake_capture_preview(conn)
        stale = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
        store.set_status(conn, "native_recorder_state", "running")
        store.set_status(conn, "native_recorder_heartbeat_at", stale)
        store.set_status(conn, "extension_state", "connected")
        store.set_status(conn, "extension_last_seen_at", store.utc_now())
    elif scenario == "paused_capture":
        record(conn, "accessibility_permission", "ok", "Fake Accessibility probe passed.")
        record(conn, "browser_automation_permission", "ok", "Fake Browser Automation probe passed.")
        fake_capture_preview(conn)
        store.set_status(conn, "native_recorder_state", "running")
        store.set_status(conn, "native_recorder_heartbeat_at", store.utc_now())
        store.set_status(conn, "extension_state", "connected")
        store.set_status(conn, "extension_last_seen_at", store.utc_now())
        paused_until = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat().replace("+00:00", "Z")
        store.set_pause(conn, paused_until)
    elif scenario in {"setup_needed", "fresh_install"}:
        record(conn, "accessibility_permission", "needs_action", "Fake setup requires Accessibility.")
        record(conn, "browser_automation_permission", "unchecked", "Run checks after Accessibility is ready.")
        setup_flow.record_capture_preview_blocked(conn, "IntentOS has not verified current app/window metadata yet.")
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
        setup_flow.record_capture_preview_blocked(conn, str(exc))
        return None
    record(
        conn,
        "accessibility_permission",
        "ok",
        f"Frontmost app metadata is available from {snapshot.app_name}.",
    )
    setup_flow.mark_milestone(conn, "accessibility_verified")
    setup_flow.record_capture_preview(
        conn,
        app_name=snapshot.app_name,
        bundle_id=snapshot.bundle_id,
        window_title=snapshot.window_title,
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
    setup_flow.record_capture_preview(
        conn,
        app_name=snapshot.app_name,
        bundle_id=snapshot.bundle_id,
        window_title=tab.title or snapshot.window_title,
        url=tab.url,
        domain=tab.domain,
        source="browser_detail",
        detail=f"IntentOS can read current app/window metadata and browser detail for {tab.domain}.",
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


def fake_capture_preview(conn: sqlite3.Connection, browser: bool = False) -> None:
    setup_flow.mark_milestone(conn, "accessibility_verified")
    setup_flow.record_capture_preview(
        conn,
        app_name="IntentOS",
        bundle_id=setup_flow.APP_BUNDLE_ID,
        window_title="IntentOS Review Board",
        url="http://127.0.0.1:58917/site/index.html?mode=beta" if browser else None,
        domain="127.0.0.1" if browser else None,
        source="fake_permission_probe",
        detail="Fake setup probe verified app/window metadata.",
    )

def clean_detail(value: str) -> str:
    return " ".join(value.split())
