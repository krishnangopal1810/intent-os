"""First-run setup milestones, capture preview, and redacted reports."""

from __future__ import annotations

import platform
import sqlite3
import os
from pathlib import Path
from typing import Any

from intentos.beta import store


APP_DISPLAY_NAME = "IntentOS"
APP_BUNDLE_ID = "local.intentos.trusted"

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
    return {
        "app": app_identity(),
        "system": {"macos": platform.mac_ver()[0] or platform.platform()},
        "runtime": {"dir": str(runtime_dir) if runtime_dir else None},
        "service": status_payload["service"],
        "database": status_payload["database"],
        "preflight": status_payload.get("preflight", {}),
        "readiness": status_payload["readiness"],
        "setup": status_payload["setup"],
        "activation": status_payload["activation"],
        "permissions": {
            key: {"state": value.get("state"), "label": value.get("label")}
            for key, value in status_payload["permissions"].items()
        },
        "capture_preview": redact_preview(status_payload["capture_preview"]),
        "recent_errors": recent_errors(conn),
        "db_path": db_path,
        "privacy": {
            "local_only": True,
            "screenshots": False,
            "keylogging": False,
            "page_bodies": False,
            "cookies": False,
            "cloud_sync": False,
        },
    }


def preflight_status(
    conn: sqlite3.Connection,
    db_path: str | None = None,
) -> dict[str, Any]:
    runtime_dir = runtime_dir_for(db_path)
    app_bundle = os.environ.get("INTENTOS_APP_BUNDLE_PATH", "")
    bundled_runtime_path = os.environ.get("INTENTOS_BUNDLED_RUNTIME_PATH", "")
    bundled_runtime = env_true("INTENTOS_BUNDLED_RUNTIME_PRESENT") or bool(
        bundled_runtime_path and Path(bundled_runtime_path).joinpath("Makefile").is_file()
    )
    service_running = (store.runtime_value(conn, "service_state") or "running") == "running"
    checks = {
        "bundled_runtime_present": check(
            bundled_runtime,
            "Tester app includes its local runtime.",
            "Source checkout path; tester package should include the runtime.",
            required=False,
        ),
        "app_support_runtime_writable": check(
            is_writable_dir(runtime_dir),
            "IntentOS can write its local runtime data.",
            "IntentOS cannot write its local runtime data folder.",
        ),
        "service_startable": check(
            service_running,
            "Local review service is running.",
            "Local review service has not started.",
        ),
        "local_port_available": check(
            service_running,
            "Localhost review port is serving.",
            "Localhost review port is not serving yet.",
        ),
        "app_location_readable": check(
            is_readable_path(Path(app_bundle)) if app_bundle else True,
            "IntentOS app location is readable.",
            "IntentOS app location is not readable.",
        ),
    }
    required_ok = all(
        item["state"] == "ok"
        for item in checks.values()
        if item.get("required", True)
    )
    return {
        "state": "ready" if required_ok else "blocked",
        "normal_path_requires_terminal": not bundled_runtime,
        "runtime_dir": str(runtime_dir) if runtime_dir else None,
        "app_bundle_path": app_bundle or None,
        "checks": checks,
    }


def runtime_dir_for(db_path: str | None) -> Path | None:
    if os.environ.get("INTENTOS_RUNTIME_DIR"):
        return Path(os.environ["INTENTOS_RUNTIME_DIR"])
    if db_path:
        path = Path(db_path)
        return path.parent.parent if path.parent.name == "beta" else path.parent
    return None


def check(ok: bool, ready: str, blocked: str, required: bool = True) -> dict[str, Any]:
    return {
        "state": "ok" if ok else "blocked",
        "detail": ready if ok else blocked,
        "required": required,
    }


def env_true(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes"}


def is_writable_dir(path: Path | None) -> bool:
    return bool(path and path.exists() and path.is_dir() and os.access(path, os.W_OK))


def is_readable_path(path: Path) -> bool:
    return path.exists() and os.access(path, os.R_OK)


def app_identity() -> dict[str, str]:
    return {"display_name": APP_DISPLAY_NAME, "bundle_id": APP_BUNDLE_ID, "channel": "trusted_beta"}


def redact_preview(preview: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": preview.get("state"),
        "observed_at": preview.get("observed_at"),
        "app_name": preview.get("app_name"),
        "bundle_id": preview.get("bundle_id"),
        "has_window_title": bool(preview.get("window_title")),
        "domain": preview.get("domain"),
        "source": preview.get("source"),
        "detail": preview.get("detail"),
    }


def recent_errors(conn: sqlite3.Connection) -> list[dict[str, str]]:
    keys = ["native_recorder_last_error", "capture_note", "accessibility_permission_detail"]
    rows = []
    for key in keys:
        value = store.runtime_value(conn, key)
        if value and "Fake" not in value:
            rows.append({"key": key, "detail": " ".join(value.split())[:240]})
    return rows


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
