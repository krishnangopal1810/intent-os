import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from intentos.capture.browser import BrowserTab
from intentos.capture.macos import MacOSAppSnapshot
from intentos.capture.session import capture_session_observations, merge_adjacent_events
from intentos.capture_cli import normalized_events_from_observation_items
from intentos.capture_replay import replay_capture
from intentos.capture.jsonl import write_events_jsonl


class CaptureSessionTest(unittest.TestCase):
    def test_capture_session_samples_repeated_snapshots(self):
        clock = FakeClock(datetime(2026, 4, 26, 10, 0, tzinfo=timezone.utc))
        snapshots = iter(
            [
                MacOSAppSnapshot("Safari", "com.apple.Safari", 10, "Search"),
                MacOSAppSnapshot("VS Code", "com.microsoft.VSCode", 11, "session.py"),
            ]
        )

        observations = capture_session_observations(
            duration_seconds=10,
            interval_seconds=5,
            snapshot_provider=lambda: next(snapshots),
            browser_provider=lambda app, bundle: (
                BrowserTab(
                    browser_name="Safari",
                    bundle_id=bundle,
                    url="https://example.com/research",
                    title="Research notes",
                    domain="example.com",
                    source="fake_browser",
                )
                if app == "Safari"
                else None
            ),
            clock=clock.now,
            sleeper=clock.sleep,
        )

        self.assertEqual(len(observations), 2)
        self.assertEqual(observations[0].window_title, "Research notes")
        self.assertEqual(observations[0].domain, "example.com")
        self.assertEqual(observations[0].metadata["capture_mode"], "manual_live_session")
        self.assertEqual(observations[1].window_title, "session.py")

    def test_merges_adjacent_equivalent_events_and_keeps_boundaries(self):
        raw = json.loads(Path("data/capture/fake_session_observations.json").read_text())
        events = normalized_events_from_observation_items(
            raw,
            Path("data/capture/privacy_policy.json"),
        )

        merged = merge_adjacent_events(events)

        self.assertEqual(len(events), 5)
        self.assertEqual(len(merged), 3)
        self.assertEqual(merged[0].source_app, "Google Chrome")
        self.assertEqual(merged[0].duration_seconds, 10)
        self.assertEqual(merged[0].metadata["sample_count"], 2)
        self.assertEqual(merged[0].metadata["merged_until"], "2026-04-26T10:00:10Z")
        self.assertEqual(merged[1].source_app, "VS Code")
        self.assertEqual(merged[1].duration_seconds, 10)
        self.assertEqual(merged[2].source_app, "Slack")

    def test_does_not_merge_equivalent_events_across_time_gaps(self):
        raw = [
            {
                "start_time": "2026-04-26T10:00:00Z",
                "end_time": "2026-04-26T10:00:05Z",
                "app_name": "VS Code",
                "bundle_id": "com.microsoft.VSCode",
                "process_id": 2002,
                "window_title": "session.py - intent-os",
                "source": "fake_session",
                "metadata": {"capture_mode": "fixture_session"},
            },
            {
                "start_time": "2026-04-26T10:00:05Z",
                "end_time": "2026-04-26T10:00:10Z",
                "app_name": "Google Chrome",
                "bundle_id": "com.google.Chrome",
                "process_id": 1001,
                "window_title": "Bank account login",
                "url": "https://bank.example/login",
                "domain": "bank.example",
                "source": "fake_session",
                "metadata": {"capture_mode": "fixture_session"},
            },
            {
                "start_time": "2026-04-26T10:00:10Z",
                "end_time": "2026-04-26T10:00:15Z",
                "app_name": "VS Code",
                "bundle_id": "com.microsoft.VSCode",
                "process_id": 2002,
                "window_title": "session.py - intent-os",
                "source": "fake_session",
                "metadata": {"capture_mode": "fixture_session"},
            },
        ]
        events = normalized_events_from_observation_items(
            raw,
            Path("data/capture/privacy_policy.json"),
        )

        merged = merge_adjacent_events(events)

        self.assertEqual(len(events), 2)
        self.assertEqual(len(merged), 2)
        self.assertNotIn("merged_until", merged[0].metadata)

    def test_session_replay_report_includes_timeline_fields(self):
        raw = json.loads(Path("data/capture/fake_session_observations.json").read_text())
        events = merge_adjacent_events(
            normalized_events_from_observation_items(
                raw,
                Path("data/capture/privacy_policy.json"),
            )
        )

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "session-events.jsonl"
            write_events_jsonl(events, output)
            report = replay_capture(output)

        self.assertEqual(len(report["items"]), 3)
        self.assertIn("started_at", report["items"][0])
        self.assertIn("metadata", report["items"][0])
        self.assertEqual(report["items"][0]["duration_seconds"], 10)


class FakeClock:
    def __init__(self, initial: datetime):
        self.current = initial

    def now(self) -> datetime:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.current += timedelta(seconds=seconds)


if __name__ == "__main__":
    unittest.main()
