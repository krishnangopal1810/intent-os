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
