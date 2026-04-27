"""SQLite persistence and daily review helpers for the dogfood beta."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from intentos.activity import ActivityEvent
from intentos.classifier import BehaviorLabel
from intentos.reporting import event_sample_count


SCHEMA_VERSION = "1"
DEFAULT_RETENTION_DAYS = 30


def connect(path: str | Path) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection, retention_days: int = DEFAULT_RETENTION_DAYS) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS activity_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event_key TEXT NOT NULL UNIQUE,
          source_app TEXT NOT NULL,
          surface TEXT NOT NULL,
          title TEXT NOT NULL,
          started_at TEXT NOT NULL,
          duration_seconds INTEGER NOT NULL,
          url TEXT,
          metadata_json TEXT NOT NULL,
          source_adapter TEXT NOT NULL,
          sample_count INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_activity_events_started
          ON activity_events(started_at);
        CREATE TABLE IF NOT EXISTS classified_segments (
          segment_key TEXT PRIMARY KEY,
          date TEXT NOT NULL,
          source_app TEXT NOT NULL,
          surface TEXT NOT NULL,
          title TEXT NOT NULL,
          url TEXT,
          started_at TEXT NOT NULL,
          duration_seconds INTEGER NOT NULL,
          label TEXT NOT NULL,
          confidence REAL NOT NULL,
          reason TEXT NOT NULL,
          sample_count INTEGER NOT NULL,
          corrected_label TEXT,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS corrections (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          segment_key TEXT NOT NULL,
          corrected_label TEXT NOT NULL,
          scope TEXT NOT NULL,
          apply_to_future INTEGER NOT NULL DEFAULT 0,
          app TEXT NOT NULL,
          surface TEXT NOT NULL,
          domain TEXT,
          title_pattern TEXT,
          url_pattern TEXT,
          created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_corrections_key
          ON corrections(segment_key, created_at);
        CREATE TABLE IF NOT EXISTS settings (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS runtime_status (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        """
    )
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
    return int(cursor.lastrowid or existing_event_id(conn, key))


def events_for_date(conn: sqlite3.Connection, date: str) -> list[ActivityEvent]:
    start = f"{date}T00:00:00"
    end = (datetime.fromisoformat(date) + timedelta(days=1)).date().isoformat()
    rows = conn.execute(
        """
        SELECT * FROM activity_events
        WHERE started_at >= ? AND started_at < ?
        ORDER BY started_at, id
        """,
        (start, f"{end}T00:00:00"),
    ).fetchall()
    return [row_to_event(row) for row in rows]


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
    cutoff = ((now or datetime.now(timezone.utc)) - timedelta(days=days)).isoformat()
    cursor = conn.execute("DELETE FROM activity_events WHERE started_at < ?", (cutoff,))
    conn.execute("DELETE FROM classified_segments WHERE started_at < ?", (cutoff,))
    conn.commit()
    return int(cursor.rowcount)


def delete_all(conn: sqlite3.Connection) -> None:
    for table in ["activity_events", "classified_segments", "corrections", "runtime_status"]:
        conn.execute(f"DELETE FROM {table}")
    set_status(conn, "data_state", "deleted")
    conn.commit()


def set_pause(conn: sqlite3.Connection, paused_until: str) -> None:
    set_setting(conn, "paused_until", paused_until)
    set_status(conn, "capture_state", "paused")


def clear_pause(conn: sqlite3.Connection) -> None:
    set_setting(conn, "paused_until", "")
    set_status(conn, "capture_state", "running")


def status(conn: sqlite3.Connection, db_path: str | None = None) -> dict[str, Any]:
    paused_until = setting(conn, "paused_until", "")
    latest = conn.execute("SELECT MAX(started_at) FROM activity_events").fetchone()[0]
    return {
        "service": {"state": runtime_value(conn, "service_state") or "running"},
        "database": {"path": db_path, "retention_days": int(setting(conn, "retention_days", "30"))},
        "capture": {"state": runtime_value(conn, "capture_state") or "ready"},
        "pause": {"paused": is_paused(paused_until), "paused_until": paused_until or None},
        "extension": {
            "state": runtime_value(conn, "extension_state") or "not_connected",
            "last_event_at": runtime_value(conn, "last_browser_event_at"),
        },
        "last_event_time": latest,
        "row_counts": row_counts(conn),
        "logs": {"service_log": runtime_value(conn, "service_log")},
    }


def set_status(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO runtime_status (key, value, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
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

def segment_key_from_parts(item: dict[str, Any]) -> str:
    url = stable_url_pattern(item.get("url"))
    surface = clean_key(domain_for_url(item.get("url")) or item.get("surface"))
    title = clean_key(item.get("title"))
    return "|".join([clean_key(item.get("source_app")), surface, url or title])

def stable_url_pattern(url: object) -> str:
    if not isinstance(url, str) or not url.strip():
        return ""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path}".rstrip("/")

def domain_for_url(url: object) -> str:
    pattern = stable_url_pattern(url)
    return urlparse(pattern).netloc.removeprefix("www.") if pattern else ""

def clean_key(value: object) -> str:
    return " ".join(value.lower().split()) if isinstance(value, str) else ""

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
        for table in ["activity_events", "classified_segments", "corrections"]
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
