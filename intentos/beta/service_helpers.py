"""Small helpers shared by the local beta HTTP service."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


def clear_generated_artifacts(runtime_dir: Path | None) -> list[str]:
    if runtime_dir is None:
        return []
    artifacts = runtime_dir / "artifacts"
    removed: list[str] = []
    for pattern in ["beta-*.json", "beta-*.png", "beta-*.html", "beta-*.txt"]:
        for path in sorted(artifacts.glob(pattern)):
            if not path.is_file():
                continue
            path.unlink()
            removed.append(str(path))
    return removed


def parsed_path(path: str) -> tuple[str, dict[str, list[str]]]:
    parsed = urlparse(path)
    return parsed.path, parse_qs(parsed.query)


def today() -> str:
    return datetime.now().astimezone().date().isoformat()


def require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be non-empty text")
    return value.strip()


def optional_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key, "")
    return value.strip() if isinstance(value, str) else ""


def event_to_dict(event) -> dict[str, object]:
    return {
        "source_app": event.source_app,
        "surface": event.surface,
        "title": event.title,
        "started_at": event.started_at,
        "duration_seconds": event.duration_seconds,
        "url": event.url,
        "metadata": event.metadata or {},
    }
