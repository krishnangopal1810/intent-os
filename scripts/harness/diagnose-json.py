#!/usr/bin/env python3
"""Write a structured, privacy-bounded runtime diagnostic artifact."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PRIVATE_KEYS = {
    "authorization",
    "body",
    "content",
    "cookie",
    "cookies",
    "page_body",
    "password",
    "token",
}


def main() -> int:
    runtime_dir = ROOT / os.environ.get("INTENTOS_RUNTIME_DIR", ".harness/runtime")
    artifact_dir = runtime_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output = artifact_dir / "diagnose.json"
    payload = build_diagnostics(runtime_dir)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"diagnose-json: wrote {output}")
    return 0 if payload["status"] in {"ok", "warning"} else 1


def build_diagnostics(runtime_dir: Path) -> dict[str, Any]:
    app_env_path = runtime_dir / "app.env"
    beta_env_path = runtime_dir / "beta/app.env"
    artifacts = runtime_dir / "artifacts"
    logs = runtime_dir / "logs"
    failures: list[str] = []

    app_env = read_env(app_env_path, failures, required=False)
    beta_env = read_env(beta_env_path, failures, required=False)
    beta_db = Path(beta_env.get("INTENTOS_BETA_DB") or runtime_dir / "beta/intentos.sqlite")

    payload = {
        "status": "ok",
        "generated_at": utc_now(),
        "runtime_dir": rel(runtime_dir),
        "app": {
            "env_path": rel(app_env_path),
            "env_present": app_env_path.is_file(),
            "url": app_env.get("INTENTOS_APP_URL"),
            "mode": app_env.get("INTENTOS_APP_MODE"),
            "data_mode": app_env.get("INTENTOS_APP_DATA_MODE"),
            "capture_mode": app_env.get("INTENTOS_CAPTURE_MODE"),
        },
        "beta": {
            "env_path": rel(beta_env_path),
            "env_present": beta_env_path.is_file(),
            "service_url": beta_env.get("INTENTOS_BETA_SERVICE_URL"),
            "ui_url": beta_env.get("INTENTOS_BETA_UI_URL"),
            "db_path": rel(beta_db),
            "status": beta_db_status(beta_db, failures),
        },
        "structured_events": read_events(logs / "events.jsonl", failures),
        "logs": {
            name: log_summary(logs / name)
            for name in [
                "app.log",
                "events.jsonl",
                "live-capture.log",
                "live-session-capture.log",
                "beta-service.log",
                "beta-native-recorder.log",
                "beta-fake-bridge.log",
            ]
        },
        "artifacts": artifact_summary(artifacts),
        "failures": failures,
        "recommended_next_commands": recommended_commands(failures, beta_env_path.is_file()),
    }
    payload["status"] = "failed" if any("error:" in item for item in failures) else (
        "warning" if failures else "ok"
    )
    return payload


def beta_db_status(db_path: Path, failures: list[str]) -> dict[str, Any] | None:
    if not db_path.is_file():
        failures.append(f"beta db not found at {rel(db_path)}")
        return None
    try:
        from intentos.beta import store

        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            return scrub(store.status(conn, str(db_path)))
        finally:
            conn.close()
    except Exception as exc:
        failures.append(f"error: failed to read beta db status: {exc}")
        return None


def read_env(path: Path, failures: list[str], required: bool) -> dict[str, str]:
    if not path.is_file():
        if required:
            failures.append(f"missing env file {rel(path)}")
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def read_events(path: Path, failures: list[str], limit: int = 40) -> dict[str, Any]:
    if not path.is_file():
        return {"path": rel(path), "present": False, "items": []}
    items = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines[-limit:]:
        if not line.strip():
            continue
        try:
            items.append(scrub(json.loads(line)))
        except json.JSONDecodeError:
            failures.append(f"error: invalid structured event JSON in {rel(path)}")
            break
    return {"path": rel(path), "present": True, "line_count": len(lines), "items": items}


def log_summary(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"path": rel(path), "present": False}
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    recent = lines[-120:]
    return {
        "path": rel(path),
        "present": True,
        "bytes": path.stat().st_size,
        "line_count": len(lines),
        "recent_error_count": count_terms(recent, ["error", "failed", "traceback"]),
        "recent_warning_count": count_terms(recent, ["warning", "blocked", "stale"]),
    }


def artifact_summary(path: Path) -> list[dict[str, Any]]:
    if not path.is_dir():
        return []
    items = []
    for item in sorted(path.iterdir()):
        if item.is_file():
            items.append({"path": rel(item), "bytes": item.stat().st_size})
    return items


def scrub(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            normalized = str(key).lower()
            if normalized in PRIVATE_KEYS:
                cleaned[key] = "[redacted]"
            else:
                cleaned[key] = scrub(item)
        return cleaned
    if isinstance(value, list):
        return [scrub(item) for item in value]
    return value


def count_terms(lines: list[str], terms: list[str]) -> int:
    count = 0
    for line in lines:
        lowered = line.lower()
        if any(term in lowered for term in terms):
            count += 1
    return count


def recommended_commands(failures: list[str], beta_env_present: bool) -> list[str]:
    commands = ["make diagnose"]
    if beta_env_present:
        commands.append("make beta-status")
    if failures:
        commands.append("make validate-beta")
    commands.append("make verify")
    return commands


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
