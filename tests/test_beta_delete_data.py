import unittest

from intentos.beta import daily_state, store
from beta_service_harness import BETA_DATE, BetaServiceHarness


class BetaDeleteDataTests(unittest.TestCase):
    def test_delete_local_data_scrubs_activity_state_but_keeps_service_running(self):
        with BetaServiceHarness() as harness:
            harness.post_fixture_events()
            harness.complete_setup()
            loop = harness.get(f"/api/daily-loop?date={BETA_DATE}")
            rescue_key = loop["focus_rescue"]["rescue_key"]
            rescue_pause = harness.post(
                "/api/focus-rescue-action",
                {
                    "date": BETA_DATE,
                    "rescue_key": rescue_key,
                    "action": "pause_capture",
                    "note": "Service test pause.",
                },
            )
            paused_by_rescue = harness.get("/api/status")
            harness.post("/api/resume", {})
            pause = harness.post("/api/pause", {"minutes": 15})
            paused = harness.get("/api/status")
            delete = harness.post("/api/delete-local-data", {})
            deleted = harness.get("/api/status")
            weekly_after_delete = harness.get(f"/api/weekly-patterns?week_start={BETA_DATE}")
            db = harness.db
            stale_report = harness.stale_report

            with store.connect(db) as conn:
                store.init_db(conn)
                intent_after_delete = daily_state.daily_intent(conn, BETA_DATE)
                checkin_after_delete = daily_state.review_checkin(conn, BETA_DATE)
                rescue_after_delete = daily_state.latest_focus_rescue_action(
                    conn,
                    BETA_DATE,
                    rescue_key,
                )

        self.assertEqual(rescue_pause["pause"]["status"], "paused")
        self.assertTrue(paused_by_rescue["pause"]["paused"])
        self.assertIsNotNone(paused_by_rescue["activation"]["intent_set_at"])
        self.assertIsNotNone(paused_by_rescue["activation"]["first_live_state_at"])
        self.assertIsNotNone(paused_by_rescue["activation"]["first_rescue_state_at"])
        self.assertIsNotNone(paused_by_rescue["activation"]["first_recovery_action_at"])
        self.assertEqual(pause["status"], "paused")
        self.assertTrue(paused["pause"]["paused"])
        self.assertEqual(delete["status"], "deleted")
        self.assertIn(str(stale_report), delete["cleared_artifacts"])
        self.assertFalse(stale_report.exists())
        self.assertEqual(deleted["row_counts"]["activity_events"], 0)
        self.assertEqual(deleted["service"]["state"], "running")
        self.assertFalse(deleted["pause"]["paused"])
        self.assertIsNone(deleted["last_event_time"])
        self.assertEqual(deleted["extension"]["state"], "never_connected")
        self.assertEqual(deleted["capture_preview"]["state"], "unchecked")
        self.assertIsNone(deleted["capture_preview"]["app_name"])
        self.assertEqual(deleted["permissions"]["accessibility"]["state"], "unchecked")
        self.assertEqual(weekly_after_delete["best_focus_window"]["duration_seconds"], 0)
        self.assertIsNone(intent_after_delete)
        self.assertIsNone(checkin_after_delete)
        self.assertIsNone(rescue_after_delete)


if __name__ == "__main__":
    unittest.main()
