import json
import unittest
from pathlib import Path

from intentos.beta.extension import chrome_event_to_activity
from intentos.capture.privacy import load_privacy_policy


class BetaExtensionTests(unittest.TestCase):
    def setUp(self):
        self.policy = load_privacy_policy("data/capture/privacy_policy.json")

    def test_manifest_is_metadata_only_mv3_bridge(self):
        manifest = json.loads(Path("extension/chrome/manifest.json").read_text())

        self.assertEqual(manifest["manifest_version"], 3)
        self.assertIn("tabs", manifest["permissions"])
        self.assertIn("http://127.0.0.1:*/*", manifest["host_permissions"])
        self.assertIn("background.js", manifest["background"]["service_worker"])

    def test_fake_chrome_event_becomes_activity_event(self):
        raw = json.loads(Path("data/beta/fake_chrome_events.json").read_text())[0]
        event = chrome_event_to_activity(raw, self.policy)

        self.assertEqual(event.source_app, "Google Chrome")
        self.assertEqual(event.surface, "chat.openai.com")
        self.assertEqual(event.metadata["source"], "chrome_extension_bridge")

    def test_private_fields_are_rejected(self):
        raw = {
            "url": "https://example.com",
            "title": "Example",
            "timestamp": "2026-04-27T09:00:00Z",
            "body": "page body must not cross the bridge",
        }

        with self.assertRaises(ValueError):
            chrome_event_to_activity(raw, self.policy)

    def test_sensitive_urls_are_ignored_before_persistence(self):
        raw = {
            "url": "https://bank.example/login",
            "title": "Banking login",
            "timestamp": "2026-04-27T09:00:00Z",
        }

        self.assertIsNone(chrome_event_to_activity(raw, self.policy))


if __name__ == "__main__":
    unittest.main()
