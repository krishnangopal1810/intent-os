import unittest

from beta_service_harness import BETA_DATE, BetaServiceHarness


class BetaOnboardingApiTests(unittest.TestCase):
    def test_onboarding_permissions_daily_loop_and_review_flow(self):
        with BetaServiceHarness() as harness:
            harness.post_fixture_events()
            onboarding = harness.get("/api/onboarding")
            permission_check = harness.post("/api/permissions/check", {})
            settings = harness.post("/api/open-system-settings", {"target": "automation"})
            early_complete = harness.post_status("/api/onboarding", {"action": "complete"})
            privacy_ack = harness.post("/api/onboarding", {"action": "acknowledge_privacy"})
            intent = harness.post(
                "/api/daily-intent",
                {
                    "date": BETA_DATE,
                    "focus_text": "Ship beta loop",
                    "avoid_text": "LinkedIn feed",
                },
            )
            completed = harness.post("/api/onboarding", {"action": "complete"})
            setup_report = harness.get("/api/setup-report")
            loop = harness.get(f"/api/daily-loop?date={BETA_DATE}")
            rescue = loop["focus_rescue"]
            rescue_shown = harness.post(
                "/api/focus-rescue-action",
                {
                    "date": BETA_DATE,
                    "rescue_key": rescue["rescue_key"],
                    "action": "shown",
                    "evidence_id": rescue["primary_evidence"]["evidence_id"],
                },
            )
            invalid_rescue = harness.post_status(
                "/api/focus-rescue-action",
                {
                    "date": BETA_DATE,
                    "rescue_key": rescue["rescue_key"],
                    "action": "invalid",
                },
            )
            weekly = harness.get(f"/api/weekly-patterns?week_start={BETA_DATE}")
            checkin = harness.post(
                "/api/review-checkin",
                {
                    "date": BETA_DATE,
                    "outcome": "mixed",
                    "reflection_text": "Loop is visible.",
                    "next_adjustment": "Review before shutdown.",
                },
            )
            completed_loop = harness.get(f"/api/daily-loop?date={BETA_DATE}")
            activation_after_review = harness.get("/api/status")

        self.assertFalse(onboarding["onboarding"]["completed"])
        self.assertEqual(permission_check["permissions"]["accessibility"]["state"], "ok")
        self.assertEqual(settings["status"], "validated")
        self.assertIn("browser entry", " ".join(settings["guidance"]["steps"]))
        self.assertEqual(early_complete, 400)
        self.assertTrue(privacy_ack["privacy_acknowledged"])
        self.assertEqual(intent["intent"]["focus_text"], "Ship beta loop")
        self.assertTrue(completed["completed"])
        self.assertEqual(setup_report["setup_report"]["capture_preview"]["state"], "ok")
        self.assertNotIn("window_title", setup_report["setup_report"]["capture_preview"])
        self.assertIn("preflight", setup_report["setup_report"])
        self.assertEqual(loop["intent"]["avoid_text"], "LinkedIn feed")
        self.assertIn("intent_contract", loop)
        self.assertIn("next_block", loop)
        self.assertIn("correction_reward", loop)
        self.assertIn("evening_receipt", loop)
        self.assertIn(rescue["state"], {"focus_protected", "recovery_available"})
        self.assertEqual(rescue_shown["status"], "recorded")
        self.assertEqual(rescue_shown["action"]["action"], "shown")
        self.assertEqual(invalid_rescue, 400)
        self.assertEqual(len(weekly["patterns"]), 3)
        self.assertIn("week", weekly["narrative"].lower())
        self.assertEqual(checkin["review_checkin"]["outcome"], "mixed")
        self.assertEqual(completed_loop["prompt"]["state"], "review_complete")
        self.assertEqual(completed_loop["evening_receipt"]["status"], "complete")
        self.assertIsNotNone(activation_after_review["activation"]["first_review_ready_at"])
        self.assertIsNotNone(activation_after_review["activation"]["review_completed_at"])


if __name__ == "__main__":
    unittest.main()
