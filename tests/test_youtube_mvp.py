import json
import tempfile
import unittest
from pathlib import Path

from intentos.youtube import (
    Label,
    YouTubeActivity,
    classify_activity,
    classify_all,
    load_activities,
    narrative,
    report,
    summarize,
)


FIXTURE = Path("data/youtube/sample_watch_history.json")


class YouTubeMvpTest(unittest.TestCase):
    def test_fixture_produces_uncomfortable_summary(self):
        result = report(FIXTURE)

        self.assertEqual(result["summary"]["total_duration"], "2h")
        self.assertEqual(result["summary"]["passive_consumption_percentage"], 68.3)
        self.assertEqual(result["summary"]["learning_percentage"], 31.7)
        self.assertEqual(
            result["summary"]["narrative"],
            "You spent 2h on YouTube. 68% was passive consumption and 32% was learning.",
        )

    def test_each_fixture_item_has_label_confidence_and_reason(self):
        result = report(FIXTURE)

        labels = [item["label"] for item in result["items"]]
        self.assertEqual(labels.count("learning"), 2)
        self.assertEqual(labels.count("entertainment"), 4)
        self.assertNotIn("unknown", labels)
        for item in result["items"]:
            self.assertGreaterEqual(item["confidence"], 0.55)
            self.assertTrue(item["reason"])

    def test_unknown_is_preserved_for_sparse_metadata(self):
        activity = YouTubeActivity(
            title="Untitled video",
            url="https://www.youtube.com/watch?v=unknown",
            channel=None,
            watched_at="2026-04-25T22:00:00Z",
            duration_seconds=300,
        )

        classification = classify_activity(activity)

        self.assertEqual(classification.label, Label.UNKNOWN)
        self.assertLess(classification.confidence, 0.5)

    def test_balanced_cues_do_not_force_a_label(self):
        activity = YouTubeActivity(
            title="Python drama recap",
            url="https://www.youtube.com/watch?v=balanced",
            channel=None,
            watched_at="2026-04-25T22:00:00Z",
            duration_seconds=300,
        )

        classification = classify_activity(activity)

        self.assertEqual(classification.label, Label.UNKNOWN)

    def test_invalid_duration_is_rejected_at_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "title": "Python tutorial",
                            "url": "https://www.youtube.com/watch?v=bad",
                            "watched_at": "2026-04-25T22:00:00Z",
                            "duration_seconds": 0,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "duration_seconds"):
                load_activities(path)

    def test_summary_counts_unknown_duration(self):
        activities = [
            YouTubeActivity(
                title="Architecture deep dive",
                url="https://www.youtube.com/watch?v=learning",
                channel=None,
                watched_at="2026-04-25T22:00:00Z",
                duration_seconds=600,
            ),
            YouTubeActivity(
                title="Untitled upload",
                url="https://www.youtube.com/watch?v=unknown",
                channel=None,
                watched_at="2026-04-25T22:12:00Z",
                duration_seconds=300,
            ),
        ]

        summary = summarize(classify_all(activities))

        self.assertEqual(summary.learning_seconds, 600)
        self.assertEqual(summary.unknown_seconds, 300)
        self.assertEqual(narrative(summary), "You spent 15m on YouTube. 0% was passive consumption and 67% was learning. 33% was unknown.")


if __name__ == "__main__":
    unittest.main()
