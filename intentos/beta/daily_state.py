"""SQLite persistence for the sticky daily loop."""

from __future__ import annotations

import sqlite3
from typing import Any

from intentos.beta import store

FOCUS_RESCUE_ACTIONS = {
    "shown",
    "return_to_focus",
    "continue_intentionally",
    "pause_capture",
    "corrected_evidence",
}


def upsert_daily_intent(
    conn: sqlite3.Connection,
    date: str,
    focus_text: str,
    avoid_text: str,
    note: str = "",
) -> dict[str, Any]:
    focus = required_text(focus_text, "focus_text")
    avoid = required_text(avoid_text, "avoid_text")
    now = store.utc_now()
    conn.execute(
        """
        INSERT INTO daily_intents (
          date, focus_text, avoid_text, note, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
          focus_text=excluded.focus_text,
          avoid_text=excluded.avoid_text,
          note=excluded.note,
          updated_at=excluded.updated_at
        """,
        (date, focus, avoid, clean_optional_text(note), now, now),
    )
    conn.commit()
    return daily_intent(conn, date) or {}


def daily_intent(conn: sqlite3.Connection, date: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT date, focus_text, avoid_text, note, created_at, updated_at
        FROM daily_intents WHERE date = ?
        """,
        (date,),
    ).fetchone()
    return dict(row) if row else None


def upsert_review_checkin(
    conn: sqlite3.Connection,
    date: str,
    outcome: str,
    reflection_text: str = "",
    next_adjustment: str = "",
) -> dict[str, Any]:
    result = required_text(outcome, "outcome")
    now = store.utc_now()
    conn.execute(
        """
        INSERT INTO review_checkins (
          date, outcome, reflection_text, next_adjustment, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
          outcome=excluded.outcome,
          reflection_text=excluded.reflection_text,
          next_adjustment=excluded.next_adjustment,
          updated_at=excluded.updated_at
        """,
        (
            date,
            result,
            clean_optional_text(reflection_text),
            clean_optional_text(next_adjustment),
            now,
            now,
        ),
    )
    conn.commit()
    return review_checkin(conn, date) or {}


def review_checkin(conn: sqlite3.Connection, date: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT date, outcome, reflection_text, next_adjustment, created_at, updated_at
        FROM review_checkins WHERE date = ?
        """,
        (date,),
    ).fetchone()
    return dict(row) if row else None


def record_focus_rescue_action(
    conn: sqlite3.Connection,
    date: str,
    rescue_key: str,
    action: str,
    evidence_id: str = "",
    note: str = "",
) -> dict[str, Any]:
    day = required_text(date, "date")
    key = required_text(rescue_key, "rescue_key")
    name = required_text(action, "action")
    if name not in FOCUS_RESCUE_ACTIONS:
        allowed = ", ".join(sorted(FOCUS_RESCUE_ACTIONS))
        raise ValueError(f"action must be one of: {allowed}")
    now = store.utc_now()
    cursor = conn.execute(
        """
        INSERT INTO focus_rescue_actions (
          date, rescue_key, action, evidence_id, note, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            day,
            key,
            name,
            clean_optional_text(evidence_id),
            clean_optional_text(note),
            now,
        ),
    )
    conn.commit()
    row = conn.execute(
        """
        SELECT id, date, rescue_key, action, evidence_id, note, created_at
        FROM focus_rescue_actions WHERE id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()
    return dict(row) if row else {}


def latest_focus_rescue_action(
    conn: sqlite3.Connection,
    date: str,
    rescue_key: str | None,
) -> dict[str, Any] | None:
    if not rescue_key:
        return None
    row = conn.execute(
        """
        SELECT id, date, rescue_key, action, evidence_id, note, created_at
        FROM focus_rescue_actions
        WHERE date = ? AND rescue_key = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (date, rescue_key),
    ).fetchone()
    return dict(row) if row else None


def required_text(value: str, field: str) -> str:
    text = value.strip() if isinstance(value, str) else ""
    if not text:
        raise ValueError(f"{field} must be non-empty text")
    return text


def clean_optional_text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""
