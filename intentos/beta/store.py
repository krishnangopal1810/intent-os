"""SQLite persistence and daily review helpers for the dogfood beta."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from intentos.activity import ActivityEvent
from intentos.beta.db_health import checkpoint, db_file_stats, quick_check
from intentos.beta.keys import clean_key, domain_for_url, segment_key_from_parts, stable_url_pattern
from intentos.beta.schema import DDL
from intentos.classifier import BehaviorLabel
from intentos.reporting import event_sample_count


SCHEMA_VERSION = "1"
DEFAULT_RETENTION_DAYS = 30


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            super().__exit__(exc_type, exc, tb)
        finally:
            self.close()
        return False


def connect(path: str | Path) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection, retention_days: int = DEFAULT_RETENTION_DAYS) -> None:
    conn.executescript(DDL)
    set_setting(conn, "schema_version", SCHEMA_VERSION, overwrite=False)
    set_setting(conn, "retention_days", str(retention_days), overwrite=False)
    set_setting(conn, "privacy_settings_version", "metadata-only-v1", overwrite=False)
    conn.commit()


def insert_event(conn: sqlite3.Connection, event: ActivityEvent, now: str | None = None) -> int:
    metadata = event.metadata or {}
    key = event_key(event)
    created_at = now or utc_now()
    source_adapter = str(metadata.get("source") or metadata.get("adapter") or "unknown")
    sample_count = event_sample_count(event)
    cursor = conn.execute(
        """
        INSERT OR IGNORE INTO activity_events (
          event_key, source_app, surface, title, started_at, duration_seconds,
          url, metadata_json, source_adapter, sample_count, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            key,
            event.source_app,
            event.surface,
            event.title,
            event.started_at,
            event.duration_seconds,
            event.url,
            json.dumps(metadata, sort_keys=True),
            source_adapter,
            sample_count,
            created_at,
        ),
    )
    conn.commit()
    if cursor.lastrowid and int(cursor.lastrowid) % 100 == 0:
        checkpoint(conn, "PASSIVE")
    return int(cursor.lastrowid or existing_event_id(conn, key))


def events_for_date(conn: sqlite3.Connection, date: str) -> list[ActivityEvent]:
    start, end = local_day_utc_bounds(date)
    rows = conn.execute(
        """
        SELECT * FROM activity_events
        WHERE started_at >= ? AND started_at < ?
        ORDER BY started_at, id
        """,
        (start, end),
    ).fetchall()
    return [row_to_event(row) for row in rows]

def local_day_utc_bounds(date: str) -> tuple[str, str]:
    local_zone = datetime.now().astimezone().tzinfo
    start = datetime.fromisoformat(date).replace(tzinfo=local_zone)
    end = start + timedelta(days=1)
    return utc_bound(start), utc_bound(end)

def utc_bound(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def add_correction(
    conn: sqlite3.Connection,
    segment: dict[str, Any],
    corrected_label: str,
    apply_to_future: bool = False,
) -> str:
    label = BehaviorLabel(corrected_label).value
    key = segment.get("segment_key") or segment_key_from_parts(segment)
    now = utc_now()
    conn.execute(
        """
        INSERT INTO corrections (
          segment_key, corrected_label, scope, apply_to_future, app, surface,
          domain, title_pattern, url_pattern, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            key,
            label,
            "future_match" if apply_to_future else "segment",
            1 if apply_to_future else 0,
            clean_key(segment.get("source_app")),
            clean_key(segment.get("surface")),
            domain_for_url(segment.get("url")),
            clean_key(segment.get("title")),
            stable_url_pattern(segment.get("url")),
            now,
        ),
    )
    conn.commit()
    return key


def cleanup_old_events(conn: sqlite3.Connection, now: datetime | None = None) -> int:
    days = int(setting(conn, "retention_days", str(DEFAULT_RETENTION_DAYS)))
    cutoff_time = (now or datetime.now(timezone.utc)) - timedelta(days=days)
    cutoff = cutoff_time.isoformat()
    cutoff_date = cutoff_time.date().isoformat()
    cursor = conn.execute("DELETE FROM activity_events WHERE started_at < ?", (cutoff,))
    conn.execute("DELETE FROM classified_segments WHERE started_at < ?", (cutoff,))
    conn.execute("DELETE FROM daily_intents WHERE date < ?", (cutoff_date,))
    conn.execute("DELETE FROM review_checkins WHERE date < ?", (cutoff_date,))
    conn.execute("DELETE FROM focus_rescue_actions WHERE date < ?", (cutoff_date,))
    conn.commit()
    if cursor.rowcount:
        checkpoint(conn, "PASSIVE")
    return int(cursor.rowcount)


def delete_all(conn: sqlite3.Connection) -> None:
    for table in [
        "activity_events",
        "classified_segments",
        "corrections",
        "daily_intents",
        "review_checkins",
        "focus_rescue_actions",
    ]:
        conn.execute(f"DELETE FROM {table}")
    set_status(conn, "data_state", "deleted")
    conn.commit()
    checkpoint(conn, "TRUNCATE")


def set_pause(conn: sqlite3.Connection, paused_until: str) -> None:
    set_setting(conn, "paused_until", paused_until)
    set_status(conn, "capture_state", "paused")


def clear_pause(conn: sqlite3.Connection) -> None:
    set_setting(conn, "paused_until", "")
    set_status(conn, "capture_state", "running")


def status(conn: sqlite3.Connection, db_path: str | None = None) -> dict[str, Any]:
    from intentos.beta import state

    return state.status(conn, db_path)


def set_status(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO runtime_status (key, value, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """,
        (key, value, utc_now()),
    )
    conn.commit()


def set_status_once(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO runtime_status (key, value, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
          value=CASE
            WHEN runtime_status.value = '' THEN excluded.value
            ELSE runtime_status.value
          END,
          updated_at=CASE
            WHEN runtime_status.value = '' THEN excluded.updated_at
            ELSE runtime_status.updated_at
          END
        """,
        (key, value, utc_now()),
    )
    conn.commit()


def set_setting(conn: sqlite3.Connection, key: str, value: str, overwrite: bool = True) -> None:
    if overwrite:
        conn.execute(
            """
            INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """,
            (key, value, utc_now()),
        )
    else:
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, utc_now()),
        )


def event_key(event: ActivityEvent) -> str:
    return hashlib.sha256(json.dumps(asdict(event), sort_keys=True).encode()).hexdigest()


def segment_key(event: ActivityEvent) -> str:
    return segment_key_from_parts(asdict(event))


def row_to_event(row: sqlite3.Row) -> ActivityEvent:
    return ActivityEvent(
        row["source_app"],
        row["surface"],
        row["title"],
        row["started_at"],
        row["duration_seconds"],
        row["url"],
        json.loads(row["metadata_json"]),
    )

def row_counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in [
            "activity_events",
            "classified_segments",
            "corrections",
            "focus_rescue_actions",
        ]
    }

def setting(conn: sqlite3.Connection, key: str, default: str) -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default

def runtime_value(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM runtime_status WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None

def existing_event_id(conn: sqlite3.Connection, key: str) -> int:
    row = conn.execute("SELECT id FROM activity_events WHERE event_key = ?", (key,)).fetchone()
    return int(row["id"]) if row else 0

def is_paused(paused_until: str) -> bool:
    if not paused_until:
        return False
    try:
        return datetime.fromisoformat(paused_until.replace("Z", "+00:00")) > datetime.now(timezone.utc)
    except ValueError:
        return False

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
