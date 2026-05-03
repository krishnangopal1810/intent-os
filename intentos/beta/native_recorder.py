"""Native macOS metadata recorder for the dogfood beta."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from intentos.activity import ActivityEvent
from intentos.beta import recorder, store
from intentos.capture.live import LiveCaptureConfig, capture_live_event
from intentos.capture.macos import MacOSCaptureError


@dataclass(frozen=True)
class NativeRecorderConfig:
    db_path: Path
    privacy_policy_path: Path
    interval_seconds: int = 5
    max_samples: int | None = None
    recorder_log: Path | None = None


CaptureOnce = Callable[[LiveCaptureConfig, Callable[[int], None]], list[ActivityEvent]]
IdleSeconds = Callable[[], int | None]
Sleeper = Callable[[int], None]


def run_native_recorder(
    config: NativeRecorderConfig,
    sleeper: Sleeper = time.sleep,
    capture_once: CaptureOnce = capture_live_event,
    idle_seconds: IdleSeconds | None = None,
) -> dict[str, int]:
    if config.interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")
    if config.max_samples is not None and config.max_samples <= 0:
        raise ValueError("max_samples must be positive when present")
    idle_seconds = idle_seconds or current_idle_seconds

    samples = 0
    events_written = 0
    live_config = LiveCaptureConfig(
        output_path=Path(os.devnull),
        privacy_policy_path=config.privacy_policy_path,
        interval_seconds=config.interval_seconds,
        max_samples=config.max_samples,
    )
    with store.connect(config.db_path) as conn:
        store.init_db(conn)
        mark_running(conn, config)

    try:
        while config.max_samples is None or samples < config.max_samples:
            with store.connect(config.db_path) as conn:
                store.init_db(conn)
                if is_paused(conn):
                    samples += 1
                    mark_paused(conn, samples, events_written)
                    print(
                        "beta-native-recorder: "
                        f"sample={samples} paused=true written={events_written}",
                        flush=True,
                    )
                    sleeper(config.interval_seconds)
                    continue

            idle = idle_seconds()
            if idle is not None and idle >= recorder.IDLE_THRESHOLD_SECONDS:
                samples += 1
                with store.connect(config.db_path) as conn:
                    store.init_db(conn)
                    mark_away(conn, idle, samples, events_written)
                print(
                    "beta-native-recorder: "
                    f"sample={samples} idle_seconds={idle} written={events_written}",
                    flush=True,
                )
                sleeper(config.interval_seconds)
                continue

            try:
                events = capture_once(live_config, sleeper)
            except MacOSCaptureError as exc:
                with store.connect(config.db_path) as conn:
                    store.init_db(conn)
                    mark_error(conn, str(exc))
                raise

            samples += 1
            with store.connect(config.db_path) as conn:
                store.init_db(conn)
                written = persist_events(conn, events)
                events_written += written
                store.set_status(conn, "native_recorder_state", "running")
                store.set_status(conn, "native_recorder_samples", str(samples))
                store.set_status(conn, "native_recorder_events", str(events_written))
            print(
                "beta-native-recorder: "
                f"sample={samples} events={len(events)} written={events_written}",
                flush=True,
            )
    except KeyboardInterrupt:
        with store.connect(config.db_path) as conn:
            store.init_db(conn)
            store.set_status(conn, "native_recorder_state", "stopped")
        return {"samples": samples, "events": events_written}

    with store.connect(config.db_path) as conn:
        store.init_db(conn)
        store.set_status(conn, "native_recorder_state", "completed")
    return {"samples": samples, "events": events_written}


def persist_events(conn: sqlite3.Connection, events: list[ActivityEvent]) -> int:
    written = 0
    for event in events:
        row_id = recorder.record_event(conn, mark_native(event))
        if row_id:
            written += 1
            store.set_status(conn, "native_recorder_last_event_at", event.started_at)
    return written


def current_idle_seconds() -> int | None:
    try:
        completed = subprocess.run(
            ["ioreg", "-c", "IOHIDSystem"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return parse_hid_idle_seconds(completed.stdout)


def parse_hid_idle_seconds(output: str) -> int | None:
    for line in output.splitlines():
        if "HIDIdleTime" not in line:
            continue
        try:
            nanoseconds = int(line.rsplit("=", 1)[1].strip())
        except (IndexError, ValueError):
            return None
        return nanoseconds // 1_000_000_000
    return None


def mark_native(event: ActivityEvent) -> ActivityEvent:
    metadata = dict(event.metadata or {})
    metadata["source_adapter"] = "native_macos_recorder"
    metadata["source"] = metadata.get("source") or "native_macos_recorder"
    return ActivityEvent(
        source_app=event.source_app,
        surface=event.surface,
        title=event.title,
        started_at=event.started_at,
        duration_seconds=event.duration_seconds,
        url=event.url,
        metadata=metadata,
    )


def mark_running(conn: sqlite3.Connection, config: NativeRecorderConfig) -> None:
    store.set_status(conn, "native_recorder_state", "running")
    store.set_status(conn, "native_recorder_pid", str(os.getpid()))
    store.set_status(conn, "native_recorder_last_error", "")
    store.set_status(conn, "native_recorder_interval_seconds", str(config.interval_seconds))
    if config.recorder_log:
        store.set_status(conn, "native_recorder_log", str(config.recorder_log))


def mark_error(conn: sqlite3.Connection, detail: str) -> None:
    store.set_status(conn, "native_recorder_state", "error")
    store.set_status(conn, "native_recorder_last_error", " ".join(detail.split()))


def is_paused(conn: sqlite3.Connection) -> bool:
    return store.is_paused(store.setting(conn, "paused_until", ""))


def mark_paused(conn: sqlite3.Connection, samples: int, events_written: int) -> None:
    store.set_status(conn, "capture_state", "paused")
    store.set_status(conn, "capture_note", "capture paused by user")
    store.set_status(conn, "native_recorder_state", "running")
    store.set_status(conn, "native_recorder_samples", str(samples))
    store.set_status(conn, "native_recorder_events", str(events_written))


def mark_away(conn: sqlite3.Connection, idle_seconds: int, samples: int, events_written: int) -> None:
    store.set_status(conn, "capture_state", "away")
    store.set_status(
        conn,
        "capture_note",
        f"ignored idle sample after {idle_seconds}s idle",
    )
    store.set_status(conn, "native_recorder_state", "running")
    store.set_status(conn, "native_recorder_samples", str(samples))
    store.set_status(conn, "native_recorder_events", str(events_written))
