"""Replay captured ActivityEvent JSONL through the classifier."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from intentos.capture.jsonl import read_events_jsonl
from intentos.reporting import activity_report


def replay_capture(path: str | Path) -> dict[str, Any]:
    return activity_report(read_events_jsonl(path))
