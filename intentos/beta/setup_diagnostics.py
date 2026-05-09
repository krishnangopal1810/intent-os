"""Setup report and preflight diagnostics for the beta runtime."""

from __future__ import annotations

import os
import platform
import sqlite3
from pathlib import Path
from typing import Any

from intentos.beta import store


APP_DISPLAY_NAME = "IntentOS"
APP_BUNDLE_ID = "local.intentos.trusted"


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
    return {
        "display_name": APP_DISPLAY_NAME,
        "bundle_id": APP_BUNDLE_ID,
        "channel": "trusted_beta",
    }


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
