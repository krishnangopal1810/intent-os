"""Weekly local pattern read model for the beta."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from intentos.beta import daily_state, loop_coach, review
from intentos.youtube import format_duration


def weekly_patterns(
    conn: sqlite3.Connection,
    week_start: str,
    db_path: str | None = None,
) -> dict[str, Any]:
    start = parse_day(week_start)
    days = [(start + timedelta(days=offset)).date().isoformat() for offset in range(7)]
    reports = [review.daily_review(conn, day, db_path) for day in days]
    items = [item for report in reports for item in report.get("items", [])]
    focus = best_focus_window(items)
    leak = recurring_leak(items)
    trust = trust_trend(reports, items)
    intent_days = sum(1 for day in days if daily_state.daily_intent(conn, day))
    review_days = sum(1 for day in days if daily_state.review_checkin(conn, day))
    cards = [
        {
            "kind": "best_focus_window",
            "title": "Best focus window",
            "value": focus["window_label"],
            "detail": focus["detail"],
            "confidence": focus["confidence"],
        },
        {
            "kind": "recurring_leak",
            "title": "Recurring leak",
            "value": leak["surface"],
            "detail": leak["detail"],
            "confidence": leak["confidence"],
        },
        {
            "kind": "trust_improvement",
            "title": "Trust improvement",
            "value": trust["value"],
            "detail": trust["detail"],
            "confidence": trust["confidence"],
        },
    ]
    return {
        "week_start": week_start,
        "week_end": days[-1],
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "best_focus_window": focus,
        "recurring_reactive_surface": leak,
        "correction_trust_trend": trust,
        "intent_days": intent_days,
        "review_days": review_days,
        "narrative": weekly_narrative(focus, leak, trust, intent_days, review_days),
        "patterns": cards,
    }


def best_focus_window(items: list[dict[str, Any]]) -> dict[str, Any]:
    by_hour: dict[int, int] = defaultdict(int)
    for item in items:
        if item.get("label") not in loop_coach.FOCUS_LABELS:
            continue
        by_hour[local_hour(item.get("started_at"))] += int(item.get("duration_seconds") or 0)
    if not by_hour:
        return {
            "window_label": "No focus window yet",
            "duration_seconds": 0,
            "duration": "0s",
            "detail": "Work normally for 20 minutes; the weekly pattern will appear after focused activity lands.",
            "confidence": 0.25,
        }
    hour, seconds = max(by_hour.items(), key=lambda row: row[1])
    label = f"{hour:02d}:00-{(hour + 1) % 24:02d}:00"
    return {
        "window_label": label,
        "duration_seconds": seconds,
        "duration": format_duration(seconds),
        "detail": f"{format_duration(seconds)} of high-value work clustered around this hour.",
        "confidence": 0.75,
    }


def recurring_leak(items: list[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, int] = defaultdict(int)
    for item in items:
        if item.get("label") not in loop_coach.REACTIVE_LABELS | {"communication"}:
            continue
        name = item.get("surface") or item.get("title") or item.get("source_app") or "Reactive surface"
        totals[str(name)] += int(item.get("duration_seconds") or 0)
    if not totals:
        return {
            "surface": "No recurring leak yet",
            "duration_seconds": 0,
            "duration": "0s",
            "detail": "The week has not shown a repeating avoid-side surface.",
            "confidence": 0.3,
        }
    surface, seconds = max(totals.items(), key=lambda row: row[1])
    return {
        "surface": surface,
        "duration_seconds": seconds,
        "duration": format_duration(seconds),
        "detail": f"{surface} repeated for {format_duration(seconds)} this week.",
        "confidence": 0.78,
    }


def trust_trend(reports: list[dict[str, Any]], items: list[dict[str, Any]]) -> dict[str, Any]:
    correction_count = sum(1 for item in items if item.get("corrected_label"))
    low_confidence_count = sum(len(report.get("low_confidence_segments") or []) for report in reports)
    improved = []
    for item in items:
        if item.get("corrected_label"):
            name = item.get("surface") or item.get("source_app") or item.get("title")
            if name and name not in improved:
                improved.append(name)
    if correction_count:
        value = f"{correction_count} correction{'s' if correction_count != 1 else ''}"
        detail = "Future reviews will classify " + ", ".join(improved[:2]) + " better."
        confidence = 0.82
    elif low_confidence_count:
        value = f"{low_confidence_count} unclear row{'s' if low_confidence_count != 1 else ''}"
        detail = "Correct these rows to improve future review accuracy."
        confidence = 0.58
    else:
        value = "Stable labels"
        detail = "No correction backlog is visible this week."
        confidence = 0.68
    return {
        "correction_count": correction_count,
        "low_confidence_count": low_confidence_count,
        "improved_surfaces": improved[:3],
        "value": value,
        "detail": detail,
        "confidence": confidence,
    }


def weekly_narrative(
    focus: dict[str, Any],
    leak: dict[str, Any],
    trust: dict[str, Any],
    intent_days: int,
    review_days: int,
) -> str:
    return (
        f"This week, the clearest focus window was {focus['window_label']}; "
        f"the recurring leak was {leak['surface']}. "
        f"{trust['value']} improved review accuracy. "
        f"{intent_days} planned day{'s' if intent_days != 1 else ''} and "
        f"{review_days} evening review{'s' if review_days != 1 else ''} are on record."
    )


def parse_day(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def local_hour(value: object) -> int:
    if not isinstance(value, str):
        return 0
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).astimezone().hour
    except ValueError:
        return 0
