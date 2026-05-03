import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from intentos.activity import ActivityEvent
from intentos.beta import recorder, review, store


class BetaStoreTests(unittest.TestCase):
    def test_schema_persists_events_and_generates_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            with store.connect(db) as conn:
                store.init_db(conn)
                event = ActivityEvent(
                    "Google Chrome",
                    "chat.openai.com",
                    "Implement classifier",
                    "2026-04-27T09:00:00Z",
                    600,
                    "https://chat.openai.com/c/test",
                    {"source": "test", "domain": "chat.openai.com"},
                )
                recorder.record_event(conn, event)
                report = review.daily_review(conn, "2026-04-27", str(db))

            self.assertEqual(report["status"]["row_counts"]["activity_events"], 1)
            self.assertEqual(report["scope"]["label"], "Today since midnight")
            self.assertEqual(report["items"][0]["label"], "deep_work")

    def test_correction_layers_without_mutating_raw_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            event = ActivityEvent(
                "Google Chrome",
                "linkedin.com",
                "LinkedIn feed scrolling",
                "2026-04-27T10:00:00Z",
                300,
                "https://www.linkedin.com/feed/",
                {"source": "test", "domain": "linkedin.com"},
            )
            with store.connect(db) as conn:
                store.init_db(conn)
                recorder.record_event(conn, event)
                first = review.daily_review(conn, "2026-04-27", str(db))["items"][0]
                store.add_correction(conn, first, "learning", apply_to_future=True)
                corrected = review.daily_review(conn, "2026-04-27", str(db))["items"][0]
                raw = store.events_for_date(conn, "2026-04-27")[0]

            self.assertEqual(first["label"], "passive_consumption")
            self.assertEqual(corrected["label"], "learning")
            self.assertEqual(raw.title, "LinkedIn feed scrolling")

    def test_daily_review_top_queues_group_repeated_surfaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            events = [
                ActivityEvent(
                    "Codex",
                    "macos_frontmost",
                    "Implement Codex",
                    "2026-04-27T09:00:00Z",
                    600,
                ),
                ActivityEvent(
                    "WhatsApp",
                    "WhatsApp",
                    "WhatsApp",
                    "2026-04-27T09:10:00Z",
                    300,
                ),
                ActivityEvent(
                    "Codex",
                    "macos_frontmost",
                    "Implement Codex",
                    "2026-04-27T09:15:00Z",
                    420,
                ),
                ActivityEvent(
                    "WhatsApp",
                    "WhatsApp",
                    "WhatsApp",
                    "2026-04-27T09:22:00Z",
                    180,
                ),
                ActivityEvent(
                    "Codex",
                    "macos_frontmost",
                    "Implement Codex",
                    "2026-04-27T09:25:00Z",
                    240,
                ),
            ]
            with store.connect(db) as conn:
                store.init_db(conn)
                for event in events:
                    recorder.record_event(conn, event)
                report = review.daily_review(conn, "2026-04-27", str(db))
                codex_segment = conn.execute(
                    """
                    SELECT duration_seconds, sample_count FROM classified_segments
                    WHERE source_app = ?
                    """,
                    ("Codex",),
                ).fetchone()

            codex_timeline_items = [
                item for item in report["items"] if item["source_app"] == "Codex"
            ]

            self.assertEqual(len(codex_timeline_items), 3)
            self.assertEqual(len(report["top_deep_work"]), 1)
            self.assertEqual(report["top_deep_work"][0]["title"], "Implement Codex")
            self.assertEqual(report["top_deep_work"][0]["duration_seconds"], 1260)
            self.assertEqual(report["top_deep_work"][0]["duration"], "21m")
            self.assertEqual(report["top_deep_work"][0]["sample_count"], 3)
            self.assertEqual(codex_segment["duration_seconds"], 1260)
            self.assertEqual(codex_segment["sample_count"], 3)
            self.assertEqual(len(report["top_reactive_surfaces"]), 1)
            self.assertEqual(report["top_reactive_surfaces"][0]["title"], "WhatsApp")
            self.assertEqual(report["top_reactive_surfaces"][0]["duration_seconds"], 480)

    def test_daily_review_low_confidence_queue_groups_and_sorts_by_duration(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            events = [
                ActivityEvent(
                    "Unknown App",
                    "unknown",
                    "Sparse Alpha",
                    "2026-04-27T09:00:00Z",
                    20,
                ),
                ActivityEvent(
                    "Unknown App",
                    "unknown",
                    "Sparse Beta",
                    "2026-04-27T09:01:00Z",
                    60,
                ),
                ActivityEvent(
                    "Unknown App",
                    "unknown",
                    "Sparse Alpha",
                    "2026-04-27T09:02:00Z",
                    25,
                ),
            ]
            with store.connect(db) as conn:
                store.init_db(conn)
                for event in events:
                    recorder.record_event(conn, event)
                report = review.daily_review(conn, "2026-04-27", str(db))

            self.assertEqual(len(report["low_confidence_segments"]), 2)
            self.assertEqual(report["low_confidence_segments"][0]["title"], "Sparse Beta")
            self.assertEqual(
                report["low_confidence_segments"][0]["duration_seconds"],
                60,
            )
            self.assertEqual(report["low_confidence_segments"][1]["title"], "Sparse Alpha")
            self.assertEqual(
                report["low_confidence_segments"][1]["duration_seconds"],
                45,
            )

    def test_retention_cleanup_removes_old_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            with store.connect(db) as conn:
                store.init_db(conn, retention_days=30)
                old = ActivityEvent("App", "Surface", "Old", "2026-03-01T00:00:00Z", 60)
                recent = ActivityEvent("App", "Surface", "Implement recent", "2026-04-20T00:00:00Z", 60)
                store.insert_event(conn, old)
                store.insert_event(conn, recent)
                removed = store.cleanup_old_events(
                    conn, datetime(2026, 4, 27, tzinfo=timezone.utc)
                )

            self.assertEqual(removed, 1)
            with store.connect(db) as conn:
                self.assertEqual(store.row_counts(conn)["activity_events"], 1)

    def test_delete_all_preserves_runtime_status_and_checkpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            with store.connect(db) as conn:
                store.init_db(conn)
                store.set_status(conn, "service_state", "running")
                store.insert_event(
                    conn,
                    ActivityEvent("App", "Surface", "Implement", "2026-04-27T09:00:00Z", 60),
                )
                store.delete_all(conn)
                status = store.status(conn, str(db))

            self.assertEqual(status["row_counts"]["activity_events"], 0)
            self.assertEqual(status["service"]["state"], "running")
            self.assertEqual(status["database"]["quick_check"], "ok")

    def test_idle_samples_are_not_counted_and_long_gaps_are_not_faked(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            with store.connect(db) as conn:
                store.init_db(conn)
                first = ActivityEvent("App", "Work", "Implement", "2026-04-27T09:00:00Z", 60)
                away = ActivityEvent(
                    "App",
                    "Work",
                    "Away",
                    "2026-04-27T09:01:00Z",
                    60,
                    metadata={"idle_seconds": 600},
                )
                later = ActivityEvent("App", "Work", "Implement later", "2026-04-27T10:00:00Z", 60)
                recorder.record_event(conn, first)
                self.assertIsNone(recorder.record_event(conn, away))
                recorder.record_event(conn, later)
                status = store.status(conn, str(db))

            self.assertEqual(status["row_counts"]["activity_events"], 2)
            self.assertEqual(status["capture"]["state"], "running")


if __name__ == "__main__":
    unittest.main()
