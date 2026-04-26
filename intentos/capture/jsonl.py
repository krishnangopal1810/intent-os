"""JSONL persistence for captured ActivityEvent records."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from intentos.activity import ActivityEvent, parse_event


def event_to_dict(event: ActivityEvent) -> dict[str, object]:
    return asdict(event)


def write_events_jsonl(events: Iterable[ActivityEvent], path: str | Path) -> int:
    return write_events_jsonl_with_mode(events, path, "w")


def append_events_jsonl(events: Iterable[ActivityEvent], path: str | Path) -> int:
    return write_events_jsonl_with_mode(events, path, "a")


def write_events_jsonl_with_mode(
    events: Iterable[ActivityEvent], path: str | Path, mode: str
) -> int:
    count = 0
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open(mode, encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event_to_dict(event), sort_keys=True))
            handle.write("\n")
            count += 1
    return count


def read_events_jsonl(path: str | Path, allow_empty: bool = False) -> list[ActivityEvent]:
    input_path = Path(path)
    events: list[ActivityEvent] = []
    for index, line in enumerate(input_path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {index + 1} is invalid JSON") from exc
        events.append(parse_event(item, index))
    if not events and not allow_empty:
        raise ValueError("capture JSONL must contain at least one ActivityEvent")
    return events
