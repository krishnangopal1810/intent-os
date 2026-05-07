import re
import unittest
from pathlib import Path


SWIFT_PATH = Path("macos/IntentOSBeta/IntentOSBeta.swift")
BETA_STOP_PATH = Path("scripts/harness/beta-stop.sh")


class BetaMenuAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.swift = SWIFT_PATH.read_text(encoding="utf-8")
        cls.beta_stop = BETA_STOP_PATH.read_text(encoding="utf-8")

    def test_menu_items_are_wired_to_expected_actions(self):
        items = re.findall(r'menu\.addItem\(item\("([^"]+)", #selector\(([^)]+)\)\)\)', self.swift)

        self.assertEqual(
            items,
            [
                ("Open Dashboard", "openDashboard"),
                ("Set Today's Intent", "setTodaysIntent"),
                ("Open Evening Review", "openEveningReview"),
                ("Open Next Block", "openNextBlock"),
                ("Open Weekly Patterns", "openWeeklyPatterns"),
                ("Start Beta", "startBeta"),
                ("Restart Beta", "restartBeta"),
                ("Stop Beta", "stopBeta"),
                ("Run Preflight", "runPreflight"),
                ("Run Permission Check", "runPermissionCheck"),
                ("Restart Onboarding", "restartOnboarding"),
                ("Copy Setup Report", "copySetupReport"),
                ("Open Accessibility Settings", "openAccessibilitySettings"),
                ("Open Automation Settings", "openAutomationSettings"),
                ("Open Chrome Extension Setup", "openChromeSetup"),
                ("Pause 15 min", "pause15"),
                ("Pause 1 hour", "pauseHour"),
                ("Pause until tomorrow", "pauseTomorrow"),
                ("Resume", "resume"),
                ("Delete Local Data", "deleteLocalData"),
                ("Open Diagnostics", "openDiagnostics"),
                ("Quit", "quit"),
            ],
        )

    def test_runtime_actions_have_stale_state_guards(self):
        self.assertIn("openRecordedDashboard()", self.swift)
        self.assertIn("isBetaRecordedRunning()", self.swift)
        self.assertIn('runtimeRoot().appendingPathComponent("beta/app.env")', self.swift)
        self.assertIn("retryPostAfterStart(", self.swift)
        self.assertIn("retryGetAfterStart(", self.swift)
        self.assertIn("error != nil && retryAfterStart", self.swift)
        self.assertIn("forceRestart: true", self.swift)
        self.assertIn("/api/setup-report", self.swift)
        self.assertIn("Run Preflight", self.swift)
        self.assertIn("INTENTOS_BUNDLED_RUNTIME_PRESENT", self.swift)
        self.assertIn("INTENTOS_APP_BUNDLE_PATH", self.swift)
        self.assertIn('"action":"reset"', self.swift)
        self.assertIn("scriptPath(for: target)", self.swift)
        self.assertIn("INTENTOS_RUNTIME_DIR", self.swift)
        self.assertIn("intent-os-runtime", self.swift)
        self.assertIn("/api/daily-loop", self.swift)
        self.assertIn("/api/daily-intent", self.swift)
        self.assertIn("/api/review-checkin", self.swift)
        self.assertIn("/api/weekly-patterns", self.swift)
        self.assertIn("Intent Due", self.swift)
        self.assertIn("Review Ready", self.swift)
        self.assertIn("Recovery Available", self.swift)
        self.assertIn("Focus Protected", self.swift)
        self.assertIn("Need Evidence", self.swift)
        self.assertIn("Focus Holding", self.swift)
        self.assertIn("Avoid Leaking", self.swift)
        self.assertIn("Needs Correction", self.swift)
        self.assertIn("Paused", self.swift)
        self.assertIn("Running", self.swift)
        self.assertIn('openDashboardAnchor("decision-title"', self.swift)
        self.assertIn('openDashboardAnchor("weekly-patterns-title"', self.swift)
        self.assertLess(
            self.swift.index('let status = json["status"] as? [String: Any] ?? json'),
            self.swift.index('if let prompt = json["prompt"] as? [String: Any]'),
        )

    def test_start_restart_stop_and_quit_have_distinct_behaviors(self):
        self.assertIn("startBetaIfNeeded(openWhenReady: false)", self.swift)
        self.assertIn("startBetaIfNeeded(openWhenReady: true, forceRestart: true)", self.swift)
        self.assertIn('runMake("beta-stop") { _ in', self.swift)
        self.assertIn("NSApp.terminate(nil)", self.swift)

    def test_privacy_controls_are_safe_and_calendar_accurate(self):
        self.assertIn("confirmDeleteLocalData()", self.swift)
        self.assertIn('"Delete Local Data?"', self.swift)
        self.assertIn('post("/api/delete-local-data"', self.swift)
        self.assertIn("minutesUntilTomorrow()", self.swift)
        self.assertIn("calendar.startOfDay(for: now)", self.swift)
        self.assertNotIn('#"{"minutes":1440}"#', self.swift)

    def test_beta_stop_respects_isolated_runtime_dir(self):
        self.assertIn('RUNTIME_DIR="${INTENTOS_RUNTIME_DIR:-.harness/runtime}"', self.beta_stop)
        self.assertIn('BETA_DIR="$RUNTIME_DIR/beta"', self.beta_stop)


if __name__ == "__main__":
    unittest.main()
