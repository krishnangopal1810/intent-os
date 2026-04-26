"""Core metadata-only capture normalization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from intentos.activity import ActivityEvent


@dataclass(frozen=True)
class CaptureObservation:
    start_time: str
    end_time: str
    app_name: str
    bundle_id: str | None = None
    process_id: int | None = None
    window_title: str | None = None
    url: str | None = None
    domain: str | None = None
    visible_text_excerpt: str | None = None
    source: str = "fake_macos"
    metadata: dict[str, Any] | None = None


def parse_observation(item: dict[str, Any], index: int = 0) -> CaptureObservation:
    if not isinstance(item, dict):
        raise ValueError(f"observation {index} must be an object")

    metadata = item.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError(f"observation {index} metadata must be an object")

    process_id = item.get("process_id")
    if process_id is not None and not isinstance(process_id, int):
        raise ValueError(f"observation {index} process_id must be an integer")

    observation = CaptureObservation(
        start_time=require_text(item, "start_time", index),
        end_time=require_text(item, "end_time", index),
        app_name=require_text(item, "app_name", index),
        bundle_id=optional_text(item, "bundle_id", index),
        process_id=process_id,
        window_title=optional_text(item, "window_title", index),
        url=optional_text(item, "url", index),
        domain=optional_text(item, "domain", index),
        visible_text_excerpt=optional_text(item, "visible_text_excerpt", index),
        source=optional_text(item, "source", index) or "fake_macos",
        metadata=metadata,
    )
    duration_seconds(observation, index)
    return observation


def observation_to_event(observation: CaptureObservation) -> ActivityEvent:
    duration = duration_seconds(observation)
    title = observation.window_title or observation.app_name
    surface = observation.domain or observation.source
    metadata = {
        "bundle_id": observation.bundle_id,
        "process_id": observation.process_id,
        "source": observation.source,
        "domain": observation.domain,
        "visible_text_excerpt": observation.visible_text_excerpt,
    }
    metadata.update(observation.metadata or {})
    return ActivityEvent(
        source_app=observation.app_name,
        surface=surface,
        title=title,
        started_at=observation.start_time,
        duration_seconds=duration,
        url=observation.url,
        metadata={key: value for key, value in metadata.items() if value is not None},
    )


def duration_seconds(observation: CaptureObservation, index: int = 0) -> int:
    start = parse_timestamp(observation.start_time, f"observation {index} start_time")
    end = parse_timestamp(observation.end_time, f"observation {index} end_time")
    duration = int((end - start).total_seconds())
    if duration <= 0:
        raise ValueError(f"observation {index} duration must be positive")
    return duration


def parse_timestamp(value: str, label: str) -> datetime:
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def require_text(item: dict[str, Any], key: str, index: int) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"observation {index} {key} must be non-empty text")
    return value.strip()


def optional_text(item: dict[str, Any], key: str, index: int) -> str | None:
    value = item.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"observation {index} {key} must be text when present")
    value = value.strip()
    return value or None
