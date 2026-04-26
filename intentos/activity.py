"""Generic activity event model for IntentOS."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ActivityEvent:
    source_app: str
    surface: str
    title: str
    started_at: str
    duration_seconds: int
    url: str | None = None
    metadata: dict[str, Any] | None = None


def load_events(path: str | Path) -> list[ActivityEvent]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("activity events must be a JSON array")
    return [parse_event(item, index) for index, item in enumerate(raw)]


def parse_event(item: Any, index: int) -> ActivityEvent:
    if not isinstance(item, dict):
        raise ValueError(f"item {index} must be an object")

    duration = item.get("duration_seconds")
    if not isinstance(duration, int) or duration <= 0:
        raise ValueError(f"item {index} duration_seconds must be a positive integer")

    metadata = item.get("metadata")
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise ValueError(f"item {index} metadata must be an object when present")

    return ActivityEvent(
        source_app=require_text(item, "source_app", index),
        surface=require_text(item, "surface", index),
        title=require_text(item, "title", index),
        started_at=require_text(item, "started_at", index),
        duration_seconds=duration,
        url=optional_text(item, "url", index),
        metadata=metadata,
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


def event_text(event: ActivityEvent) -> str:
    metadata_text = " ".join(str(value) for value in (event.metadata or {}).values())
    return " ".join(
        part
        for part in [
            event.source_app,
            event.surface,
            event.title,
            event.url or "",
            metadata_text,
        ]
        if part
    ).lower()
