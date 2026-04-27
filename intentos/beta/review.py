"""Service-backed daily review generation for beta data."""

from __future__ import annotations

import sqlite3
from typing import Any

from intentos.activity import ActivityEvent
from intentos.beta import store
from intentos.classifier import ActivityClassification, BehaviorLabel, classify_event
from intentos.reporting import (
    ClassifiedEvent,
    activity_narrative,
    aggregate_by_label,
    session_to_dict,
    sessionize_classified_events,
)
from intentos.youtube import format_duration, percentage


def daily_review(conn: sqlite3.Connection, date: str, db_path: str | None = None) -> dict[str, Any]:
    events = store.events_for_date(conn, date)
    classified: list[ClassifiedEvent] = []
    corrected_keys = corrected_segment_keys(conn)
    for event in events:
        base = classify_event(event)
        classified.append(ClassifiedEvent(event, correction_for_event(conn, event, base) or base))

    totals = aggregate_by_label(classified)
    total_seconds = sum(totals.values())
    labels = {
        label.value: {
            "seconds": seconds,
            "duration": format_duration(seconds),
            "percentage": percentage(seconds, total_seconds),
        }
        for label, seconds in totals.items()
        if seconds
    }
    items = review_items(classified, corrected_keys)
    write_classified_segments(conn, date, items)
    return {
        "date": date,
        "generated_at": store.utc_now(),
        "status": store.status(conn, db_path),
        "summary": {
            "total_seconds": total_seconds,
            "total_duration": format_duration(total_seconds),
            "labels": labels,
            "narrative": activity_narrative(totals),
        },
        "items": items,
        "intent_mix": labels,
        "top_deep_work": top_items(items, {"deep_work", "learning", "active_creation"}),
        "top_reactive_surfaces": top_items(
            items, {"passive_consumption", "entertainment", "communication"}
        ),
        "low_confidence_segments": [
            item
            for item in items
            if item.get("confidence", 1) < 0.55 or item.get("label") == "unknown"
        ],
    }


def review_items(classified: list[ClassifiedEvent], corrected_keys: set[str]) -> list[dict[str, Any]]:
    items = []
    for session in sessionize_classified_events(classified):
        item = session_to_dict(session)
        key = store.segment_key(session[0].event)
        item["segment_key"] = key
        if key in corrected_keys:
            item["corrected_label"] = item["label"]
        items.append(item)
    return items


def correction_for_event(
    conn: sqlite3.Connection, event: ActivityEvent, base: ActivityClassification
) -> ActivityClassification | None:
    row = conn.execute(
        "SELECT corrected_label FROM corrections WHERE segment_key = ? ORDER BY id DESC LIMIT 1",
        (store.segment_key(event),),
    ).fetchone()
    if not row:
        return None
    return ActivityClassification(
        label=BehaviorLabel(row["corrected_label"]),
        confidence=1.0,
        reason="Corrected by user.",
        scores=base.scores,
    )


def write_classified_segments(conn: sqlite3.Connection, date: str, items: list[dict[str, Any]]) -> None:
    now = store.utc_now()
    for item in items:
        conn.execute(
            """
            INSERT INTO classified_segments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(segment_key) DO UPDATE SET
              label=excluded.label, confidence=excluded.confidence, reason=excluded.reason,
              duration_seconds=excluded.duration_seconds, corrected_label=excluded.corrected_label,
              updated_at=excluded.updated_at
            """,
            (
                item["segment_key"],
                date,
                item["source_app"],
                item["surface"],
                item["title"],
                item.get("url"),
                item["started_at"],
                item["duration_seconds"],
                item["label"],
                item["confidence"],
                item["reason"],
                item.get("sample_count", 1),
                item.get("corrected_label"),
                now,
            ),
        )
    conn.commit()


def corrected_segment_keys(conn: sqlite3.Connection) -> set[str]:
    return {row["segment_key"] for row in conn.execute("SELECT segment_key FROM corrections")}


def top_items(items: list[dict[str, Any]], wanted: set[str]) -> list[dict[str, Any]]:
    return sorted(
        [item for item in items if item.get("label") in wanted],
        key=lambda item: item.get("duration_seconds", 0),
        reverse=True,
    )[:3]
