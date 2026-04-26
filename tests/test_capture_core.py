import json
import tempfile
import unittest
from pathlib import Path

from intentos.capture.core import parse_observation, observation_to_event
from intentos.capture.jsonl import read_events_jsonl, write_events_jsonl


class CaptureCoreTest(unittest.TestCase):
    def test_observation_converts_to_activity_event(self):
        observation = parse_observation(
            {
                "start_time": "2026-04-26T09:00:00Z",
                "end_time": "2026-04-26T09:05:00Z",
                "app_name": "VS Code",
                "bundle_id": "com.microsoft.VSCode",
                "process_id": 42,
                "window_title": "classifier.py - implement behavior scoring",
                "source": "fake_macos",
                "metadata": {"capture_mode": "fake_sensor"},
            }
        )

        event = observation_to_event(observation)

        self.assertEqual(event.source_app, "VS Code")
        self.assertEqual(event.duration_seconds, 300)
        self.assertEqual(event.title, "classifier.py - implement behavior scoring")
        self.assertEqual(event.metadata["bundle_id"], "com.microsoft.VSCode")
        self.assertEqual(event.metadata["capture_mode"], "fake_sensor")

    def test_rejects_invalid_duration(self):
        with self.assertRaisesRegex(ValueError, "duration must be positive"):
            parse_observation(
                {
                    "start_time": "2026-04-26T09:00:00Z",
                    "end_time": "2026-04-26T08:59:00Z",
                    "app_name": "VS Code",
                }
            )

    def test_rejects_non_object_metadata(self):
        with self.assertRaisesRegex(ValueError, "metadata must be an object"):
            parse_observation(
                {
                    "start_time": "2026-04-26T09:00:00Z",
                    "end_time": "2026-04-26T09:01:00Z",
                    "app_name": "VS Code",
                    "metadata": [],
                }
            )

    def test_jsonl_round_trip(self):
        raw = json.loads(Path("data/capture/fake_macos_observations.json").read_text())
        events = [observation_to_event(parse_observation(item, i)) for i, item in enumerate(raw)]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            count = write_events_jsonl(events, path)
            loaded = read_events_jsonl(path)

        self.assertEqual(count, len(events))
        self.assertEqual(len(loaded), len(events))
        self.assertEqual(loaded[0].source_app, "VS Code")
        self.assertEqual(loaded[-1].source_app, "Unknown App")


if __name__ == "__main__":
    unittest.main()
