"""Beta recorder helpers that persist accepted ActivityEvent rows."""

from __future__ import annotations

import sqlite3
from datetime import timedelta

from intentos.activity import ActivityEvent
from intentos.beta import store
from intentos.capture.core import parse_timestamp
from intentos.capture.session import event_end


IDLE_THRESHOLD_SECONDS = 5 * 60
LONG_GAP_SECONDS = 10 * 60


def record_event(conn: sqlite3.Connection, event: ActivityEvent) -> int | None:
    idle_seconds = idle_value(event)
    if idle_seconds and idle_seconds >= IDLE_THRESHOLD_SECONDS:
        store.set_status(conn, "capture_state", "away")
        store.set_status(
            conn,
            "capture_note",
            f"ignored idle sample over {IDLE_THRESHOLD_SECONDS // 60} minutes",
        )
        return None

    note_long_gap(conn, event)
    row_id = store.insert_event(conn, event)
    store.set_status(conn, "capture_state", "running")
    return row_id


def note_long_gap(conn: sqlite3.Connection, event: ActivityEvent) -> None:
    row = conn.execute(
        """
        SELECT started_at, duration_seconds FROM activity_events
        ORDER BY started_at DESC, id DESC LIMIT 1
        """
    ).fetchone()
    if not row:
        return
    previous = ActivityEvent("", "", "", row["started_at"], row["duration_seconds"])
    gap = parse_timestamp(event.started_at, "event started_at") - event_end(previous)
    if gap > timedelta(seconds=LONG_GAP_SECONDS):
        store.set_status(conn, "capture_note", f"detected long capture gap: {int(gap.total_seconds())}s")


def idle_value(event: ActivityEvent) -> int | None:
    value = (event.metadata or {}).get("idle_seconds")
    return value if isinstance(value, int) and value > 0 else None
