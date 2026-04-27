import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import intentos.capture.live as live
from intentos.capture.browser import BrowserTab
from intentos.capture.jsonl import read_events_jsonl
from intentos.capture.live import LiveCaptureConfig
from intentos.capture.macos import MacOSAppSnapshot, MacOSCaptureError


class CaptureLiveTest(unittest.TestCase):
    def test_live_capture_appends_events_and_refreshes_summary(self):
        original_frontmost = live.frontmost_app_snapshot
        original_active_tab = live.active_browser_tab
        original_utc_now = live.utc_now
        now = datetime(2026, 4, 26, 10, 0, tzinfo=timezone.utc)
        calls = []

        def fake_frontmost():
            calls.append("frontmost")
            return MacOSAppSnapshot(
                app_name="Google Chrome",
                bundle_id="com.google.Chrome",
                process_id=123,
                window_title="IntentOS live capture",
            )

        def fake_active_tab(app_name, bundle_id):
            calls.append("browser")
            return BrowserTab(
                browser_name=app_name,
                bundle_id=bundle_id,
                url="https://chatgpt.com/c/intent-os",
                title="ChatGPT - IntentOS live capture",
                domain="chatgpt.com",
                source="live_browser_osascript",
            )

        def fake_utc_now():
            return now

        def fake_sleep(seconds):
            nonlocal now
            now = now + timedelta(seconds=seconds)

        try:
            live.frontmost_app_snapshot = fake_frontmost
            live.active_browser_tab = fake_active_tab
            live.utc_now = fake_utc_now
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                config = LiveCaptureConfig(
                    output_path=root / "events.jsonl",
                    privacy_policy_path=Path("data/capture/privacy_policy.json"),
                    interval_seconds=1,
                    timeline_output_path=root / "timeline.jsonl",
                    summary_json_path=root / "summary.json",
                    summary_text_path=root / "summary.txt",
                    status_json_path=root / "status.json",
                    max_samples=2,
                )
                result = live.run_live_capture(config, sleeper=fake_sleep)
                events = read_events_jsonl(config.output_path)
                timeline = read_events_jsonl(config.timeline_output_path)
                summary = json.loads(config.summary_json_path.read_text())
                status = json.loads(config.status_json_path.read_text())
        finally:
            live.frontmost_app_snapshot = original_frontmost
            live.active_browser_tab = original_active_tab
            live.utc_now = original_utc_now

        self.assertEqual(result, {"samples": 2, "events": 2, "timeline_events": 1})
        self.assertEqual(len(events), 2)
        self.assertEqual(len(timeline), 1)
        self.assertEqual(timeline[0].duration_seconds, 2)
        self.assertEqual(timeline[0].metadata["sample_count"], 2)
        self.assertEqual(events[0].source_app, "Google Chrome")
        self.assertEqual(events[0].url, "https://chatgpt.com/c/intent-os")
        self.assertEqual(summary["items"][0]["duration_seconds"], 2)
        self.assertEqual(summary["items"][0]["sample_count"], 2)
        self.assertEqual(summary["items"][0]["source_app"], "Google Chrome")
        self.assertEqual(status["capture_mode"], "background_timeline")
        self.assertEqual(status["state"], "completed")
        self.assertEqual(status["events"], 2)
        self.assertEqual(status["timeline_events"], 1)
        self.assertEqual(status["timeline_output_path"], str(config.timeline_output_path))
        self.assertEqual(status["latest_event"]["source_app"], "Google Chrome")
        self.assertEqual(calls.count("frontmost"), 2)
        self.assertEqual(calls.count("browser"), 2)

    def test_live_capture_error_status_preserves_capture_error(self):
        original_capture_live_event = live.capture_live_event

        def fake_capture_live_event(config, sleeper):
            raise MacOSCaptureError("missing Accessibility permission")

        try:
            live.capture_live_event = fake_capture_live_event
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                config = LiveCaptureConfig(
                    output_path=root / "events.jsonl",
                    privacy_policy_path=Path("data/capture/privacy_policy.json"),
                    interval_seconds=1,
                    timeline_output_path=root / "timeline.jsonl",
                    status_json_path=root / "status.json",
                    max_samples=1,
                )
                with self.assertRaisesRegex(
                    MacOSCaptureError,
                    "missing Accessibility permission",
                ):
                    live.run_live_capture(config, sleeper=lambda seconds: None)
                status = json.loads(config.status_json_path.read_text())
        finally:
            live.capture_live_event = original_capture_live_event

        self.assertEqual(status["state"], "error")
        self.assertEqual(status["events"], 0)
        self.assertEqual(status["timeline_events"], 0)


if __name__ == "__main__":
    unittest.main()
