import json
import tempfile
import unittest
from pathlib import Path

from intentos.activity import ActivityEvent, load_events
from intentos.activity_evaluate import evaluate
from intentos.classifier import BehaviorLabel, classify_event
from intentos.reporting import activity_report


EVENTS = Path("data/activity/multi_app_events.json")
EVALUATION = Path("data/activity/evaluation_set.json")


class ActivityClassificationTest(unittest.TestCase):
    def test_multi_app_report_aggregates_behavior_labels(self):
        result = activity_report(load_events(EVENTS))

        self.assertEqual(result["summary"]["total_duration"], "3h 30m")
        labels = result["summary"]["labels"]
        self.assertEqual(labels["deep_work"]["duration"], "1h 10m")
        self.assertEqual(labels["passive_consumption"]["duration"], "40m")
        self.assertEqual(labels["admin"]["duration"], "30m")
        self.assertIn("largest behavior bucket was deep_work", result["summary"]["narrative"])

    def test_report_sessionizes_adjacent_same_url_rows_and_shows_seconds(self):
        events = [
            ActivityEvent(
                source_app="Google Chrome",
                surface="127.0.0.1:55123",
                title="IntentOS",
                started_at="2026-04-26T18:34:03Z",
                duration_seconds=2,
                url="http://127.0.0.1:55123/site/index.html",
                metadata={},
            ),
            ActivityEvent(
                source_app="Google Chrome",
                surface="127.0.0.1:55123",
                title="IntentOS",
                started_at="2026-04-26T18:34:05Z",
                duration_seconds=2,
                url="http://127.0.0.1:55123/site/index.html",
                metadata={},
            ),
            ActivityEvent(
                source_app="Google Chrome",
                surface="youtube.com",
                title="Dhurandhar - YouTube",
                started_at="2026-04-26T18:34:07Z",
                duration_seconds=2,
                url="https://www.youtube.com/watch?v=example",
                metadata={},
            ),
        ]

        result = activity_report(events)

        self.assertEqual(result["summary"]["total_duration"], "6s")
        self.assertEqual(result["summary"]["labels"]["deep_work"]["duration"], "4s")
        self.assertEqual(result["summary"]["labels"]["unknown"]["duration"], "2s")
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["duration"], "4s")
        self.assertEqual(result["items"][0]["sample_count"], 2)
        self.assertEqual(result["items"][1]["duration"], "2s")

    def test_report_keeps_adjacent_non_url_titles_separate(self):
        events = [
            ActivityEvent(
                source_app="Codex",
                surface="macos_frontmost",
                title="Implement live capture",
                started_at="2026-04-26T18:34:03Z",
                duration_seconds=2,
                metadata={},
            ),
            ActivityEvent(
                source_app="Codex",
                surface="macos_frontmost",
                title="Review pull request",
                started_at="2026-04-26T18:34:05Z",
                duration_seconds=2,
                metadata={},
            ),
        ]

        result = activity_report(events)

        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["title"], "Implement live capture")
        self.assertEqual(result["items"][1]["title"], "Review pull request")

    def test_chatgpt_is_classified_by_conversation_intent(self):
        coding = ActivityEvent(
            source_app="ChatGPT",
            surface="chatgpt.com",
            title="Debug failing Python unittest",
            started_at="2026-04-25T09:00:00Z",
            duration_seconds=600,
            metadata={"conversation_summary": "Implement code and tests."},
        )
        fun = ActivityEvent(
            source_app="ChatGPT",
            surface="chatgpt.com",
            title="Make up a silly superhero story",
            started_at="2026-04-25T20:00:00Z",
            duration_seconds=300,
            metadata={"conversation_summary": "Casual fun conversation."},
        )

        self.assertEqual(classify_event(coding).label, BehaviorLabel.DEEP_WORK)
        self.assertEqual(classify_event(fun).label, BehaviorLabel.ENTERTAINMENT)

    def test_live_browser_surfaces_use_domain_and_title_context(self):
        cases = [
            (
                ActivityEvent(
                    "Google Chrome",
                    "bazel.build",
                    "BUILD Style Guide | Bazel",
                    "2026-05-03T09:00:00Z",
                    600,
                    url="https://bazel.build/build/style-guide",
                ),
                BehaviorLabel.LEARNING,
            ),
            (
                ActivityEvent(
                    "Google Chrome",
                    "youtube.com",
                    "Final | India vs Pakistan | DP World Asia Cup 2025 - YouTube",
                    "2026-05-03T09:10:00Z",
                    300,
                    url="https://www.youtube.com/watch?v=MAm0RLQpYas",
                ),
                BehaviorLabel.ENTERTAINMENT,
            ),
            (
                ActivityEvent(
                    "Google Chrome",
                    "google.com",
                    "cafe graze brunch - Google Search",
                    "2026-05-03T09:20:00Z",
                    30,
                    url="https://www.google.com/search?q=cafe+graze+brunch",
                ),
                BehaviorLabel.ADMIN,
            ),
            (
                ActivityEvent(
                    "Google Chrome",
                    "natureville.in",
                    "Cafe Graze",
                    "2026-05-03T09:21:00Z",
                    45,
                    url="https://natureville.in/cafe-graze/",
                ),
                BehaviorLabel.ADMIN,
            ),
            (
                ActivityEvent(
                    "Google Chrome",
                    "amazon.in",
                    "Instant Pot Duo 6QT 7-in-1 Electric Pressure Cooker",
                    "2026-05-03T09:30:00Z",
                    155,
                    url="https://www.amazon.in/Instant-Pot/dp/example",
                ),
                BehaviorLabel.ADMIN,
            ),
            (
                ActivityEvent(
                    "Google Chrome",
                    "github.com",
                    "krishnangopal1810/intent-os",
                    "2026-05-03T09:40:00Z",
                    60,
                    url="https://github.com/krishnangopal1810/intent-os",
                ),
                BehaviorLabel.DEEP_WORK,
            ),
            (
                ActivityEvent(
                    "Google Chrome",
                    "127.0.0.1:62471",
                    "IntentOS",
                    "2026-05-03T09:45:00Z",
                    60,
                    url="http://127.0.0.1:62471/site/index.html?mode=beta",
                ),
                BehaviorLabel.DEEP_WORK,
            ),
            (
                ActivityEvent(
                    "Google Chrome",
                    "x.com",
                    "Prem Soni on X: property thread / X",
                    "2026-05-03T09:50:00Z",
                    70,
                    url="https://x.com/ValueWithPrem/status/2050767004001595781",
                ),
                BehaviorLabel.PASSIVE_CONSUMPTION,
            ),
        ]

        for event, expected in cases:
            with self.subTest(title=event.title):
                self.assertEqual(classify_event(event).label, expected)

    def test_sparse_browser_homepage_remains_unknown(self):
        event = ActivityEvent(
            "Google Chrome",
            "google.com",
            "Google",
            "2026-05-03T10:00:00Z",
            600,
            url="https://www.google.com/",
        )

        classification = classify_event(event)

        self.assertEqual(classification.label, BehaviorLabel.UNKNOWN)
        self.assertLess(classification.confidence, 0.5)

    def test_ambiguous_activity_remains_unknown(self):
        event = ActivityEvent(
            source_app="Browser",
            surface="unknown",
            title="Python drama recap",
            started_at="2026-04-25T22:00:00Z",
            duration_seconds=300,
            metadata={},
        )

        classification = classify_event(event)

        self.assertEqual(classification.label, BehaviorLabel.UNKNOWN)
        self.assertLess(classification.confidence, 0.5)

    def test_invalid_activity_event_is_rejected_at_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "source_app": "ChatGPT",
                            "surface": "chatgpt.com",
                            "title": "Debug code",
                            "started_at": "2026-04-25T09:00:00Z",
                            "duration_seconds": -1,
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "duration_seconds"):
                load_events(path)

    def test_labeled_multi_app_evaluation_passes_threshold(self):
        result = evaluate(EVALUATION)

        self.assertGreaterEqual(result["accuracy"], 85.0)
        self.assertEqual(result["correct"], result["total"])


if __name__ == "__main__":
    unittest.main()
