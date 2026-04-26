"""Continuous metadata-only live capture loop."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from intentos.capture.browser import (
    BrowserCaptureError,
    active_browser_tab,
    browser_tab_metadata,
)
from intentos.capture.core import CaptureObservation, observation_to_event
from intentos.capture.jsonl import append_events_jsonl, write_events_jsonl
from intentos.capture.macos import (
    MacOSCaptureError,
    frontmost_app_snapshot,
    snapshot_to_observation,
    utc_now,
)
from intentos.capture.privacy import load_privacy_policy, redact_metadata, should_exclude
from intentos.capture_replay import replay_capture


@dataclass(frozen=True)
class LiveCaptureConfig:
    output_path: Path
    privacy_policy_path: Path
    interval_seconds: int = 5
    summary_json_path: Path | None = None
    summary_text_path: Path | None = None
    status_json_path: Path | None = None
    max_samples: int | None = None


Sleeper = Callable[[int], None]


def run_live_capture(
    config: LiveCaptureConfig,
    sleeper: Sleeper = time.sleep,
) -> dict[str, int]:
    if config.interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")
    if config.max_samples is not None and config.max_samples <= 0:
        raise ValueError("max_samples must be positive when present")

    samples = 0
    events_written = 0
    write_events_jsonl([], config.output_path)
    write_status(config, "running", samples, events_written)
    refresh_summary(config)

    try:
        while config.max_samples is None or samples < config.max_samples:
            try:
                events = capture_live_event(config, sleeper)
            except MacOSCaptureError:
                write_status(config, "error", samples, events_written)
                raise

            samples += 1
            events_written += append_events_jsonl(events, config.output_path)
            refresh_summary(config)
            write_status(config, "running", samples, events_written)
            print(
                "capture-live: "
                f"sample={samples} events={len(events)} total_events={events_written}",
                flush=True,
            )
    except KeyboardInterrupt:
        write_status(config, "stopped", samples, events_written)
        return {"samples": samples, "events": events_written}

    write_status(config, "completed", samples, events_written)
    return {"samples": samples, "events": events_written}


def capture_live_event(
    config: LiveCaptureConfig,
    sleeper: Sleeper = time.sleep,
) -> list[object]:
    start = utc_now()
    snapshot = frontmost_app_snapshot()
    browser = None
    try:
        browser = active_browser_tab(snapshot.app_name, snapshot.bundle_id)
    except BrowserCaptureError as exc:
        print(f"capture-live: browser metadata unavailable: {exc}", flush=True)

    sleeper(config.interval_seconds)
    observation = snapshot_to_observation(snapshot, start, utc_now())
    return normalize_live_observation(observation, browser, config.privacy_policy_path)


def normalize_live_observation(
    observation: CaptureObservation,
    browser,
    privacy_policy_path: Path,
) -> list[object]:
    event = observation_to_event(observation)
    policy = load_privacy_policy(privacy_policy_path)
    metadata = {
        "app_name": event.source_app,
        "bundle_id": event.metadata.get("bundle_id") if event.metadata else None,
        "window_title": event.title,
        "title": event.title,
        "url": event.url,
        "domain": event.metadata.get("domain") if event.metadata else None,
        "visible_text_excerpt": (event.metadata or {}).get("visible_text_excerpt"),
    }

    if browser:
        browser_metadata = browser_tab_metadata(browser)
        metadata.update(browser_metadata)
        metadata["url"] = browser.url
        metadata["title"] = browser.title
        metadata["window_title"] = browser.title
        event = event.__class__(
            source_app=event.source_app,
            surface=browser.domain,
            title=browser.title,
            started_at=event.started_at,
            duration_seconds=event.duration_seconds,
            url=browser.url,
            metadata={**(event.metadata or {}), **browser_metadata},
        )

    if should_exclude(metadata, policy):
        return []

    return [
        event.__class__(
            source_app=event.source_app,
            surface=event.surface,
            title=event.title,
            started_at=event.started_at,
            duration_seconds=event.duration_seconds,
            url=event.url,
            metadata=redact_metadata(event.metadata or {}, policy),
        )
    ]


def refresh_summary(config: LiveCaptureConfig) -> None:
    result = replay_capture(config.output_path, allow_empty=True)
    if config.summary_json_path:
        write_json(config.summary_json_path, result)
    if config.summary_text_path:
        config.summary_text_path.parent.mkdir(parents=True, exist_ok=True)
        config.summary_text_path.write_text(format_report(result), encoding="utf-8")


def write_status(
    config: LiveCaptureConfig,
    state: str,
    samples: int,
    events: int,
) -> None:
    if not config.status_json_path:
        return
    write_json(
        config.status_json_path,
        {
            "capture_mode": "background_live_sensor",
            "state": state,
            "interval_seconds": config.interval_seconds,
            "samples": samples,
            "events": events,
            "output_path": str(config.output_path),
            "summary_json_path": (
                str(config.summary_json_path) if config.summary_json_path else None
            ),
            "updated_at": utc_now().isoformat().replace("+00:00", "Z"),
        },
    )


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def format_report(result: dict[str, object]) -> str:
    summary = result["summary"]
    lines = [summary["narrative"], ""]
    for label, data in summary["labels"].items():
        lines.append(f"- {label}: {data['duration']} ({data['percentage']}%)")
    return "\n".join(lines).strip() + "\n"
