import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
        self.assertEqual(result["guidance"]["title"], "Accessibility Settings")
        self.assertIn("enable IntentOSBeta", " ".join(result["guidance"]["steps"]))
        with self.assertRaises(ValueError):
            permissions.open_settings_target("unknown", Path("/tmp"), allow_open=False)

    def test_chrome_extension_guidance_points_to_unpacked_extension(self):
        result = permissions.open_settings_target(
            "chrome_extensions", Path("/tmp/intent-os-runtime"), allow_open=False
        )

        self.assertTrue(result["guidance"]["optional"])
        self.assertIn("Load unpacked", " ".join(result["guidance"]["steps"]))
        self.assertIn("extension/chrome", " ".join(result["guidance"]["steps"]))

    def test_browser_permission_check_explains_untested_non_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            snapshot = permissions.macos.MacOSAppSnapshot(
                app_name="iTerm2",
                bundle_id="com.googlecode.iterm2",
                process_id=123,
                window_title="shell",
            )
            with store.connect(db) as conn:
                store.init_db(conn)
                permissions.check_browser_automation(conn, snapshot)
                status = store.status(conn, str(db))

        browser_permission = status["permissions"]["browser_automation"]
        self.assertEqual(browser_permission["state"], "not_applicable")
        self.assertIn("iTerm2 is frontmost", browser_permission["detail"])

    def test_browser_permission_check_explains_visible_browser_without_tab(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            snapshot = permissions.macos.MacOSAppSnapshot(
                app_name="Google Chrome",
                bundle_id="com.google.chrome",
                process_id=123,
                window_title="New Tab",
            )
            with store.connect(db) as conn, patch(
                "intentos.capture.browser.active_browser_tab",
                return_value=None,
            ):
                store.init_db(conn)
                permissions.check_browser_automation(conn, snapshot)
                status = store.status(conn, str(db))

        browser_permission = status["permissions"]["browser_automation"]
        self.assertEqual(browser_permission["state"], "not_applicable")
        self.assertIn("Google Chrome is frontmost", browser_permission["detail"])

    def test_beta_harness_matches_chrome_bridge_default_port(self):
        beta_dev = Path("scripts/harness/beta-dev.sh").read_text(encoding="utf-8")
        bridge = Path("extension/chrome/background.js").read_text(encoding="utf-8")

        self.assertIn("INTENTOS_BETA_SERVICE_PORT:-58917", beta_dev)
        self.assertIn("INTENTOS_BETA_FAKE_BRIDGE:-0", beta_dev)
        self.assertIn("DEFAULT_PORT = 58917", bridge)


if __name__ == "__main__":
    unittest.main()
