"""CLI wiring for continuous live capture."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path

from intentos.capture.live import LiveCaptureConfig, run_live_capture
from intentos.capture.macos import MacOSCaptureError


def add_capture_live_parser(subparsers) -> ArgumentParser:
    capture_live = subparsers.add_parser(
        "capture-live",
        help="Continuously capture frontmost macOS app/window and browser metadata.",
    )
    capture_live.add_argument("--output", required=True, help="Output JSONL path.")
    capture_live.add_argument(
        "--interval-seconds",
        type=int,
        default=5,
        help="Seconds represented by each live sample.",
    )
    capture_live.add_argument(
        "--summary-json",
        help="Optional replay summary JSON refreshed after each sample.",
    )
    capture_live.add_argument(
        "--summary-text",
        help="Optional replay summary text refreshed after each sample.",
    )
    capture_live.add_argument(
        "--status-json",
        help="Optional capture status JSON refreshed after each sample.",
    )
    capture_live.add_argument(
        "--max-samples",
        type=int,
        help="Optional deterministic stop after N samples.",
    )
    capture_live.add_argument(
        "--privacy-policy",
        default="data/capture/privacy_policy.json",
        help="Local privacy policy JSON.",
    )
    return capture_live


def run_capture_live_command(args: Namespace) -> int:
    config = LiveCaptureConfig(
        output_path=Path(args.output),
        privacy_policy_path=Path(args.privacy_policy),
        interval_seconds=args.interval_seconds,
        summary_json_path=Path(args.summary_json) if args.summary_json else None,
        summary_text_path=Path(args.summary_text) if args.summary_text else None,
        status_json_path=Path(args.status_json) if args.status_json else None,
        max_samples=args.max_samples,
    )
    try:
        result = run_live_capture(config)
    except MacOSCaptureError as exc:
        raise SystemExit(str(exc)) from exc
    print(
        "capture-cli: live capture stopped after "
        f"{result['samples']} sample(s), {result['events']} event row(s)"
    )
    return 0
