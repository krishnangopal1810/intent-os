#!/usr/bin/env python3
"""Manifest for checked-in UI screenshot evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILES = [
    "web/index.html",
    "web/styles.css",
    "web/app.js",
    "scripts/product/dev.sh",
    "data/activity/multi_app_events.json",
    "data/capture/fake_browser_tabs.json",
    "data/capture/fake_macos_observations.json",
    "data/capture/privacy_policy.json",
    "data/youtube/sample_watch_history.json",
    "intentos/activity.py",
    "intentos/activity_cli.py",
    "intentos/capture_cli.py",
    "intentos/capture/browser.py",
    "intentos/capture/core.py",
    "intentos/capture/jsonl.py",
    "intentos/capture/privacy.py",
    "intentos/capture_replay.py",
    "intentos/classifier.py",
    "intentos/cli.py",
    "intentos/reporting.py",
    "intentos/youtube.py",
]


def manifest() -> dict[str, object]:
    digest = hashlib.sha256()
    for relative_path in SOURCE_FILES:
        path = ROOT / relative_path
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return {
        "version": 1,
        "source_files": SOURCE_FILES,
        "source_hash": digest.hexdigest(),
    }


def main() -> int:
    print(json.dumps(manifest(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
