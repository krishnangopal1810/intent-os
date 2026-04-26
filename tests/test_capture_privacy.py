import unittest

from intentos.capture.privacy import (
    PrivacyPolicy,
    bound_text,
    load_privacy_policy,
    redact_metadata,
    should_exclude,
)


class CapturePrivacyTest(unittest.TestCase):
    def test_policy_excludes_sensitive_domain(self):
        policy = PrivacyPolicy(excluded_domains=("bank.example",))

        self.assertTrue(should_exclude({"domain": "secure.bank.example"}, policy))

    def test_policy_excludes_private_browsing(self):
        policy = PrivacyPolicy(private_browsing_terms=("private browsing",))

        self.assertTrue(
            should_exclude({"window_title": "Private Browsing - Search"}, policy)
        )
        self.assertTrue(
            should_exclude(
                {
                    "window_title": "Generic Browser",
                    "title": "Private Browsing - Search",
                },
                policy,
            )
        )

    def test_policy_excludes_sensitive_visible_text(self):
        policy = PrivacyPolicy(sensitive_terms=("payment form",))

        self.assertTrue(
            should_exclude(
                {
                    "app_name": "Browser",
                    "window_title": "Generic page",
                    "visible_text_excerpt": "Complete this payment form",
                },
                policy,
            )
        )

    def test_bounds_visible_text_excerpt(self):
        self.assertEqual(bound_text("alpha   beta gamma", 20), "alpha beta gamma")
        self.assertEqual(bound_text("abcdefghijklmnopqrstuvwxyz", 10), "abcdefg...")

    def test_redacts_metadata_text(self):
        policy = PrivacyPolicy(visible_text_limit=12)
        redacted = redact_metadata(
            {"visible_text_excerpt": "one two three four five"},
            policy,
        )

        self.assertEqual(redacted["visible_text_excerpt"], "one two t...")

    def test_loads_policy_fixture(self):
        policy = load_privacy_policy("data/capture/privacy_policy.json")

        self.assertIn("private browsing", policy.private_browsing_terms)
        self.assertEqual(policy.visible_text_limit, 80)


if __name__ == "__main__":
    unittest.main()
