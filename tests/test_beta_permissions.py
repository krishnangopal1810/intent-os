import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from intentos.beta import permissions, setup_flow, state, store


class BetaPermissionTests(unittest.TestCase):
    def test_fake_permission_check_updates_serialized_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            with store.connect(db) as conn:
                store.init_db(conn)
                payload = permissions.run_check(conn, "fake", str(db))

            self.assertEqual(payload["permissions"]["accessibility"]["state"], "ok")
            self.assertEqual(payload["permissions"]["browser_automation"]["state"], "ok")
            self.assertEqual(payload["readiness"]["state"], "ready")

    def test_fake_permission_scenarios_cover_blocked_and_stale_states(self):
        scenarios = {
            "accessibility_blocked": ("blocked", "unchecked", "running", "never_connected", False, "setup_needed"),
            "automation_blocked": ("ok", "blocked", "running", "never_connected", False, "ready"),
            "chrome_bridge_missing": ("ok", "not_applicable", "running", "never_connected", False, "ready"),
            "recorder_stale": ("ok", "ok", "stale", "connected", False, "setup_needed"),
            "paused_capture": ("ok", "ok", "running", "connected", True, "setup_needed"),
            "setup_needed": ("needs_action", "unchecked", "not_started", "never_connected", False, "setup_needed"),
            "fresh_install": ("needs_action", "unchecked", "not_started", "never_connected", False, "setup_needed"),
            "capture_preview_blocked": ("ok", "unchecked", "running", "never_connected", False, "setup_needed"),
            "browser_detail_skipped": ("ok", "not_applicable", "running", "never_connected", False, "ready"),
            "browser_detail_granted": ("ok", "ok", "running", "connected", False, "ready"),
            "duplicate_permission_identity": ("blocked", "unchecked", "running", "never_connected", False, "setup_needed"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            for scenario, expected in scenarios.items():
                db = Path(tmp) / f"{scenario}.sqlite"
                with store.connect(db) as conn:
                    store.init_db(conn)
                    payload = permissions.apply_fake_scenario(conn, scenario, str(db))
                actual = (
                    payload["permissions"]["accessibility"]["state"],
                    payload["permissions"]["browser_automation"]["state"],
                    payload["native_recorder"]["state"],
                    payload["extension"]["state"],
                    payload["pause"]["paused"],
                    payload["readiness"]["state"],
                )
                self.assertEqual(actual, expected, scenario)

    def test_onboarding_state_is_shared_through_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            with store.connect(db) as conn:
                store.init_db(conn)
                current = state.onboarding(conn)
                with self.assertRaisesRegex(ValueError, "privacy acknowledgment"):
                    state.update_onboarding(conn, "complete")
                state.update_onboarding(conn, "acknowledge_privacy")
                permissions.apply_fake_scenario(conn, "capture_preview_success", str(db))
                store.set_status(conn, "activation_intent_set_at", store.utc_now())
                completed = state.update_onboarding(conn, "complete")

            self.assertFalse(current["completed"])
            self.assertTrue(completed["completed"])
            self.assertTrue(completed["privacy_acknowledged"])

    def test_reset_onboarding_allows_milestones_to_be_recorded_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            with store.connect(db) as conn:
                store.init_db(conn)
                setup_flow.mark_milestone(conn, "opened", "2026-01-01T00:00:00Z")
                setup_flow.mark_milestone(conn, "intent_set", "2026-01-01T00:10:00Z")
                state.update_onboarding(conn, "reset")
                setup_flow.mark_milestone(conn, "opened", "2026-01-02T00:00:00Z")
                setup_flow.mark_milestone(conn, "intent_set", "2026-01-02T00:10:00Z")
                activation = setup_flow.activation_status(conn)

            self.assertEqual(activation["opened_at"], "2026-01-02T00:00:00Z")
            self.assertEqual(activation["intent_set_at"], "2026-01-02T00:10:00Z")

    def test_open_settings_validates_allowed_targets_without_side_effect(self):
        result = permissions.open_settings_target(
            "accessibility", Path("/tmp/intent-os-runtime"), allow_open=False
        )
        self.assertEqual(result["status"], "validated")
        self.assertEqual(result["target"], "accessibility")
        self.assertEqual(result["guidance"]["title"], "Accessibility Settings")
        self.assertIn("enable IntentOS", " ".join(result["guidance"]["steps"]))
        with self.assertRaises(ValueError):
            permissions.open_settings_target("unknown", Path("/tmp"), allow_open=False)

    def test_capture_preview_and_setup_report_are_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            with store.connect(db) as conn:
                store.init_db(conn)
                payload = permissions.apply_fake_scenario(conn, "browser_detail_granted", str(db))

            self.assertEqual(payload["capture_preview"]["state"], "ok")
            self.assertEqual(payload["capture_preview"]["app_name"], "IntentOS")
            self.assertEqual(payload["setup"]["browser_detail"]["state"], "enabled")
            self.assertEqual(payload["app_identity"]["bundle_id"], "local.intentos.trusted")

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
