"""CLI for generic multi-app ActivityEvent reporting."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from intentos.activity import load_events
from intentos.reporting import activity_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify local multi-app activity events into behavior labels."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="data/activity/multi_app_events.json",
        help="Path to a local ActivityEvent JSON file.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    result = activity_report(load_events(Path(args.input)))
    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(result["summary"]["narrative"])
    print()
    for label, data in result["summary"]["labels"].items():
        print(f"- {label}: {data['duration']} ({data['percentage']}%)")
    print()
    for item in result["items"]:
        confidence = int(round(item["confidence"] * 100))
        print(f"- {item['label']} ({confidence}%): {item['source_app']} - {item['title']}")
        print(f"  {item['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
