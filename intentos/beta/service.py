"""Local HTTP API for the dogfood beta dashboard and Chrome bridge."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from intentos.beta import permissions, recorder, review, state, store
from intentos.beta.extension import chrome_event_to_activity
from intentos.capture.privacy import load_privacy_policy


@dataclass(frozen=True)
class ServiceConfig:
    db_path: Path
    privacy_policy_path: Path
    port: int
    retention_days: int = store.DEFAULT_RETENTION_DAYS
    service_log: Path | None = None
    runtime_dir: Path | None = None
    permission_mode: str = "real"
    allow_system_open: bool = True


def make_handler(config: ServiceConfig):
    class BetaHandler(BaseHTTPRequestHandler):
        server_version = "IntentOSBeta/1"

        def do_OPTIONS(self) -> None:
            self.send_json({"status": "ok"})

        def do_GET(self) -> None:
            try:
                path, query = parsed_path(self.path)
                if path == "/api/status":
                    self.send_json(self.with_conn(lambda conn: store.status(conn, str(config.db_path))))
                elif path == "/api/onboarding":
                    self.send_json(self.with_conn(lambda conn: onboarding_payload(conn)))
                elif path == "/api/daily-review":
                    date = query.get("date", [today()])[0]
                    self.send_json(
                        self.with_conn(lambda conn: review.daily_review(conn, date, str(config.db_path)))
                    )
                elif path == "/api/events":
                    date = query.get("date", [today()])[0]
                    events = self.with_conn(lambda conn: store.events_for_date(conn, date))
                    self.send_json({"date": date, "items": [event_to_dict(event) for event in events]})
                else:
                    self.send_error(404, "unknown beta endpoint")
            except Exception as exc:  # pragma: no cover - smoke diagnostics
                self.send_json({"error": str(exc)}, status=500)

        def do_POST(self) -> None:
            try:
                path, _ = parsed_path(self.path)
                payload = self.read_json()
                if path == "/api/browser-event":
                    self.handle_browser_event(payload)
                elif path == "/api/extension-heartbeat":
                    self.handle_extension_heartbeat(payload)
                elif path == "/api/corrections":
                    self.handle_correction(payload)
                elif path == "/api/pause":
                    self.handle_pause(payload)
                elif path == "/api/resume":
                    self.with_conn(store.clear_pause)
                    self.send_json({"status": "resumed"})
                elif path == "/api/delete-local-data":
                    self.with_conn(store.delete_all)
                    self.send_json({"status": "deleted"})
                elif path == "/api/onboarding":
                    self.handle_onboarding(payload)
                elif path == "/api/permissions/check":
                    self.send_json(
                        self.with_conn(
                            lambda conn: permissions.run_check(
                                conn, config.permission_mode, str(config.db_path)
                            )
                        )
                    )
                elif path == "/api/open-system-settings":
                    self.handle_open_system_settings(payload)
                else:
                    self.send_error(404, "unknown beta endpoint")
            except ValueError as exc:
                self.send_json({"error": str(exc)}, status=400)
            except Exception as exc:  # pragma: no cover - smoke diagnostics
                self.send_json({"error": str(exc)}, status=500)

        def handle_browser_event(self, payload: dict[str, Any]) -> None:
            policy = load_privacy_policy(config.privacy_policy_path)
            event = chrome_event_to_activity(payload, policy)
            if event is None:
                self.send_json({"status": "ignored"})
                return
            def write(conn: sqlite3.Connection) -> int | None:
                row_id = recorder.record_event(conn, event)
                now = store.utc_now()
                store.set_status(conn, "extension_state", "posting_events")
                store.set_status(conn, "extension_last_seen_at", now)
                store.set_status(conn, "last_browser_event_at", event.started_at)
                return row_id
            row_id = self.with_conn(write)
            self.send_json({"status": "accepted", "event_id": row_id})

        def handle_extension_heartbeat(self, payload: dict[str, Any]) -> None:
            version = payload.get("version")
            def write(conn: sqlite3.Connection) -> None:
                store.set_status(conn, "extension_state", "connected")
                store.set_status(conn, "extension_last_seen_at", store.utc_now())
                if isinstance(version, str) and version.strip():
                    store.set_status(conn, "extension_version", version.strip())
            self.with_conn(write)
            self.send_json({"status": "connected"})

        def handle_correction(self, payload: dict[str, Any]) -> None:
            label = require_text(payload, "corrected_label")
            segment = payload.get("segment")
            if not isinstance(segment, dict):
                raise ValueError("segment must be an object")
            apply_future = bool(payload.get("apply_to_future", False))
            key = self.with_conn(lambda conn: store.add_correction(conn, segment, label, apply_future))
            self.send_json({"status": "corrected", "segment_key": key})

        def handle_pause(self, payload: dict[str, Any]) -> None:
            minutes = payload.get("minutes", 15)
            if not isinstance(minutes, int) or minutes <= 0:
                raise ValueError("minutes must be a positive integer")
            paused_until = (
                datetime.now(timezone.utc) + timedelta(minutes=minutes)
            ).isoformat().replace("+00:00", "Z")
            self.with_conn(lambda conn: store.set_pause(conn, paused_until))
            self.send_json({"status": "paused", "paused_until": paused_until})

        def handle_onboarding(self, payload: dict[str, Any]) -> None:
            action = require_text(payload, "action")
            minutes = payload.get("minutes", 240)
            if not isinstance(minutes, int):
                raise ValueError("minutes must be an integer")
            self.send_json(self.with_conn(lambda conn: state.update_onboarding(conn, action, minutes)))

        def handle_open_system_settings(self, payload: dict[str, Any]) -> None:
            target = require_text(payload, "target")
            runtime_dir = config.runtime_dir or config.db_path.parent.parent
            self.send_json(
                permissions.open_settings_target(target, runtime_dir, config.allow_system_open)
            )

        def read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError("request body must be a JSON object")
            return payload

        def with_conn(self, fn):
            conn = store.connect(config.db_path)
            try:
                store.init_db(conn, config.retention_days)
                return fn(conn)
            finally:
                conn.close()

        def send_json(self, payload: object, status: int = 200) -> None:
            data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, fmt: str, *args: object) -> None:
            print(f"beta-service: {self.address_string()} {fmt % args}", flush=True)

    return BetaHandler


def serve(config: ServiceConfig) -> None:
    with store.connect(config.db_path) as conn:
        store.init_db(conn, config.retention_days)
        store.cleanup_old_events(conn)
        store.set_status(conn, "service_state", "running")
        store.set_status(conn, "capture_state", "ready")
        store.set_status(conn, "capture_note", "")
        if config.service_log:
            store.set_status(conn, "service_log", str(config.service_log))
    server = ThreadingHTTPServer(("127.0.0.1", config.port), make_handler(config))
    print(f"beta-service: serving http://127.0.0.1:{config.port}", flush=True)
    server.serve_forever()


def onboarding_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    return {
        "onboarding": state.onboarding(conn),
        "status": store.status(conn),
    }


def parsed_path(path: str) -> tuple[str, dict[str, list[str]]]:
    parsed = urlparse(path)
    return parsed.path, parse_qs(parsed.query)


def today() -> str:
    return datetime.now().astimezone().date().isoformat()


def require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be non-empty text")
    return value.strip()


def event_to_dict(event) -> dict[str, object]:
    return {
        "source_app": event.source_app,
        "surface": event.surface,
        "title": event.title,
        "started_at": event.started_at,
        "duration_seconds": event.duration_seconds,
        "url": event.url,
        "metadata": event.metadata or {},
    }
