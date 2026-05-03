"""Shared beta runtime status and onboarding state."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from intentos.beta import store


ONBOARDING_KEYS = {
    "completed_at": "onboarding_completed_at",
    "dismissed_until": "onboarding_dismissed_until",
    "privacy_acknowledged_at": "privacy_acknowledged_at",
    "last_readiness_check_at": "last_readiness_check_at",
}


def status(conn: sqlite3.Connection, db_path: str | None = None) -> dict[str, Any]:
    paused_until = store.setting(conn, "paused_until", "")
    latest = conn.execute("SELECT MAX(started_at) FROM activity_events").fetchone()[0]
    native = native_recorder_status(conn)
    extension = extension_status(conn)
    payload = {
        "service": {"state": store.runtime_value(conn, "service_state") or "running"},
        "database": {
            "path": db_path,
            "retention_days": int(store.setting(conn, "retention_days", "30")),
            "writable": db_writable(conn),
        },
        "capture": {
            "state": store.runtime_value(conn, "capture_state") or "ready",
            "note": store.runtime_value(conn, "capture_note"),
        },
        "pause": {"paused": store.is_paused(paused_until), "paused_until": paused_until or None},
        "native_recorder": native,
        "extension": extension,
        "last_event_time": latest,
        "row_counts": store.row_counts(conn),
        "logs": {
            "service_log": store.runtime_value(conn, "service_log"),
            "native_recorder_log": native.get("log"),
        },
    }
    payload["permissions"] = permission_summary(conn, payload)
    payload["readiness"] = readiness_state(onboarding(conn), payload["permissions"])
    return payload


def onboarding(conn: sqlite3.Connection) -> dict[str, Any]:
    completed_at = store.setting(conn, ONBOARDING_KEYS["completed_at"], "")
    dismissed_until = store.setting(conn, ONBOARDING_KEYS["dismissed_until"], "")
    privacy_ack = store.setting(conn, ONBOARDING_KEYS["privacy_acknowledged_at"], "")
    last_check = store.setting(conn, ONBOARDING_KEYS["last_readiness_check_at"], "")
    return {
        "completed": bool(completed_at),
        "completed_at": completed_at or None,
        "dismissed": store.is_paused(dismissed_until),
        "dismissed_until": dismissed_until or None,
        "privacy_acknowledged": bool(privacy_ack),
        "privacy_acknowledged_at": privacy_ack or None,
        "last_readiness_check_at": last_check or None,
    }


def update_onboarding(conn: sqlite3.Connection, action: str, minutes: int = 240) -> dict[str, Any]:
    now = store.utc_now()
    if action == "complete":
        store.set_setting(conn, ONBOARDING_KEYS["privacy_acknowledged_at"], now)
        store.set_setting(conn, ONBOARDING_KEYS["completed_at"], now)
        store.set_setting(conn, ONBOARDING_KEYS["dismissed_until"], "")
    elif action == "acknowledge_privacy":
        store.set_setting(conn, ONBOARDING_KEYS["privacy_acknowledged_at"], now)
    elif action == "dismiss":
        if minutes <= 0:
            raise ValueError("minutes must be positive")
        dismissed_until = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()
        store.set_setting(conn, ONBOARDING_KEYS["dismissed_until"], dismissed_until.replace("+00:00", "Z"))
    elif action == "reset":
        for key in ONBOARDING_KEYS.values():
            store.set_setting(conn, key, "")
    else:
        raise ValueError("unknown onboarding action")
    conn.commit()
    return onboarding(conn)


def mark_readiness_check(conn: sqlite3.Connection) -> None:
    store.set_setting(conn, ONBOARDING_KEYS["last_readiness_check_at"], store.utc_now())


def permission_summary(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    extension = payload["extension"]["state"]
    capture_state = payload["capture"]["state"]
    return {
        "local_service": item("ok", "Local service", "Dashboard API is running.", "diagnostics"),
        "database": item(
            "ok" if payload["database"]["writable"] else "blocked",
            "Local database",
            "SQLite is writable." if payload["database"]["writable"] else "SQLite is not writable.",
            "diagnostics",
        ),
        "accessibility": permission_item(
            conn,
            "accessibility_permission",
            "Accessibility",
            "Required for current app and window metadata.",
            "accessibility",
        ),
        "browser_automation": permission_item(
            conn,
            "browser_automation_permission",
            "Browser Automation",
            "Fallback for browser URL and title metadata when the extension is unavailable.",
            "automation",
        ),
        "native_recorder": item(
            "ok" if payload["native_recorder"]["state"] == "running" else "needs_action",
            "Native recorder",
            native_recorder_detail(payload["native_recorder"]),
            "diagnostics",
        ),
        "chrome_extension": item(
            "ok" if extension in {"connected", "posting_events", "fixture_bridge"} else "unchecked",
            "Chrome bridge",
            chrome_extension_detail(payload["extension"]),
            "chrome_extensions",
        ),
        "capture": item(
            "ok" if capture_state in {"ready", "running", "away"} else "needs_action",
            "Capture health",
            payload["capture"].get("note") or f"Capture is {capture_state}.",
            "diagnostics",
        ),
        "privacy": item(
            "ok",
            "Privacy mode",
            "Local-only metadata capture; screenshots, keylogging, page bodies, cookies, and cloud sync stay off.",
            "diagnostics",
        ),
    }


def permission_item(
    conn: sqlite3.Connection, key: str, label: str, unchecked_detail: str, action: str
) -> dict[str, str]:
    value = store.runtime_value(conn, key) or "unchecked"
    detail = store.runtime_value(conn, f"{key}_detail") or unchecked_detail
    return item(value, label, detail, action)


def item(state: str, label: str, detail: str, action: str) -> dict[str, str]:
    normalized = state if state in {"ok", "needs_action", "blocked", "not_applicable"} else "unchecked"
    return {"state": normalized, "label": label, "detail": detail, "action": action}


def native_recorder_status(conn: sqlite3.Connection) -> dict[str, Any]:
    return {
        "state": store.runtime_value(conn, "native_recorder_state") or "not_started",
        "pid": store.runtime_value(conn, "native_recorder_pid"),
        "last_event_at": store.runtime_value(conn, "native_recorder_last_event_at"),
        "last_error": store.runtime_value(conn, "native_recorder_last_error"),
        "interval_seconds": store.runtime_value(conn, "native_recorder_interval_seconds"),
        "log": store.runtime_value(conn, "native_recorder_log"),
    }


def extension_status(conn: sqlite3.Connection) -> dict[str, Any]:
    raw_state = store.runtime_value(conn, "extension_state")
    last_seen_at = store.runtime_value(conn, "extension_last_seen_at")
    last_event_at = store.runtime_value(conn, "last_browser_event_at")
    state_name = raw_state or "never_connected"
    if raw_state != "fixture_bridge":
        if raw_state == "posting_events" and last_seen_at and is_recent(last_seen_at, minutes=5):
            state_name = "posting_events"
        elif raw_state == "connected" and last_seen_at and is_recent(last_seen_at, minutes=5):
            state_name = "connected"
        elif last_event_at and is_recent(last_event_at, minutes=5):
            state_name = "posting_events"
        elif last_seen_at and is_recent(last_seen_at, minutes=5):
            state_name = "connected"
        elif last_seen_at or last_event_at:
            state_name = "stale"
        else:
            state_name = "never_connected"
    return {
        "state": state_name,
        "last_seen_at": last_seen_at,
        "last_event_at": last_event_at,
    }


def native_recorder_detail(native: dict[str, Any]) -> str:
    state_name = native.get("state")
    if state_name == "running":
        last = native.get("last_event_at")
        return f"Native macOS metadata capture is running{f'; last event {last}' if last else ''}."
    if state_name == "error":
        return native.get("last_error") or "Native recorder failed."
    return f"Native recorder is {state_name}."


def chrome_extension_detail(extension: dict[str, Any]) -> str:
    state_name = extension.get("state")
    if state_name == "posting_events":
        return "Chrome bridge is posting enhanced tab metadata."
    if state_name == "connected":
        return "Chrome bridge heartbeat is connected."
    if state_name == "fixture_bridge":
        return "Fixture Chrome bridge is connected."
    if state_name == "stale":
        return "Chrome bridge was seen before but has not posted recently."
    return "Optional: install or wake the Chrome bridge for richer browser metadata."


def readiness_state(onboarding_state: dict[str, Any], permissions: dict[str, Any]) -> dict[str, str]:
    states = [item["state"] for item in permissions.values()]
    if "blocked" in states or "needs_action" in states:
        state_name = "setup_needed"
    elif onboarding_state["completed"]:
        state_name = "complete"
    else:
        state_name = "ready"
    return {"state": state_name, "label": state_name.replace("_", " ").title()}


def db_writable(conn: sqlite3.Connection) -> bool:
    try:
        conn.execute("SELECT 1").fetchone()
        return True
    except sqlite3.Error:
        return False


def is_recent(value: str, minutes: int) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.astimezone(timezone.utc) >= datetime.now(timezone.utc) - timedelta(minutes=minutes)
