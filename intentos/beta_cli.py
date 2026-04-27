"""Command line wiring for the dogfood beta runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import sleep
from urllib.request import Request, urlopen

from intentos.beta import recorder, review, store
from intentos.beta.extension import chrome_event_to_activity
from intentos.beta.service import ServiceConfig, serve
from intentos.capture.privacy import load_privacy_policy


def main() -> int:
    parser = argparse.ArgumentParser(description="Run and inspect the IntentOS beta service.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve", help="Start the local beta HTTP service.")
    add_common(serve_parser)
    serve_parser.add_argument("--port", type=int, required=True)
    serve_parser.add_argument("--service-log")

    seed = subparsers.add_parser("seed-fixtures", help="Persist fake Chrome bridge events.")
    add_common(seed)
    seed.add_argument("--input", default="data/beta/fake_chrome_events.json")

    bridge = subparsers.add_parser("fake-bridge", help="Post fake Chrome events to the service.")
    bridge.add_argument("--service-url", required=True)
    bridge.add_argument("--input", default="data/beta/fake_chrome_events.json")
    bridge.add_argument("--interval-seconds", type=int, default=60)
    bridge.add_argument("--once", action="store_true")

    status = subparsers.add_parser("status", help="Print beta runtime status.")
    status.add_argument("--db", required=True)
    status.add_argument("--json", action="store_true")

    review_parser = subparsers.add_parser("daily-review", help="Write a daily review JSON artifact.")
    review_parser.add_argument("--db", required=True)
    review_parser.add_argument("--date", required=True)
    review_parser.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.command == "serve":
        serve(
            ServiceConfig(
                db_path=Path(args.db),
                privacy_policy_path=Path(args.privacy_policy),
                port=args.port,
                retention_days=args.retention_days,
                service_log=Path(args.service_log) if args.service_log else None,
            )
        )
        return 0
    if args.command == "seed-fixtures":
        count = seed_fixtures(Path(args.db), Path(args.input), Path(args.privacy_policy), args.retention_days)
        print(f"beta-cli: seeded {count} fixture event(s)")
        return 0
    if args.command == "fake-bridge":
        return run_fake_bridge(
            args.service_url,
            Path(args.input),
            args.interval_seconds,
            once=args.once,
        )
    if args.command == "status":
        with store.connect(args.db) as conn:
            store.init_db(conn)
            payload = store.status(conn, args.db)
        print(json.dumps(payload, indent=2) if args.json else format_status(payload))
        return 0
    if args.command == "daily-review":
        with store.connect(args.db) as conn:
            store.init_db(conn)
            payload = review.daily_review(conn, args.date, args.db)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"beta-cli: wrote {args.output}")
        return 0
    raise AssertionError(args.command)


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db", required=True)
    parser.add_argument("--privacy-policy", default="data/capture/privacy_policy.json")
    parser.add_argument("--retention-days", type=int, default=store.DEFAULT_RETENTION_DAYS)


def seed_fixtures(
    db_path: Path, input_path: Path, privacy_policy_path: Path, retention_days: int
) -> int:
    raw = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("fake Chrome events must be a JSON array")
    policy = load_privacy_policy(privacy_policy_path)
    count = 0
    with store.connect(db_path) as conn:
        store.init_db(conn, retention_days)
        store.cleanup_old_events(conn)
        for index, item in enumerate(raw):
            event = chrome_event_to_activity(item, policy, index)
            if event is not None and recorder.record_event(conn, event):
                count += 1
                store.set_status(conn, "last_browser_event_at", event.started_at)
        store.set_status(conn, "extension_state", "fixture_bridge")
    return count


def run_fake_bridge(
    service_url: str, input_path: Path, interval_seconds: int, once: bool = False
) -> int:
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")
    raw = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("fake Chrome events must be a JSON array")
    while True:
        accepted = 0
        for item in raw:
            data = json.dumps(item).encode("utf-8")
            request = Request(
                service_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=3) as response:
                if 200 <= response.status < 300:
                    accepted += 1
        print(f"beta-cli: fake bridge posted {accepted} event(s)", flush=True)
        if once:
            return 0
        sleep(interval_seconds)


def format_status(payload: dict[str, object]) -> str:
    rows = [
        "beta-status:",
        f"service={payload['service']['state']}",
        f"db={payload['database']['path']}",
        f"retention_days={payload['database']['retention_days']}",
        f"capture={payload['capture']['state']}",
        f"paused={payload['pause']['paused']}",
        f"extension={payload['extension']['state']}",
        f"last_event_time={payload.get('last_event_time')}",
        f"row_counts={payload['row_counts']}",
        f"logs={payload['logs']}",
    ]
    return "\n".join(rows)


if __name__ == "__main__":
    raise SystemExit(main())
