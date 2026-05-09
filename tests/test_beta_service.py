import unittest

from beta_service_harness import BETA_DATE, BetaServiceHarness


class BetaServiceSmokeTests(unittest.TestCase):
    def test_daily_review_smoke_uses_persisted_browser_events(self):
        with BetaServiceHarness() as harness:
            accepted = harness.post_fixture_events()
            report = harness.get(f"/api/daily-review?date={BETA_DATE}")

        self.assertGreaterEqual(len(accepted), 3)
        self.assertGreaterEqual(len(report["items"]), 3)


if __name__ == "__main__":
    unittest.main()
