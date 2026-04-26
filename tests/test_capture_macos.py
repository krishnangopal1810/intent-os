import subprocess
import unittest
from datetime import datetime, timezone
from pathlib import Path

from intentos.capture.macos import (
    MacOSCaptureError,
    frontmost_app_snapshot,
    permission_help,
    snapshot_to_observation,
)


class CaptureMacOSTest(unittest.TestCase):
    def test_parses_frontmost_app_snapshot_fixture(self):
        fixture = json_fixture("data/capture/macos_frontmost_snapshot.json")

        snapshot = frontmost_app_snapshot(
            lambda command: subprocess.CompletedProcess(
                command,
                0,
                stdout=fixture["stdout"],
                stderr="",
            )
        )

        self.assertEqual(snapshot.app_name, fixture["expected"]["app_name"])
        self.assertEqual(snapshot.bundle_id, fixture["expected"]["bundle_id"])
        self.assertEqual(snapshot.process_id, fixture["expected"]["process_id"])
        self.assertEqual(snapshot.window_title, fixture["expected"]["window_title"])

    def test_parses_frontmost_app_snapshot(self):
        def runner(command):
            self.assertEqual(command[0], "osascript")
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="Safari\ncom.apple.Safari\n123\nExample Window\n",
                stderr="",
            )

        snapshot = frontmost_app_snapshot(runner)

        self.assertEqual(snapshot.app_name, "Safari")
        self.assertEqual(snapshot.bundle_id, "com.apple.Safari")
        self.assertEqual(snapshot.process_id, 123)
        self.assertEqual(snapshot.window_title, "Example Window")

    def test_reports_permission_help_on_failure(self):
        def runner(command):
            return subprocess.CompletedProcess(
                command,
                1,
                stdout="",
                stderr="System Events got an error: Not authorized",
            )

        with self.assertRaisesRegex(MacOSCaptureError, "Accessibility permission"):
            frontmost_app_snapshot(runner)

    def test_rejects_invalid_process_id(self):
        def runner(command):
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="Safari\ncom.apple.Safari\nnot-a-pid\nExample Window\n",
                stderr="",
            )

        with self.assertRaisesRegex(MacOSCaptureError, "invalid process id"):
            frontmost_app_snapshot(runner)

    def test_snapshot_converts_to_capture_observation(self):
        snapshot = frontmost_app_snapshot(
            lambda command: subprocess.CompletedProcess(
                command,
                0,
                stdout="VS Code\ncom.microsoft.VSCode\n456\ncapture.py\n",
                stderr="",
            )
        )

        observation = snapshot_to_observation(
            snapshot,
            datetime(2026, 4, 26, 10, 0, tzinfo=timezone.utc),
            datetime(2026, 4, 26, 10, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(observation.app_name, "VS Code")
        self.assertEqual(observation.source, "macos_frontmost")
        self.assertEqual(observation.metadata["capture_mode"], "manual_live_sensor")

    def test_permission_help_includes_system_events_detail(self):
        message = permission_help("Not authorized")

        self.assertIn("Accessibility permission", message)
        self.assertIn("Not authorized", message)


def json_fixture(path):
    import json

    return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
