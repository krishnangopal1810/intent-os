"""First-run setup milestones, capture preview, and redacted reports."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from intentos.beta import setup_diagnostics, store


APP_DISPLAY_NAME = setup_diagnostics.APP_DISPLAY_NAME
APP_BUNDLE_ID = setup_diagnostics.APP_BUNDLE_ID

ACTIVATION_KEYS = {
    "opened": "activation_opened_at",
    "privacy_acknowledged": "privacy_acknowledged_at",
    "accessibility_verified": "activation_accessibility_verified_at",
    "capture_verified": "activation_capture_verified_at",
    "intent_set": "activation_intent_set_at",
    "first_live_state": "activation_first_live_state_at",
    "first_rescue_state": "activation_first_rescue_state_at",
    "first_recovery_action": "activation_first_recovery_action_at",
    "first_review_ready": "activation_first_review_ready_at",
    "review_completed": "activation_review_completed_at",
}

CAPTURE_PREVIEW_KEYS = {
    "state": "capture_preview_state",
    "observed_at": "capture_preview_observed_at",
    "app_name": "capture_preview_app_name",
    "bundle_id": "capture_preview_bundle_id",
    "window_title": "capture_preview_window_title",
    "url": "capture_preview_url",
    "domain": "capture_preview_domain",
    "source": "capture_preview_source",
    "detail": "capture_preview_detail",
}


def mark_milestone(conn: sqlite3.Connection, name: str, at: str | None = None) -> None:
    key = ACTIVATION_KEYS[name]
    if key == "privacy_acknowledged_at":
        store.set_setting(conn, key, at or store.utc_now(), overwrite=False)
    else:
        store.set_status_once(conn, key, at or store.utc_now())


def activation_status(conn: sqlite3.Connection) -> dict[str, Any]:
    milestones = {
        name: milestone_value(conn, key)
        for name, key in ACTIVATION_KEYS.items()
    }
    opened = parse_time(milestones.get("opened"))
    capture = parse_time(milestones.get("capture_verified"))
    intent = parse_time(milestones.get("intent_set"))
    return {
        "app_opened_at": milestones["opened"],
        "opened_at": milestones["opened"],
        "privacy_acknowledged_at": milestones["privacy_acknowledged"],
        "accessibility_verified_at": milestones["accessibility_verified"],
        "capture_verified_at": milestones["capture_verified"],
        "intent_set_at": milestones["intent_set"],
        "first_live_state_at": milestones["first_live_state"],
        "first_rescue_state_at": milestones["first_rescue_state"],
        "first_recovery_action_at": milestones["first_recovery_action"],
        "first_review_ready_at": milestones["first_review_ready"],
        "review_completed_at": milestones["review_completed"],
        "time_to_capture_ready_seconds": elapsed_seconds(opened, capture),
        "time_to_intent_set_seconds": elapsed_seconds(opened, intent),
        "milestones": milestones,
    }


def milestone_value(conn: sqlite3.Connection, key: str) -> str | None:
    if key == "privacy_acknowledged_at":
        value = store.setting(conn, key, "")
    else:
        value = store.runtime_value(conn, key) or ""
    return value or None


def record_capture_preview(
    conn: sqlite3.Connection,
    *,
    app_name: str,
    bundle_id: str | None,
    window_title: str | None,
    url: str | None = None,
    domain: str | None = None,
    source: str = "accessibility",
    detail: str = "IntentOS can read current app and window metadata.",
) -> None:
    values = {
        "state": "ok",
        "observed_at": store.utc_now(),
        "app_name": app_name,
        "bundle_id": bundle_id or "",
        "window_title": window_title or "",
        "url": url or "",
        "domain": domain or "",
        "source": source,
        "detail": detail,
    }
    for name, value in values.items():
        store.set_status(conn, CAPTURE_PREVIEW_KEYS[name], value)
    mark_milestone(conn, "capture_verified")


def record_capture_preview_blocked(conn: sqlite3.Connection, detail: str) -> None:
    store.set_status(conn, CAPTURE_PREVIEW_KEYS["state"], "blocked")
    store.set_status(conn, CAPTURE_PREVIEW_KEYS["observed_at"], store.utc_now())
    store.set_status(conn, CAPTURE_PREVIEW_KEYS["detail"], " ".join(detail.split()))
    for name in ["app_name", "bundle_id", "window_title", "url", "domain", "source"]:
        store.set_status(conn, CAPTURE_PREVIEW_KEYS[name], "")


def reset_setup(conn: sqlite3.Connection) -> None:
    for key in ACTIVATION_KEYS.values():
        if key == "privacy_acknowledged_at":
            store.set_setting(conn, key, "")
        else:
            store.set_status(conn, key, "")
    for key in CAPTURE_PREVIEW_KEYS.values():
        store.set_status(conn, key, "")
    store.set_setting(conn, "browser_detail_state", "not_started")


def capture_preview(conn: sqlite3.Connection) -> dict[str, Any]:
    state = store.runtime_value(conn, CAPTURE_PREVIEW_KEYS["state"]) or "unchecked"
    return {
        "state": state,
        "observed_at": store.runtime_value(conn, CAPTURE_PREVIEW_KEYS["observed_at"]),
        "app_name": empty_to_none(store.runtime_value(conn, CAPTURE_PREVIEW_KEYS["app_name"])),
        "bundle_id": empty_to_none(store.runtime_value(conn, CAPTURE_PREVIEW_KEYS["bundle_id"])),
        "window_title": empty_to_none(store.runtime_value(conn, CAPTURE_PREVIEW_KEYS["window_title"])),
        "url": empty_to_none(store.runtime_value(conn, CAPTURE_PREVIEW_KEYS["url"])),
        "domain": empty_to_none(store.runtime_value(conn, CAPTURE_PREVIEW_KEYS["domain"])),
        "source": empty_to_none(store.runtime_value(conn, CAPTURE_PREVIEW_KEYS["source"])),
        "detail": store.runtime_value(conn, CAPTURE_PREVIEW_KEYS["detail"]) or capture_preview_detail(state),
    }


def enrich_onboarding(
    conn: sqlite3.Connection,
    onboarding: dict[str, Any],
    status_payload: dict[str, Any],
) -> dict[str, Any]:
    activation = status_payload["activation"]
    preview = status_payload["capture_preview"]
    permissions = status_payload["permissions"]
    browser_state = store.setting(conn, "browser_detail_state", "not_started")
    milestones = {
        "opened": bool(activation.get("opened_at")),
        "privacy_acknowledged": bool(onboarding.get("privacy_acknowledged")),
        "accessibility_verified": permissions["accessibility"]["state"] == "ok",
        "capture_verified": preview.get("state") == "ok",
        "intent_set": bool(activation.get("intent_set_at")),
        "first_live_state": bool(activation.get("first_live_state_at")),
        "first_rescue_state": bool(activation.get("first_rescue_state_at")),
    }
    enriched = dict(onboarding)
    enriched.update(
        {
            "current_step": current_step(milestones, onboarding),
            "steps": setup_steps(milestones),
            "milestones": milestones,
            "browser_detail": {
                "state": browser_state,
                "required": False,
                "label": browser_detail_label(browser_state),
            },
            "can_complete": can_complete_milestones(milestones),
            "completion_blockers": completion_blockers(milestones),
        }
    )
    return enriched


def setup_summary(
    conn: sqlite3.Connection,
    onboarding: dict[str, Any],
    status_payload: dict[str, Any],
) -> dict[str, Any]:
    enriched = enrich_onboarding(conn, onboarding, status_payload)
    return {
        "current_step": enriched["current_step"],
        "setup_complete": bool(enriched["completed"] and enriched["can_complete"]),
        "can_complete": enriched["can_complete"],
        "completion_blockers": enriched["completion_blockers"],
        "browser_detail": enriched["browser_detail"],
    }


def current_step(milestones: dict[str, bool], onboarding: dict[str, Any]) -> str:
    if onboarding.get("completed") and can_complete_milestones(milestones):
        return "complete"
    if not milestones["privacy_acknowledged"]:
        return "privacy"
    if not milestones["accessibility_verified"]:
        return "app_access"
    if not milestones["capture_verified"]:
        return "capture_check"
    if not milestones["intent_set"]:
        return "daily_focus"
    return "first_block"


def setup_steps(milestones: dict[str, bool]) -> list[dict[str, Any]]:
    return [
        step("privacy", "Privacy", milestones["privacy_acknowledged"], "Local-only promise accepted."),
        step("app_access", "App access", milestones["accessibility_verified"], "App/window access verified."),
        step("capture_check", "Capture check", milestones["capture_verified"], "Current metadata preview shown."),
        step("daily_focus", "Daily focus", milestones["intent_set"], "Focus and avoid target saved."),
        step("first_block", "First block", milestones["first_live_state"], "First live state is visible."),
    ]


def step(step_id: str, label: str, complete: bool, ready_copy: str) -> dict[str, Any]:
    return {
        "id": step_id,
        "label": label,
        "complete": complete,
        "verification": ready_copy if complete else "Next action",
    }


def can_complete(
    conn: sqlite3.Connection,
    onboarding: dict[str, Any],
    status_payload: dict[str, Any],
) -> bool:
    enriched = enrich_onboarding(conn, onboarding, status_payload)
    return bool(enriched["can_complete"])


def can_complete_milestones(milestones: dict[str, bool]) -> bool:
    return all(
        milestones[name]
        for name in [
            "privacy_acknowledged",
            "accessibility_verified",
            "capture_verified",
            "intent_set",
        ]
    )


def completion_blockers(milestones: dict[str, bool]) -> list[str]:
    labels = {
        "privacy_acknowledged": "privacy acknowledgment",
        "accessibility_verified": "app access",
        "capture_verified": "capture check",
        "intent_set": "daily focus",
    }
    return [label for key, label in labels.items() if not milestones.get(key)]


def setup_report(
    conn: sqlite3.Connection,
    db_path: str | None,
    runtime_dir: Path | None,
    status_payload: dict[str, Any],
) -> dict[str, Any]:
    return setup_diagnostics.setup_report(conn, db_path, runtime_dir, status_payload)


def preflight_status(
    conn: sqlite3.Connection,
    db_path: str | None = None,
) -> dict[str, Any]:
    return setup_diagnostics.preflight_status(conn, db_path)


def app_identity() -> dict[str, str]:
    return setup_diagnostics.app_identity()


def browser_detail_label(state: str) -> str:
    if state == "enabled":
        return "Browser detail enabled"
    if state == "skipped":
        return "Browser detail skipped"
    return "Browser detail optional"


def capture_preview_detail(state: str) -> str:
    if state == "blocked":
        return "IntentOS could not verify current app/window metadata yet."
    if state == "ok":
        return "IntentOS can read current app and window metadata."
    return "Run the app access check to verify current app/window metadata."


def empty_to_none(value: str | None) -> str | None:
    return value or None


def parse_time(value: str | None) -> float | None:
    if not value:
        return None
    from datetime import datetime

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def elapsed_seconds(start: float | None, end: float | None) -> int | None:
    if start is None or end is None or end < start:
        return None
    return int(end - start)
