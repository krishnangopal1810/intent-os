"""CLI for metadata-only capture normalization and replay."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from intentos.capture.browser import (
    BrowserCaptureError,
    active_browser_tab,
    browser_tab_metadata,
    parse_browser_tab,
)
from intentos.capture.core import CaptureObservation, parse_observation, observation_to_event
from intentos.capture.jsonl import write_events_jsonl
from intentos.capture.macos import (
    MacOSCaptureError,
    frontmost_app_snapshot,
    snapshot_to_observation,
    utc_now,
)
from intentos.capture.privacy import (
    load_privacy_policy,
    redact_metadata,
    should_exclude,
)
from intentos.capture.session import capture_session_observations, merge_adjacent_events
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
    normalize.add_argument(
        "--merge-adjacent",
        action="store_true",
        help="Merge adjacent equivalent rows after privacy filtering.",
    )

    capture_macos = subparsers.add_parser(
        "capture-macos",
        help="Capture one metadata-only frontmost macOS app/window sample.",
    )
    capture_macos.add_argument("--output", required=True, help="Output JSONL path.")
    capture_macos.add_argument(
        "--duration-seconds",
        type=int,
        default=5,
        help="Sample duration for the current frontmost app/window.",
    )
    capture_macos.add_argument(
        "--privacy-policy",
        default="data/capture/privacy_policy.json",
        help="Local privacy policy JSON.",
    )

    capture_session = subparsers.add_parser(
        "capture-session",
        help="Capture a short metadata-only macOS app/window/browser session.",
    )
    capture_session.add_argument("--output", required=True, help="Output JSONL path.")
    capture_session.add_argument(
        "--duration-seconds",
        type=int,
        default=30,
        help="Total bounded session duration.",
    )
    capture_session.add_argument(
        "--interval-seconds",
        type=int,
        default=5,
        help="Seconds between repeated metadata samples.",
    )
    capture_session.add_argument(
        "--privacy-policy",
        default="data/capture/privacy_policy.json",
        help="Local privacy policy JSON.",
    )

    replay = subparsers.add_parser(
        "replay", help="Replay ActivityEvent JSONL through the behavior report."
    )
    replay.add_argument("input", help="Path to ActivityEvent JSONL.")
    replay.add_argument("--json", action="store_true", help="Emit JSON output.")
    replay.add_argument(
        "--allow-empty",
        action="store_true",
        help="Return an empty report instead of failing when all capture rows were excluded.",
    )

    args = parser.parse_args()
    if args.command == "normalize-observations":
        count = normalize_observations(
            Path(args.input),
            Path(args.output),
            Path(args.privacy_policy),
            Path(args.browser_tabs) if args.browser_tabs else None,
            merge_adjacent=args.merge_adjacent,
        )
        print(f"capture-cli: wrote {count} ActivityEvent row(s) to {args.output}")
        return 0

    if args.command == "capture-macos":
        try:
            observation, browser_by_app = capture_live_observation_and_browser(
                args.duration_seconds
            )
        except MacOSCaptureError as exc:
            raise SystemExit(str(exc)) from exc
        count = normalize_observation_items(
            [observation],
            Path(args.output),
            Path(args.privacy_policy),
            browser_by_app,
        )
        print(f"capture-cli: wrote {count} ActivityEvent row(s) to {args.output}")
        return 0

    if args.command == "capture-session":
        try:
            observations = capture_session_observations(
                duration_seconds=args.duration_seconds,
                interval_seconds=args.interval_seconds,
                browser_provider=active_tab_or_none,
            )
        except MacOSCaptureError as exc:
            raise SystemExit(str(exc)) from exc
        events = normalized_events_from_observation_items(
            observations,
            Path(args.privacy_policy),
        )
        merged_events = merge_adjacent_events(events)
        count = write_events_jsonl(merged_events, Path(args.output))
        excluded_count = len(observations) - len(events)
        merged_count = len(events) - len(merged_events)
        print(
            "capture-cli: session "
            f"samples={len(observations)} excluded={excluded_count} "
            f"merged={merged_count} wrote={count} ActivityEvent row(s) "
            f"to {args.output}"
        )
        return 0

    result = replay_capture(Path(args.input), allow_empty=args.allow_empty)
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
    merge_adjacent: bool = False,
) -> int:
    browser_by_app = load_browser_tabs(browser_tabs_path)
    raw = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("capture observations must be a JSON array")
    return normalize_observation_items(
        raw,
        output_path,
        privacy_policy_path,
        browser_by_app,
        merge_adjacent=merge_adjacent,
    )


def normalize_observation_items(
    raw: list[object],
    output_path: Path,
    privacy_policy_path: Path,
    browser_by_app: dict[str, object] | None = None,
    merge_adjacent: bool = False,
) -> int:
    events = normalized_events_from_observation_items(
        raw,
        privacy_policy_path,
        browser_by_app,
    )
    if merge_adjacent:
        events = merge_adjacent_events(events)
    return write_events_jsonl(events, output_path)


def normalized_events_from_observation_items(
    raw: list[object],
    privacy_policy_path: Path,
    browser_by_app: dict[str, object] | None = None,
):
    policy = load_privacy_policy(privacy_policy_path)
    browser_by_app = browser_by_app or {}
    events = []
    for index, item in enumerate(raw):
        observation = (
            item if isinstance(item, CaptureObservation) else parse_observation(item, index)
        )
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
    return events


def capture_live_observation_and_browser(duration_seconds: int):
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")

    start = utc_now()
    snapshot = frontmost_app_snapshot()
    browser_by_app = browser_snapshot_for_app(snapshot.app_name, snapshot.bundle_id)
    time.sleep(duration_seconds)
    observation = snapshot_to_observation(snapshot, start, utc_now())
    return observation, browser_by_app


def browser_snapshot_for_app(app_name: str, bundle_id: str | None) -> dict[str, object]:
    try:
        browser = active_browser_tab(app_name, bundle_id)
    except BrowserCaptureError as exc:
        print(f"capture-cli: browser metadata unavailable: {exc}")
        return {}
    if not browser:
        return {}
    return {app_name.lower(): browser}


def active_tab_or_none(app_name: str, bundle_id: str | None):
    try:
        return active_browser_tab(app_name, bundle_id)
    except BrowserCaptureError as exc:
        print(f"capture-cli: browser metadata unavailable: {exc}")
        return None


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
