"""Sessionization for repeated metadata-only capture samples."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Callable, Iterable

from intentos.activity import ActivityEvent
from intentos.capture.browser import BrowserTab, browser_tab_metadata
from intentos.capture.core import CaptureObservation, parse_timestamp
from intentos.capture.macos import (
    MacOSAppSnapshot,
    format_timestamp,
    frontmost_app_snapshot,
    utc_now,
)


SnapshotProvider = Callable[[], MacOSAppSnapshot]
BrowserProvider = Callable[[str, str | None], BrowserTab | None]
Clock = Callable[[], datetime]
Sleeper = Callable[[float], None]


def capture_session_observations(
    duration_seconds: int,
    interval_seconds: int,
    browser_provider: BrowserProvider | None = None,
    snapshot_provider: SnapshotProvider = frontmost_app_snapshot,
    clock: Clock = utc_now,
    sleeper: Sleeper = time.sleep,
) -> list[CaptureObservation]:
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")

    observations: list[CaptureObservation] = []
    remaining = duration_seconds
    start = clock()
    while remaining > 0:
        sample_seconds = min(interval_seconds, remaining)
        snapshot = snapshot_provider()
        browser = (
            browser_provider(snapshot.app_name, snapshot.bundle_id)
            if browser_provider
            else None
        )
        sleeper(sample_seconds)
        end = clock()
        if end <= start:
            end = start + timedelta(seconds=sample_seconds)
        observations.append(snapshot_to_session_observation(snapshot, browser, start, end))
        remaining -= sample_seconds
        start = end
    return observations


def snapshot_to_session_observation(
    snapshot: MacOSAppSnapshot,
    browser: BrowserTab | None,
    start: datetime,
    end: datetime,
) -> CaptureObservation:
    metadata = {
        "capture_mode": "manual_live_session",
        "adapter": "osascript_system_events",
        "permission": "Accessibility permission may be required",
    }
    window_title = snapshot.window_title
    url = None
    domain = None
    source = "macos_frontmost"
    if browser:
        metadata.update(browser_tab_metadata(browser))
        window_title = browser.title
        url = browser.url
        domain = browser.domain
        source = "macos_frontmost_with_browser"

    return CaptureObservation(
        start_time=format_timestamp(start),
        end_time=format_timestamp(end),
        app_name=snapshot.app_name,
        bundle_id=snapshot.bundle_id,
        process_id=snapshot.process_id,
        window_title=window_title,
        url=url,
        domain=domain,
        source=source,
        metadata=metadata,
    )


def merge_adjacent_events(events: Iterable[ActivityEvent]) -> list[ActivityEvent]:
    merged: list[ActivityEvent] = []
    for event in events:
        event = with_sample_count(event, 1)
        if merged and equivalent_event(merged[-1], event) and time_contiguous(
            merged[-1], event
        ):
            merged[-1] = merge_pair(merged[-1], event)
        else:
            merged.append(event)
    return merged


def equivalent_event(left: ActivityEvent, right: ActivityEvent) -> bool:
    return (
        left.source_app == right.source_app
        and left.surface == right.surface
        and left.title == right.title
        and left.url == right.url
        and comparable_metadata(left) == comparable_metadata(right)
    )


def comparable_metadata(event: ActivityEvent) -> tuple[object, ...]:
    metadata = event.metadata or {}
    return tuple(
        metadata.get(key)
        for key in (
            "bundle_id",
            "domain",
            "source",
            "capture_mode",
            "browser_name",
        )
    )


def time_contiguous(left: ActivityEvent, right: ActivityEvent) -> bool:
    return event_end(left) == parse_timestamp(right.started_at, "event started_at")


def event_end(event: ActivityEvent) -> datetime:
    return parse_timestamp(event.started_at, "event started_at") + timedelta(
        seconds=event.duration_seconds
    )


def merge_pair(left: ActivityEvent, right: ActivityEvent) -> ActivityEvent:
    duration = left.duration_seconds + right.duration_seconds
    metadata = dict(left.metadata or {})
    metadata["sample_count"] = int(metadata.get("sample_count", 1)) + int(
        (right.metadata or {}).get("sample_count", 1)
    )
    metadata["merged_until"] = format_timestamp(event_end(right))
    metadata["merged"] = True
    return ActivityEvent(
        source_app=left.source_app,
        surface=left.surface,
        title=left.title,
        started_at=left.started_at,
        duration_seconds=duration,
        url=left.url,
        metadata=metadata,
    )


def with_sample_count(event: ActivityEvent, sample_count: int) -> ActivityEvent:
    metadata = dict(event.metadata or {})
    metadata.setdefault("sample_count", sample_count)
    return ActivityEvent(
        source_app=event.source_app,
        surface=event.surface,
        title=event.title,
        started_at=event.started_at,
        duration_seconds=event.duration_seconds,
        url=event.url,
        metadata=metadata,
    )
