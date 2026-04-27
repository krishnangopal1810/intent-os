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
