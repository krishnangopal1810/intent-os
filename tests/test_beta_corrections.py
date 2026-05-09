import unittest

from beta_service_harness import BETA_DATE, BetaServiceHarness


class BetaCorrectionTests(unittest.TestCase):
    def test_apply_to_future_matches_specific_future_segment_only(self):
        with BetaServiceHarness() as harness:
            raw = harness.fixture_event()
            accepted = harness.post("/api/browser-event", raw)
            report = harness.get(f"/api/daily-review?date={BETA_DATE}")
            segment = report["items"][0]
            correction = harness.post(
                "/api/corrections",
                {
                    "segment": segment,
                    "corrected_label": "learning",
                    "apply_to_future": True,
                },
            )
            corrected = harness.get(f"/api/daily-review?date={BETA_DATE}")
            future_raw = dict(raw)
            future_raw["timestamp"] = "2026-04-27T09:45:00Z"
            future_raw["url"] = "https://chat.openai.com/c/future-intent-os-beta"
            future_raw["title"] = segment["title"]
            future_accepted = harness.post("/api/browser-event", future_raw)
            unrelated_future_raw = dict(raw)
            unrelated_future_raw["timestamp"] = "2026-04-27T09:50:00Z"
            unrelated_future_raw["url"] = "https://chat.openai.com/c/unrelated-domain-scope"
            unrelated_future_raw["title"] = "Casual ChatGPT thread"
            unrelated_accepted = harness.post("/api/browser-event", unrelated_future_raw)
            corrected_future = harness.get(f"/api/daily-review?date={BETA_DATE}")

        self.assertEqual(accepted["status"], "accepted")
        self.assertEqual(correction["status"], "corrected")
        self.assertEqual(corrected["items"][0]["label"], "learning")
        self.assertEqual(future_accepted["status"], "accepted")
        future_item = next(
            item for item in corrected_future["items"]
            if (item.get("url") or "").endswith("/future-intent-os-beta")
        )
        self.assertEqual(future_item["label"], "learning")
        self.assertEqual(future_item["corrected_label"], "learning")
        self.assertEqual(unrelated_accepted["status"], "accepted")
        unrelated_item = next(
            item for item in corrected_future["items"]
            if (item.get("url") or "").endswith("/unrelated-domain-scope")
        )
        self.assertNotEqual(unrelated_item["label"], "learning")
        self.assertNotEqual(unrelated_item.get("corrected_label"), "learning")


if __name__ == "__main__":
    unittest.main()
