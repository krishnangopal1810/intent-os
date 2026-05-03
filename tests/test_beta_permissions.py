import tempfile
import unittest
from pathlib import Path

from intentos.beta import permissions, state, store


class BetaPermissionTests(unittest.TestCase):
    def test_fake_permission_check_updates_serialized_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            with store.connect(db) as conn:
                store.init_db(conn)
                payload = permissions.run_check(conn, "fake", str(db))

            self.assertEqual(payload["permissions"]["accessibility"]["state"], "ok")
            self.assertEqual(payload["permissions"]["browser_automation"]["state"], "ok")
            self.assertEqual(payload["readiness"]["state"], "setup_needed")

    def test_onboarding_state_is_shared_through_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            with store.connect(db) as conn:
                store.init_db(conn)
                current = state.onboarding(conn)
                completed = state.update_onboarding(conn, "complete")

            self.assertFalse(current["completed"])
            self.assertTrue(completed["completed"])
            self.assertTrue(completed["privacy_acknowledged"])

    def test_open_settings_validates_allowed_targets_without_side_effect(self):
        result = permissions.open_settings_target(
            "accessibility", Path("/tmp/intent-os-runtime"), allow_open=False
        )
        self.assertEqual(result["status"], "validated")
        self.assertEqual(result["target"], "accessibility")
        with self.assertRaises(ValueError):
            permissions.open_settings_target("unknown", Path("/tmp"), allow_open=False)

    def test_beta_harness_matches_chrome_bridge_default_port(self):
        beta_dev = Path("scripts/harness/beta-dev.sh").read_text(encoding="utf-8")
        bridge = Path("extension/chrome/background.js").read_text(encoding="utf-8")

        self.assertIn("INTENTOS_BETA_SERVICE_PORT:-58917", beta_dev)
        self.assertIn("INTENTOS_BETA_FAKE_BRIDGE:-0", beta_dev)
        self.assertIn("DEFAULT_PORT = 58917", bridge)


if __name__ == "__main__":
    unittest.main()
