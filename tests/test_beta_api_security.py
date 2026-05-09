import unittest

from beta_service_harness import BetaServiceHarness, TRUSTED_ORIGIN


class BetaApiSecurityTests(unittest.TestCase):
    def test_rejects_unauthorized_reads_writes_and_origins(self):
        with BetaServiceHarness() as harness:
            unauthorized_read = harness.get_status("/api/status", token="wrong")
            unauthorized_write = harness.post_status(
                "/api/pause",
                {"minutes": 15},
                token="wrong",
            )
            blocked_origin = harness.get_status(
                "/api/status",
                origin="https://evil.example",
            )
            trusted_headers = harness.options_headers("/api/status", TRUSTED_ORIGIN)

        self.assertEqual(unauthorized_read, 403)
        self.assertEqual(unauthorized_write, 403)
        self.assertEqual(blocked_origin, 403)
        self.assertEqual(trusted_headers["Access-Control-Allow-Origin"], TRUSTED_ORIGIN)

    def test_extension_heartbeat_and_event_post_update_status(self):
        with BetaServiceHarness() as harness:
            heartbeat = harness.post("/api/extension-heartbeat", {"version": "test"})
            connected = harness.get("/api/status")
            accepted = harness.post("/api/browser-event", harness.fixture_event())
            status = harness.get("/api/status")

        self.assertEqual(heartbeat["status"], "connected")
        self.assertEqual(connected["extension"]["state"], "connected")
        self.assertEqual(accepted["status"], "accepted")
        self.assertEqual(status["row_counts"]["activity_events"], 1)
        self.assertEqual(status["extension"]["state"], "posting_events")


if __name__ == "__main__":
    unittest.main()
