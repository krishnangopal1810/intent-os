import tempfile
import unittest
from pathlib import Path

from intentos.activity import ActivityEvent
from intentos.beta import native_recorder, store


class BetaNativeRecorderTests(unittest.TestCase):
    def test_native_recorder_writes_activity_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            config = native_recorder.NativeRecorderConfig(
                db_path=db,
                privacy_policy_path=Path("data/capture/privacy_policy.json"),
                interval_seconds=1,
                max_samples=1,
            )

            result = native_recorder.run_native_recorder(
                config,
                sleeper=lambda _seconds: None,
                capture_once=lambda _config, _sleeper: [sample_event()],
                idle_seconds=lambda: None,
            )

            with store.connect(db) as conn:
                store.init_db(conn)
                counts = store.row_counts(conn)
                status = store.status(conn, str(db))

        self.assertEqual(result["samples"], 1)
        self.assertEqual(result["events"], 1)
        self.assertEqual(counts["activity_events"], 1)
        self.assertEqual(status["native_recorder"]["state"], "completed")
        self.assertEqual(status["native_recorder"]["last_event_at"], sample_event().started_at)

    def test_native_recorder_does_not_count_idle_samples_as_activity(self):
        idle_event = sample_event(metadata={"idle_seconds": 301})
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            config = native_recorder.NativeRecorderConfig(
                db_path=db,
                privacy_policy_path=Path("data/capture/privacy_policy.json"),
                interval_seconds=1,
                max_samples=1,
            )

            result = native_recorder.run_native_recorder(
                config,
                sleeper=lambda _seconds: None,
                capture_once=lambda _config, _sleeper: [idle_event],
                idle_seconds=lambda: None,
            )

            with store.connect(db) as conn:
                store.init_db(conn)
                counts = store.row_counts(conn)
                capture_state = store.runtime_value(conn, "capture_state")

        self.assertEqual(result["events"], 0)
        self.assertEqual(counts["activity_events"], 0)
        self.assertEqual(capture_state, "away")

    def test_native_recorder_skips_capture_while_paused(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            config = native_recorder.NativeRecorderConfig(
                db_path=db,
                privacy_policy_path=Path("data/capture/privacy_policy.json"),
                interval_seconds=1,
                max_samples=1,
            )
            with store.connect(db) as conn:
                store.init_db(conn)
                store.set_pause(conn, "2999-01-01T00:00:00Z")

            result = native_recorder.run_native_recorder(
                config,
                sleeper=lambda _seconds: None,
                capture_once=unexpected_capture,
                idle_seconds=lambda: None,
            )

            with store.connect(db) as conn:
                store.init_db(conn)
                counts = store.row_counts(conn)
                capture_state = store.runtime_value(conn, "capture_state")

        self.assertEqual(result["samples"], 1)
        self.assertEqual(result["events"], 0)
        self.assertEqual(counts["activity_events"], 0)
        self.assertEqual(capture_state, "paused")

    def test_native_recorder_uses_real_idle_probe_before_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            config = native_recorder.NativeRecorderConfig(
                db_path=db,
                privacy_policy_path=Path("data/capture/privacy_policy.json"),
                interval_seconds=1,
                max_samples=1,
            )

            result = native_recorder.run_native_recorder(
                config,
                sleeper=lambda _seconds: None,
                capture_once=unexpected_capture,
                idle_seconds=lambda: 301,
            )

            with store.connect(db) as conn:
                store.init_db(conn)
                counts = store.row_counts(conn)
                capture_state = store.runtime_value(conn, "capture_state")

        self.assertEqual(result["samples"], 1)
        self.assertEqual(result["events"], 0)
        self.assertEqual(counts["activity_events"], 0)
        self.assertEqual(capture_state, "away")

    def test_parse_hid_idle_seconds(self):
        output = '  | |   "HIDIdleTime" = 12345678901\n'

        self.assertEqual(native_recorder.parse_hid_idle_seconds(output), 12)


def sample_event(metadata=None):
    return ActivityEvent(
        source_app="Google Chrome",
        surface="docs.example.com",
        title="Launch notes",
        started_at="2026-04-27T10:00:00Z",
        duration_seconds=5,
        url="https://docs.example.com/launch",
        metadata=metadata or {"source": "native_macos_recorder"},
    )


def unexpected_capture(_config, _sleeper):
    raise AssertionError("capture should not run")


if __name__ == "__main__":
    unittest.main()
