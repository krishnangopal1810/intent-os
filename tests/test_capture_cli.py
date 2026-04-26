import unittest
from datetime import datetime, timezone

import intentos.capture_cli as capture_cli
from intentos.capture.browser import BrowserTab
from intentos.capture.macos import MacOSAppSnapshot


class CaptureCliTest(unittest.TestCase):
    def test_live_browser_snapshot_is_taken_before_duration_sleep(self):
        calls = []
        snapshot = MacOSAppSnapshot(
            app_name="Chrome",
            bundle_id="com.google.Chrome",
            process_id=123,
            window_title="Initial tab",
        )
        tab = BrowserTab(
            browser_name="Chrome",
            bundle_id="com.google.Chrome",
            url="https://example.com/initial",
            title="Initial tab",
            domain="example.com",
            source="live_browser_osascript",
        )
        original_frontmost = capture_cli.frontmost_app_snapshot
        original_active_tab = capture_cli.active_browser_tab
        original_sleep = capture_cli.time.sleep
        original_utc_now = capture_cli.utc_now

        def fake_frontmost():
            calls.append("frontmost")
            return snapshot

        def fake_active_tab(app_name, bundle_id):
            calls.append("browser")
            self.assertEqual(app_name, "Chrome")
            self.assertEqual(bundle_id, "com.google.Chrome")
            return tab

        def fake_sleep(duration):
            calls.append("sleep")
            self.assertEqual(duration, 5)

        def fake_utc_now():
            calls.append("utc_now")
            if calls.count("utc_now") == 1:
                return datetime(2026, 4, 26, 10, 0, tzinfo=timezone.utc)
            return datetime(2026, 4, 26, 10, 0, 5, tzinfo=timezone.utc)

        try:
            capture_cli.frontmost_app_snapshot = fake_frontmost
            capture_cli.active_browser_tab = fake_active_tab
            capture_cli.time.sleep = fake_sleep
            capture_cli.utc_now = fake_utc_now

            observation, browser_by_app = capture_cli.capture_live_observation_and_browser(5)
        finally:
            capture_cli.frontmost_app_snapshot = original_frontmost
            capture_cli.active_browser_tab = original_active_tab
            capture_cli.time.sleep = original_sleep
            capture_cli.utc_now = original_utc_now

        self.assertLess(calls.index("browser"), calls.index("sleep"))
        self.assertEqual(observation.app_name, "Chrome")
        self.assertEqual(browser_by_app["chrome"].url, "https://example.com/initial")


if __name__ == "__main__":
    unittest.main()
