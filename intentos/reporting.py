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
        "items": [
            {
                "source_app": item.event.source_app,
                "surface": item.event.surface,
                "title": item.event.title,
                "duration_seconds": item.event.duration_seconds,
                "label": item.classification.label.value,
                "confidence": item.classification.confidence,
                "reason": item.classification.reason,
            }
            for item in classified
        ],
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
