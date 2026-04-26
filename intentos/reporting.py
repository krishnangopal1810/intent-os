"""Reporting for generic IntentOS activity events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from intentos.activity import ActivityEvent
from intentos.classifier import ActivityClassification, BehaviorLabel, classify_event
from intentos.youtube import format_duration, percentage


@dataclass(frozen=True)
class ClassifiedEvent:
    event: ActivityEvent
    classification: ActivityClassification


def classify_events(events: Iterable[ActivityEvent]) -> list[ClassifiedEvent]:
    return [
        ClassifiedEvent(event=event, classification=classify_event(event))
        for event in events
    ]


def aggregate_by_label(items: Iterable[ClassifiedEvent]) -> dict[BehaviorLabel, int]:
    totals = {label: 0 for label in BehaviorLabel}
    for item in items:
        totals[item.classification.label] += item.event.duration_seconds
    return totals


def activity_report(events: Iterable[ActivityEvent]) -> dict[str, Any]:
    classified = classify_events(events)
    totals = aggregate_by_label(classified)
    total_seconds = sum(totals.values())
    sessions = sessionize_classified_events(classified)
    labels = {
        label.value: {
            "seconds": seconds,
            "duration": format_duration(seconds),
            "percentage": percentage(seconds, total_seconds),
        }
        for label, seconds in totals.items()
        if seconds
    }
    return {
        "summary": {
            "total_seconds": total_seconds,
            "total_duration": format_duration(total_seconds),
            "labels": labels,
            "narrative": activity_narrative(totals),
        },
        "items": [session_to_dict(session) for session in sessions],
    }


def sessionize_classified_events(items: list[ClassifiedEvent]) -> list[list[ClassifiedEvent]]:
    sessions: list[list[ClassifiedEvent]] = []
    current: list[ClassifiedEvent] = []
    current_key: tuple[str, str, str, str, str] | None = None

    for item in items:
        key = session_key(item)
        if current and key != current_key:
            sessions.append(current)
            current = []
        current.append(item)
        current_key = key

    if current:
        sessions.append(current)
    return sessions


def session_key(item: ClassifiedEvent) -> tuple[str, str, str, str, str]:
    event = item.event
    url = (event.url or "").lower()
    title_key = "" if url else event.title.lower()
    return (
        event.source_app.lower(),
        event.surface.lower(),
        url,
        title_key,
        item.classification.label.value,
    )


def session_to_dict(session: list[ClassifiedEvent]) -> dict[str, object]:
    first = session[0]
    duration_seconds = sum(item.event.duration_seconds for item in session)
    confidence = sum(item.classification.confidence for item in session) / len(session)
    return {
        "source_app": first.event.source_app,
        "surface": first.event.surface,
        "title": first.event.title,
        "started_at": first.event.started_at,
        "duration_seconds": duration_seconds,
        "duration": format_duration(duration_seconds),
        "sample_count": len(session),
        "url": first.event.url,
        "label": first.classification.label.value,
        "confidence": round(confidence, 2),
        "reason": first.classification.reason,
        "metadata": first.event.metadata or {},
    }


def activity_narrative(totals: dict[BehaviorLabel, int]) -> str:
    total_seconds = sum(totals.values())
    if total_seconds == 0:
        return "No activity was available to classify."

    ranked = sorted(
        ((label, seconds) for label, seconds in totals.items() if seconds),
        key=lambda item: item[1],
        reverse=True,
    )
    leader, leader_seconds = ranked[0]
    return (
        f"You spent {format_duration(total_seconds)} across tracked apps. "
        f"The largest behavior bucket was {leader.value} at "
        f"{round(percentage(leader_seconds, total_seconds))}%."
    )
