#!/usr/bin/env python3
"""Append structured local runtime events for Codex inspection."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: runtime-log.py component event [key=value ...]", file=sys.stderr)
        return 2

    runtime_dir = Path(os.environ.get("INTENTOS_RUNTIME_DIR", ".harness/runtime"))
    log_path = runtime_dir / "logs" / "events.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, object] = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "component": sys.argv[1],
        "event": sys.argv[2],
    }
    for token in sys.argv[3:]:
        if "=" not in token:
            print(f"runtime-log: expected key=value, got {token!r}", file=sys.stderr)
            return 2
        key, value = token.split("=", 1)
        payload[key] = coerce(value)

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return 0


def coerce(value: str) -> object:
    if value in {"true", "false"}:
        return value == "true"
    if value.isdigit():
        return int(value)
    return value


if __name__ == "__main__":
    raise SystemExit(main())
