"""Command line interface for the IntentOS YouTube MVP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from intentos.youtube import report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify local YouTube watch activity into behavioral intent."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="data/youtube/sample_watch_history.json",
        help="Path to a local YouTube watch-history JSON file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the full machine-readable report as JSON.",
    )
    args = parser.parse_args()

    result = report(Path(args.input))
    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    summary = result["summary"]
    print(summary["narrative"])
    print()
    for item in result["items"]:
        confidence = int(round(item["confidence"] * 100))
        print(f"- {item['label']} ({confidence}%): {item['title']}")
        print(f"  {item['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
