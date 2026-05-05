"""Local HTTP API for the dogfood beta dashboard and Chrome bridge."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from intentos.beta import daily_loop, daily_state, permissions, recorder, review, setup_flow, state, store, weekly_patterns
from intentos.beta.extension import chrome_event_to_activity
from intentos.beta.service_helpers import (
    clear_generated_artifacts,
    event_to_dict,
    optional_text,
    parsed_path,
    require_text,
    today,
)
from intentos.capture.privacy import load_privacy_policy

class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


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
                elif path == "/api/setup-report":
                    self.send_json(self.with_conn(lambda conn: {
                        "status": "ok",
                        "setup_report": setup_flow.setup_report(
                            conn,
                            str(config.db_path),
                            config.runtime_dir,
                            store.status(conn),
                        ),
                    }))
                elif path == "/api/daily-review":
                    date = query.get("date", [today()])[0]
                    self.send_json(
                        self.with_conn(lambda conn: review.daily_review(conn, date, str(config.db_path)))
                    )
                elif path == "/api/daily-loop":
                    date = query.get("date", [today()])[0]
                    self.send_json(
                        self.with_conn(lambda conn: daily_loop.daily_loop(conn, date, str(config.db_path)))
                    )
                elif path == "/api/weekly-patterns":
                    week_start = query.get("week_start", [today()])[0]
                    self.send_json(
                        self.with_conn(
                            lambda conn: weekly_patterns.weekly_patterns(
                                conn,
                                week_start,
                                str(config.db_path),
                            )
                        )
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
                    removed = clear_generated_artifacts(config.runtime_dir)
                    self.send_json({"status": "deleted", "cleared_artifacts": removed})
                elif path == "/api/onboarding":
                    self.handle_onboarding(payload)
                elif path == "/api/daily-intent":
                    self.handle_daily_intent(payload)
                elif path == "/api/review-checkin":
                    self.handle_review_checkin(payload)
                elif path == "/api/focus-rescue-action":
                    self.handle_focus_rescue_action(payload)
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

        def handle_daily_intent(self, payload: dict[str, Any]) -> None:
            date = optional_text(payload, "date") or today()
            focus_text = require_text(payload, "focus_text")
            avoid_text = require_text(payload, "avoid_text")
            note = optional_text(payload, "note")
            def write(conn: sqlite3.Connection) -> dict[str, Any]:
                intent = daily_state.upsert_daily_intent(
                    conn,
                    date,
                    focus_text,
                    avoid_text,
                    note,
                )
                store.set_status_once(conn, "activation_intent_set_at", store.utc_now())
                return intent

            intent = self.with_conn(write)
            self.send_json({"status": "saved", "intent": intent})

        def handle_review_checkin(self, payload: dict[str, Any]) -> None:
            date = optional_text(payload, "date") or today()
            outcome = require_text(payload, "outcome")
            reflection_text = optional_text(payload, "reflection_text")
            next_adjustment = optional_text(payload, "next_adjustment")
            def write(conn: sqlite3.Connection) -> dict[str, Any]:
                checkin = daily_state.upsert_review_checkin(
                    conn,
                    date,
                    outcome,
                    reflection_text,
                    next_adjustment,
                )
                store.set_status_once(conn, "activation_review_completed_at", store.utc_now())
                return checkin

            checkin = self.with_conn(write)
            self.send_json({"status": "saved", "review_checkin": checkin})

        def handle_focus_rescue_action(self, payload: dict[str, Any]) -> None:
            date = optional_text(payload, "date") or today()
            rescue_key = require_text(payload, "rescue_key")
            action = require_text(payload, "action")
            evidence_id = optional_text(payload, "evidence_id")
            note = optional_text(payload, "note")

            def write(conn: sqlite3.Connection) -> dict[str, Any]:
                row = daily_state.record_focus_rescue_action(
                    conn,
                    date,
                    rescue_key,
                    action,
                    evidence_id,
                    note,
                )
                result: dict[str, Any] = {"status": "recorded", "action": row}
                if action != "shown":
                    store.set_status_once(conn, "activation_first_recovery_action_at", store.utc_now())
                if action == "pause_capture":
                    paused_until = (
                        datetime.now(timezone.utc) + timedelta(minutes=15)
                    ).isoformat().replace("+00:00", "Z")
                    store.set_pause(conn, paused_until)
                    result["pause"] = {"status": "paused", "paused_until": paused_until}
                return result

            self.send_json(self.with_conn(write))

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
        store.checkpoint(conn, "PASSIVE")
        store.set_status(conn, "service_state", "running")
        store.set_status(conn, "service_started_at", store.utc_now())
        setup_flow.mark_milestone(conn, "opened")
        store.set_status(conn, "capture_state", "ready")
        store.set_status(conn, "capture_note", "")
        if config.service_log:
            store.set_status(conn, "service_log", str(config.service_log))
    server = ReusableThreadingHTTPServer(
        ("127.0.0.1", config.port),
        make_handler(config),
    )
    print(f"beta-service: serving http://127.0.0.1:{config.port}", flush=True)
    server.serve_forever()

def onboarding_payload(conn: sqlite3.Connection) -> dict[str, Any]:
    status_payload = store.status(conn)
    return {
        "onboarding": setup_flow.enrich_onboarding(conn, state.onboarding(conn), status_payload),
        "status": status_payload,
    }
