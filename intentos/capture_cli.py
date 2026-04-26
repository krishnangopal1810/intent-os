"""CLI for metadata-only capture normalization and replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from intentos.capture.browser import browser_tab_metadata, parse_browser_tab
from intentos.capture.core import parse_observation, observation_to_event
from intentos.capture.jsonl import write_events_jsonl
from intentos.capture.privacy import (
    load_privacy_policy,
    redact_metadata,
    should_exclude,
)
from intentos.capture_replay import replay_capture


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize metadata-only capture fixtures and replay reports."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    normalize = subparsers.add_parser(
        "normalize-observations",
        help="Normalize fake macOS observations into ActivityEvent JSONL.",
    )
    normalize.add_argument("input", help="Path to fake macOS observations JSON.")
    normalize.add_argument("--output", required=True, help="Output JSONL path.")
    normalize.add_argument(
        "--browser-tabs",
        help="Optional fake browser tab metadata JSON used for URL/title enrichment.",
    )
    normalize.add_argument(
        "--privacy-policy",
        default="data/capture/privacy_policy.json",
        help="Local privacy policy JSON.",
    )

    replay = subparsers.add_parser(
        "replay", help="Replay ActivityEvent JSONL through the behavior report."
    )
    replay.add_argument("input", help="Path to ActivityEvent JSONL.")
    replay.add_argument("--json", action="store_true", help="Emit JSON output.")

    args = parser.parse_args()
    if args.command == "normalize-observations":
        count = normalize_observations(
            Path(args.input),
            Path(args.output),
            Path(args.privacy_policy),
            Path(args.browser_tabs) if args.browser_tabs else None,
        )
        print(f"capture-cli: wrote {count} ActivityEvent row(s) to {args.output}")
        return 0

    result = replay_capture(Path(args.input))
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print_activity_report(result)
    return 0


def normalize_observations(
    input_path: Path,
    output_path: Path,
    privacy_policy_path: Path,
    browser_tabs_path: Path | None = None,
) -> int:
    policy = load_privacy_policy(privacy_policy_path)
    browser_by_app = load_browser_tabs(browser_tabs_path)
    raw = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("capture observations must be a JSON array")

    events = []
    for index, item in enumerate(raw):
        observation = parse_observation(item, index)
        event = observation_to_event(observation)
        metadata = {
            "app_name": event.source_app,
            "bundle_id": event.metadata.get("bundle_id") if event.metadata else None,
            "window_title": event.title,
            "title": event.title,
            "url": event.url,
            "domain": event.metadata.get("domain") if event.metadata else None,
            "visible_text_excerpt": (event.metadata or {}).get("visible_text_excerpt"),
        }
        browser = browser_by_app.get(event.source_app.lower())
        if browser:
            metadata.update(browser_tab_metadata(browser))
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
                metadata={**(event.metadata or {}), **browser_tab_metadata(browser)},
            )
        if should_exclude(metadata, policy):
            continue
        redacted = redact_metadata(event.metadata or {}, policy)
        events.append(
            event.__class__(
                source_app=event.source_app,
                surface=event.surface,
                title=event.title,
                started_at=event.started_at,
                duration_seconds=event.duration_seconds,
                url=event.url,
                metadata=redacted,
            )
        )
    return write_events_jsonl(events, output_path)


def load_browser_tabs(path: Path | None):
    if path is None:
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("browser tabs must be a JSON array")
    tabs = [parse_browser_tab(item, index) for index, item in enumerate(raw)]
    return {tab.browser_name.lower(): tab for tab in tabs}


def print_activity_report(result: dict[str, object]) -> None:
    summary = result["summary"]
    print(summary["narrative"])
    print()
    for label, data in summary["labels"].items():
        print(f"- {label}: {data['duration']} ({data['percentage']}%)")
    print()
    for item in result["items"]:
        confidence = int(round(item["confidence"] * 100))
        print(f"- {item['label']} ({confidence}%): {item['source_app']} - {item['title']}")
        print(f"  {item['reason']}")


if __name__ == "__main__":
    raise SystemExit(main())
