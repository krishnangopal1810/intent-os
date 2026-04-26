"""Local YouTube activity classification for the IntentOS MVP."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable


class Label(str, Enum):
    LEARNING = "learning"
    ENTERTAINMENT = "entertainment"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class YouTubeActivity:
    title: str
    url: str
    channel: str | None
    watched_at: str
    duration_seconds: int
    description: str | None = None


@dataclass(frozen=True)
class Classification:
    label: Label
    confidence: float
    reason: str
    learning_score: int
    entertainment_score: int


@dataclass(frozen=True)
class ClassifiedActivity:
    activity: YouTubeActivity
    classification: Classification


@dataclass(frozen=True)
class Summary:
    total_seconds: int
    learning_seconds: int
    entertainment_seconds: int
    unknown_seconds: int

    @property
    def passive_consumption_percentage(self) -> float:
        return percentage(self.entertainment_seconds, self.total_seconds)

    @property
    def learning_percentage(self) -> float:
        return percentage(self.learning_seconds, self.total_seconds)

    @property
    def unknown_percentage(self) -> float:
        return percentage(self.unknown_seconds, self.total_seconds)


LEARNING_CUES = {
    "advanced": 1,
    "architecture": 2,
    "asyncio": 3,
    "build": 2,
    "building": 2,
    "course": 3,
    "deep dive": 3,
    "engineering": 3,
    "guide": 2,
    "lecture": 3,
    "llm": 2,
    "local inference": 3,
    "model": 1,
    "ollama": 2,
    "python": 3,
    "step by step": 2,
    "technical": 2,
    "tutorial": 3,
}

ENTERTAINMENT_CUES = {
    "celebrity": 3,
    "clips": 2,
    "compilation": 3,
    "drama": 3,
    "funny": 2,
    "gaming": 3,
    "highlights": 3,
    "internet culture": 2,
    "laugh": 3,
    "pop": 2,
    "reaction": 2,
    "reactions": 2,
    "recap": 1,
    "recommendations": 3,
    "viral": 2,
}


def load_activities(path: str | Path) -> list[YouTubeActivity]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("watch history must be a JSON array")
    return [parse_activity(item, index) for index, item in enumerate(raw)]


def parse_activity(item: Any, index: int) -> YouTubeActivity:
    if not isinstance(item, dict):
        raise ValueError(f"item {index} must be an object")

    title = require_text(item, "title", index)
    url = require_text(item, "url", index)
    watched_at = require_text(item, "watched_at", index)
    duration = item.get("duration_seconds")
    if not isinstance(duration, int) or duration <= 0:
        raise ValueError(f"item {index} duration_seconds must be a positive integer")

    return YouTubeActivity(
        title=title,
        url=url,
        channel=optional_text(item, "channel", index),
        watched_at=watched_at,
        duration_seconds=duration,
        description=optional_text(item, "description", index),
    )


def require_text(item: dict[str, Any], key: str, index: int) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"item {index} {key} must be non-empty text")
    return value.strip()


def optional_text(item: dict[str, Any], key: str, index: int) -> str | None:
    value = item.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"item {index} {key} must be text when present")
    value = value.strip()
    return value or None


def classify_activity(activity: YouTubeActivity) -> Classification:
    text = " ".join(
        part
        for part in [activity.title, activity.channel or "", activity.description or ""]
        if part
    ).lower()
    learning_matches = score_cues(text, LEARNING_CUES)
    entertainment_matches = score_cues(text, ENTERTAINMENT_CUES)
    learning_score = sum(learning_matches.values())
    entertainment_score = sum(entertainment_matches.values())

    if learning_score == 0 and entertainment_score == 0:
        return Classification(
            label=Label.UNKNOWN,
            confidence=0.35,
            reason="No strong learning or entertainment cues were present.",
            learning_score=0,
            entertainment_score=0,
        )

    if abs(learning_score - entertainment_score) <= 1:
        return Classification(
            label=Label.UNKNOWN,
            confidence=0.45,
            reason=(
                "Learning and entertainment cues were too close to force a label: "
                f"{format_cues(learning_matches, entertainment_matches)}."
            ),
            learning_score=learning_score,
            entertainment_score=entertainment_score,
        )

    label = Label.LEARNING if learning_score > entertainment_score else Label.ENTERTAINMENT
    gap = abs(learning_score - entertainment_score)
    confidence = min(0.95, 0.55 + (gap * 0.08))
    return Classification(
        label=label,
        confidence=round(confidence, 2),
        reason=format_reason(label, learning_matches, entertainment_matches),
        learning_score=learning_score,
        entertainment_score=entertainment_score,
    )


def score_cues(text: str, cues: dict[str, int]) -> dict[str, int]:
    return {cue: weight for cue, weight in cues.items() if cue in text}


def format_reason(
    label: Label, learning_matches: dict[str, int], entertainment_matches: dict[str, int]
) -> str:
    if label is Label.LEARNING:
        cues = ", ".join(sorted(learning_matches)) or "learning context"
        return f"Classified as learning because it matched: {cues}."
    cues = ", ".join(sorted(entertainment_matches)) or "entertainment context"
    return f"Classified as entertainment because it matched: {cues}."


def format_cues(
    learning_matches: dict[str, int], entertainment_matches: dict[str, int]
) -> str:
    learning = ", ".join(sorted(learning_matches)) or "none"
    entertainment = ", ".join(sorted(entertainment_matches)) or "none"
    return f"learning={learning}; entertainment={entertainment}"


def classify_all(activities: Iterable[YouTubeActivity]) -> list[ClassifiedActivity]:
    return [
        ClassifiedActivity(activity=activity, classification=classify_activity(activity))
        for activity in activities
    ]


def summarize(items: Iterable[ClassifiedActivity]) -> Summary:
    learning = 0
    entertainment = 0
    unknown = 0
    for item in items:
        duration = item.activity.duration_seconds
        if item.classification.label is Label.LEARNING:
            learning += duration
        elif item.classification.label is Label.ENTERTAINMENT:
            entertainment += duration
        else:
            unknown += duration
    return Summary(
        total_seconds=learning + entertainment + unknown,
        learning_seconds=learning,
        entertainment_seconds=entertainment,
        unknown_seconds=unknown,
    )


def percentage(part: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round((part / total) * 100, 1)


def format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    minutes = round(seconds / 60)
    hours = minutes // 60
    remaining_minutes = minutes % 60
    if hours and remaining_minutes:
        return f"{hours}h {remaining_minutes}m"
    if hours:
        return f"{hours}h"
    return f"{remaining_minutes}m"


def narrative(summary: Summary) -> str:
    passive = round(summary.passive_consumption_percentage)
    learning = round(summary.learning_percentage)
    unknown = round(summary.unknown_percentage)
    base = (
        f"You spent {format_duration(summary.total_seconds)} on YouTube. "
        f"{passive}% was passive consumption and {learning}% was learning."
    )
    if unknown:
        return f"{base} {unknown}% was unknown."
    return base


def report(path: str | Path) -> dict[str, Any]:
    classified = classify_all(load_activities(path))
    summary = summarize(classified)
    return {
        "summary": {
            "total_seconds": summary.total_seconds,
            "total_duration": format_duration(summary.total_seconds),
            "learning_percentage": summary.learning_percentage,
            "passive_consumption_percentage": summary.passive_consumption_percentage,
            "unknown_percentage": summary.unknown_percentage,
            "narrative": narrative(summary),
        },
        "items": [
            {
                "title": item.activity.title,
                "url": item.activity.url,
                "channel": item.activity.channel,
                "duration_seconds": item.activity.duration_seconds,
                "watched_at": item.activity.watched_at,
                "label": item.classification.label.value,
                "confidence": item.classification.confidence,
                "reason": item.classification.reason,
            }
            for item in classified
        ],
    }
