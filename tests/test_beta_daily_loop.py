import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from intentos.activity import ActivityEvent
from intentos.beta import daily_loop, daily_state, loop_coach, recorder, review, store, weekly_patterns


class BetaDailyLoopTests(unittest.TestCase):
    def test_daily_intent_and_review_checkin_upsert_by_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            with store.connect(db) as conn:
                store.init_db(conn)
                first_intent = daily_state.upsert_daily_intent(
                    conn,
                    "2026-04-27",
                    "Ship IntentOS review",
                    "LinkedIn feed",
                    "Morning plan",
                )
                updated_intent = daily_state.upsert_daily_intent(
                    conn,
                    "2026-04-27",
                    "Ship sticky loop",
                    "Open-ended feeds",
                )
                first_checkin = daily_state.upsert_review_checkin(
                    conn,
                    "2026-04-27",
                    "mixed",
                    "Focus held, feed leaked.",
                    "Cap feed before lunch.",
                )
                updated_checkin = daily_state.upsert_review_checkin(
                    conn,
                    "2026-04-27",
                    "kept_focus",
                )

            self.assertEqual(first_intent["focus_text"], "Ship IntentOS review")
            self.assertEqual(updated_intent["focus_text"], "Ship sticky loop")
            self.assertEqual(updated_intent["avoid_text"], "Open-ended feeds")
            self.assertEqual(first_checkin["outcome"], "mixed")
            self.assertEqual(updated_checkin["outcome"], "kept_focus")
            self.assertEqual(updated_checkin["reflection_text"], "")

    def test_daily_loop_prompt_states_and_accuracy_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            event = ActivityEvent(
                "Google Chrome",
                "linkedin.com",
                "LinkedIn feed scrolling",
                "2026-04-27T10:00:00Z",
                7200,
                "https://www.linkedin.com/feed/",
                {"source": "test", "domain": "linkedin.com"},
            )
            with store.connect(db) as conn:
                store.init_db(conn)
                missing = daily_loop.daily_loop(
                    conn,
                    "2026-04-27",
                    str(db),
                    now=datetime(2026, 4, 27, 8, 0, tzinfo=timezone.utc),
                )
                recorder.record_event(conn, event)
                daily_state.upsert_daily_intent(
                    conn,
                    "2026-04-27",
                    "Implement sticky loop",
                    "LinkedIn feed",
                )
                due = daily_loop.daily_loop(
                    conn,
                    "2026-04-27",
                    str(db),
                    now=datetime(2026, 4, 27, 10, 0, tzinfo=timezone.utc),
                )
                segment = review.daily_review(conn, "2026-04-27", str(db))["items"][0]
                store.add_correction(conn, segment, "learning")
                corrected = daily_loop.daily_loop(
                    conn,
                    "2026-04-27",
                    str(db),
                    now=datetime(2026, 4, 27, 10, 0, tzinfo=timezone.utc),
                )
                daily_state.upsert_review_checkin(
                    conn,
                    "2026-04-27",
                    "mixed",
                    "Feed leaked.",
                    "Set a cap before opening LinkedIn.",
                )
                completed = daily_loop.daily_loop(
                    conn,
                    "2026-04-27",
                    str(db),
                    now=datetime(2026, 4, 27, 18, 0, tzinfo=timezone.utc),
                )

            self.assertTrue(missing["prompt"]["intent_due"])
            self.assertEqual(missing["prompt"]["state"], "intent_due")
            self.assertEqual(due["prompt"]["state"], "review_due")
            self.assertEqual(
                due["plan_vs_actual"]["matched_avoid"]["title"],
                "LinkedIn feed scrolling",
            )
            self.assertIn("intent_contract", due)
            self.assertIn("next_block", due)
            self.assertIn("correction_reward", due)
            self.assertIn("linkedin", due["intent_contract"]["avoid_tokens"])
            self.assertEqual(due["next_block"]["target_surface"], "linkedin.com")
            self.assertIn("Close", due["next_block"]["title"])
            self.assertEqual(corrected["correction_count"], 1)
            self.assertEqual(corrected["correction_reward"]["correction_count"], 1)
            self.assertTrue(corrected["correction_reward"]["improved_surfaces"])
            self.assertEqual(completed["prompt"]["state"], "review_complete")
            self.assertEqual(
                completed["review_checkin"]["next_adjustment"],
                "Set a cap before opening LinkedIn.",
            )

    def test_focus_rescue_states_and_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            with store.connect(db) as conn:
                store.init_db(conn)
                missing = daily_loop.daily_loop(conn, "2026-04-27", str(db))
                daily_state.upsert_daily_intent(
                    conn,
                    "2026-04-27",
                    "Implement sticky loop",
                    "LinkedIn feed",
                )
                insufficient = daily_loop.daily_loop(conn, "2026-04-27", str(db))
                recorder.record_event(
                    conn,
                    ActivityEvent(
                        "VS Code",
                        "intent-os",
                        "Implement sticky loop",
                        "2026-04-27T09:00:00Z",
                        600,
                    ),
                )
                protected = daily_loop.daily_loop(conn, "2026-04-27", str(db))
                recorder.record_event(
                    conn,
                    ActivityEvent(
                        "Google Chrome",
                        "linkedin.com",
                        "LinkedIn feed scrolling",
                        "2026-04-27T09:15:00Z",
                        240,
                        "https://www.linkedin.com/feed/",
                        {"source": "test", "domain": "linkedin.com"},
                    ),
                )
                under_threshold = daily_loop.daily_loop(conn, "2026-04-27", str(db))
                recorder.record_event(
                    conn,
                    ActivityEvent(
                        "Google Chrome",
                        "linkedin.com",
                        "LinkedIn feed scrolling",
                        "2026-04-27T09:19:00Z",
                        60,
                        "https://www.linkedin.com/feed/",
                        {"source": "test", "domain": "linkedin.com"},
                    ),
                )
                recovery = daily_loop.daily_loop(conn, "2026-04-27", str(db))
                key = recovery["focus_rescue"]["rescue_key"]
                daily_state.record_focus_rescue_action(
                    conn,
                    "2026-04-27",
                    key,
                    "continue_intentionally",
                    recovery["focus_rescue"]["primary_evidence"]["evidence_id"],
                )
                leaking = daily_loop.daily_loop(conn, "2026-04-27", str(db))
                daily_state.record_focus_rescue_action(
                    conn,
                    "2026-04-27",
                    key,
                    "return_to_focus",
                    recovery["focus_rescue"]["primary_evidence"]["evidence_id"],
                )
                returned = daily_loop.daily_loop(conn, "2026-04-27", str(db))

        self.assertEqual(missing["focus_rescue"]["state"], "intent_needed")
        self.assertEqual(insufficient["focus_rescue"]["state"], "evidence_insufficient")
        self.assertEqual(protected["focus_rescue"]["state"], "focus_protected")
        self.assertEqual(under_threshold["focus_rescue"]["state"], "focus_protected")
        self.assertEqual(recovery["focus_rescue"]["state"], "recovery_available")
        self.assertEqual(recovery["focus_rescue"]["avoid_seconds"], 300)
        self.assertEqual(leaking["focus_rescue"]["state"], "avoid_leaking")
        self.assertEqual(leaking["focus_rescue"]["latest_action"]["action"], "continue_intentionally")
        self.assertEqual(returned["focus_rescue"]["state"], "focus_protected")
        self.assertEqual(returned["focus_rescue"]["latest_action"]["action"], "return_to_focus")

    def test_intent_contract_next_block_empty_focus_and_trust_gap_cases(self):
        contract = loop_coach.build_intent_contract(
            {
                "focus_text": "Protect Codex and IntentOS docs",
                "avoid_text": "Cap LinkedIn feed scrolling",
                "note": "Review implementation tomorrow",
            },
            [
                {
                    "source_app": "Codex",
                    "surface": "IntentOS repo",
                    "title": "Implement IntentOS daily coach",
                    "label": "deep_work",
                    "duration_seconds": 3600,
                    "segment_key": "focus-1",
                },
                {
                    "source_app": "Google Chrome",
                    "surface": "linkedin.com",
                    "title": "LinkedIn feed scrolling",
                    "label": "passive_consumption",
                    "duration_seconds": 900,
                    "segment_key": "avoid-1",
                },
            ],
        )
        self.assertIn("codex", contract["focus_tokens"])
        self.assertIn("linkedin", contract["avoid_tokens"])
        self.assertEqual(contract["matched_focus_signals"][0]["evidence_id"], "focus-1")
        self.assertEqual(contract["matched_avoid_signals"][0]["evidence_id"], "avoid-1")

        empty_next = loop_coach.build_next_block(None, {"focus_seconds": 0, "reactive_seconds": 0}, [], 0)
        self.assertEqual(empty_next["title"], "Work normally for 20 minutes")

        trust_next = loop_coach.build_next_block(
            None,
            {"focus_seconds": 1200, "reactive_seconds": 0, "matched_focus": None},
            [
                {
                    "source_app": "Google Chrome",
                    "surface": "Unknown",
                    "title": "Sparse local metadata",
                    "label": "unknown",
                    "confidence": 0.2,
                    "duration_seconds": 600,
                    "segment_key": "trust-1",
                }
            ],
            1,
        )
        self.assertEqual(trust_next["title"], "Fix the trust gap first")
        self.assertEqual(trust_next["source_evidence_ids"], ["trust-1"])

    def test_plan_matching_ignores_tokens_on_wrong_behavior_labels(self):
        focus = {"source_app": "VS Code", "surface": "intent-os", "title": "Implement LinkedIn integration", "label": "deep_work", "duration_seconds": 1800, "segment_key": "focus-1"}
        reactive = {"source_app": "Google Chrome", "surface": "example.com", "title": "Dashboard review gossip reel", "label": "entertainment", "duration_seconds": 600, "segment_key": "reactive-1"}
        plan = loop_coach.compare_plan_to_actual(
            {"focus_text": "Ship dashboard review", "avoid_text": "LinkedIn feed"},
            [focus, reactive],
            focus_seconds=1800, reactive_seconds=600,
            correction_count=0, low_confidence_count=0,
        )

        self.assertEqual(plan["matched_focus"]["evidence_id"], "focus-1")
        self.assertEqual(plan["matched_avoid"]["evidence_id"], "reactive-1")
        self.assertNotEqual(plan["matched_avoid"]["title"], "Implement LinkedIn integration")
        self.assertNotEqual(plan["matched_focus"]["title"], "Dashboard review gossip reel")

    def test_weekly_patterns_aggregate_local_activity_and_corrections(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            with store.connect(db) as conn:
                store.init_db(conn)
                recorder.record_event(
                    conn,
                    ActivityEvent(
                        "Codex",
                        "IntentOS repo",
                        "Implement IntentOS daily coach",
                        "2026-04-27T05:00:00Z",
                        3600,
                        None,
                        {"source": "test"},
                    ),
                )
                recorder.record_event(
                    conn,
                    ActivityEvent(
                        "Google Chrome",
                        "linkedin.com",
                        "LinkedIn feed scrolling",
                        "2026-04-28T07:00:00Z",
                        1800,
                        "https://www.linkedin.com/feed/",
                        {"source": "test"},
                    ),
                )
                daily_state.upsert_daily_intent(conn, "2026-04-27", "Protect Codex", "LinkedIn")
                daily_state.upsert_review_checkin(conn, "2026-04-27", "kept_focus")
                segment = review.daily_review(conn, "2026-04-28", str(db))["items"][0]
                store.add_correction(conn, segment, "learning")
                review.daily_review(conn, "2026-04-28", str(db))
                payload = weekly_patterns.weekly_patterns(conn, "2026-04-27", str(db))

        self.assertEqual(payload["week_start"], "2026-04-27")
        self.assertEqual(len(payload["patterns"]), 3)
        self.assertEqual(payload["intent_days"], 1)
        self.assertEqual(payload["review_days"], 1)
        self.assertIn("Best focus window", [card["title"] for card in payload["patterns"]])
        self.assertGreater(payload["correction_trust_trend"]["correction_count"], 0)


if __name__ == "__main__":
    unittest.main()
