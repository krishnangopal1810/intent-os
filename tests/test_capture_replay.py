import json
import tempfile
import unittest
from pathlib import Path

from intentos.capture_cli import normalize_observations
from intentos.capture_replay import replay_capture


class CaptureReplayTest(unittest.TestCase):
    def test_normalize_and_replay_fake_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "events.jsonl"
            count = normalize_observations(
                Path("data/capture/fake_macos_observations.json"),
                output,
                Path("data/capture/privacy_policy.json"),
                Path("data/capture/fake_browser_tabs.json"),
            )
            report = replay_capture(output)

        self.assertEqual(count, 6)
        self.assertGreater(report["summary"]["total_seconds"], 0)
        labels = report["summary"]["labels"]
        self.assertIn("deep_work", labels)
        self.assertIn("admin", labels)
        self.assertIn("passive_consumption", labels)

    def test_rejects_empty_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "events.jsonl"
            output.write_text("", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "at least one ActivityEvent"):
                replay_capture(output)

    def test_allows_empty_jsonl_for_live_observation_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "events.jsonl"
            output.write_text("", encoding="utf-8")

            report = replay_capture(output, allow_empty=True)

        self.assertEqual(report["summary"]["total_seconds"], 0)
        self.assertEqual(report["summary"]["labels"], {})
        self.assertEqual(report["items"], [])

    def test_rejects_malformed_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "events.jsonl"
            output.write_text("{bad json\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "line 1 is invalid JSON"):
                replay_capture(output)

    def test_json_replay_output_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "events.jsonl"
            normalize_observations(
                Path("data/capture/fake_macos_observations.json"),
                output,
                Path("data/capture/privacy_policy.json"),
                None,
            )
            report = replay_capture(output)

        json.dumps(report)
        self.assertIn("items", report)

    def test_browser_title_participates_in_privacy_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            observations = Path(tmp) / "observations.json"
            tabs = Path(tmp) / "tabs.json"
            output = Path(tmp) / "events.jsonl"
            observations.write_text(
                json.dumps(
                    [
                        {
                            "start_time": "2026-04-26T10:00:00Z",
                            "end_time": "2026-04-26T10:01:00Z",
                            "app_name": "Chrome",
                            "window_title": "Generic Browser",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            tabs.write_text(
                json.dumps(
                    [
                        {
                            "browser_name": "Chrome",
                            "url": "https://example.com/private-search",
                            "title": "Private Browsing - Search",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            count = normalize_observations(
                observations,
                output,
                Path("data/capture/privacy_policy.json"),
                tabs,
            )

        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
