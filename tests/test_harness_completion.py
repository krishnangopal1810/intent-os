import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from intentos.activity import ActivityEvent
from intentos.beta import recorder, review, store


ROOT = Path(__file__).resolve().parents[1]


class HarnessCompletionTests(unittest.TestCase):
    def test_new_feature_scaffold_generates_decision_complete_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                **os.environ,
                "INTENTOS_PLAN_DIR": tmp,
                "INTENTOS_PLAN_DATE": "2026-05-03",
            }
            result = subprocess.run(
                ["bash", "scripts/harness/new-feature.sh", "calendar-context", "data-source"],
                cwd=ROOT,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            path = Path(result.stdout.strip())
            text = path.read_text(encoding="utf-8")

        self.assertIn("## Acceptance Criteria", text)
        self.assertIn("## Harness Impact", text)
        self.assertIn("Runtime commands and artifacts", text)
        self.assertIn("Fixtures or fakes", text)
        self.assertNotIn("TBD", text)

    def test_new_feature_rejects_unknown_class(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "INTENTOS_PLAN_DIR": tmp}
            result = subprocess.run(
                ["bash", "scripts/harness/new-feature.sh", "bad-feature", "unknown"],
                cwd=ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown class", result.stderr)

    def test_adapter_fixture_check_writes_manifest_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/harness/adapter-fixture-check.py",
                    "--runtime-dir",
                    tmp,
                ],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            output = Path(tmp) / "artifacts/adapter-fixture-check.json"
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertIn("adapter-fixture-check: ok", result.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertGreaterEqual(len(payload["adapters"]), 4)

    def test_feedback_fixture_candidates_hash_raw_titles_and_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            output = Path(tmp) / "candidates.json"
            event = ActivityEvent(
                "Google Chrome",
                "linkedin.com",
                "Private user title should not export",
                "2026-04-27T10:00:00Z",
                300,
                "https://www.linkedin.com/feed/private-user",
                {"source": "test", "domain": "linkedin.com"},
            )
            with store.connect(db) as conn:
                store.init_db(conn)
                recorder.record_event(conn, event)
                segment = review.daily_review(conn, "2026-04-27", str(db))["items"][0]
                store.add_correction(conn, segment, "learning", apply_to_future=True)

            subprocess.run(
                [
                    sys.executable,
                    "scripts/harness/feedback-fixture-candidates.py",
                    "--db",
                    str(db),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            text = output.read_text(encoding="utf-8")
            payload = json.loads(text)

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["item_count"], 1)
        self.assertIn("title_pattern_hash", payload["items"][0])
        self.assertNotIn("Private user title", text)
        self.assertNotIn("private-user", text)

    def test_diagnose_json_writes_stable_artifact_without_live_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, "scripts/harness/diagnose-json.py"],
                cwd=ROOT,
                env={**os.environ, "INTENTOS_RUNTIME_DIR": tmp},
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            output = Path(tmp) / "artifacts/diagnose.json"
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertIn("diagnose-json: wrote", result.stdout)
        self.assertIn(payload["status"], {"ok", "warning"})
        self.assertIn("recommended_next_commands", payload)

    def test_onboarding_package_and_cohort_checks_write_artifacts(self):
        for command, output in [
            ("package-onboarding-check.py", ".harness/runtime/artifacts/package-onboarding-check.json"),
            ("cohort-evidence-check.py", ".harness/runtime/artifacts/cohort-evidence-check.json"),
        ]:
            result = subprocess.run(
                [sys.executable, f"scripts/harness/{command}"],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            payload = json.loads(Path(output).read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "ok")
            self.assertIn(": ok", result.stdout)
        package_payload = json.loads(
            Path(".harness/runtime/artifacts/package-onboarding-check.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            package_payload["checked_menu_app"],
            "macos/IntentOSBeta/IntentOSBeta.swift",
        )

    def test_package_check_rejects_stale_dashboard_menu_regression(self):
        module = self.load_harness_script(
            "package_onboarding_check",
            "scripts/harness/package-onboarding-check.py",
        )
        stale_menu_source = """
        menu.addItem(item("Open Dashboard", #selector(openDashboard)))
        private func openDashboard() {
            if !openRecordedDashboard() {
                startBetaIfNeeded(openWhenReady: true)
            }
        }
        private func isBetaRecordedRunning() -> Bool {
            envValue("INTENTOS_BETA_STATUS") == "running"
        }
        private func openRecordedDashboard(anchor: String? = nil) -> Bool {
            NSWorkspace.shared.open(dashboard)
            return true
        }
        """
        failures = []
        module.check_menu_app_stale_dashboard_guard(stale_menu_source, failures)
        message = "\n".join(failures)

        self.assertIn("INTENTOS_BETA_SERVICE_PID", message)
        self.assertIn("INTENTOS_BETA_UI_PID", message)
        self.assertIn("kill(pid, 0)", message)
        self.assertIn("must not report dashboard opened", message)

    def test_cohort_evidence_check_enforces_success_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "cohort-evidence.json"
            evidence.write_text(
                json.dumps(
                    {
                        "testers": [
                            self.cohort_tester(7, 4, "recovery_available", True),
                            self.cohort_tester(7, 5, "focus_protected", True),
                            self.cohort_tester(7, 4, "avoid_leaking", False),
                            self.cohort_tester(3, 5, "evidence_insufficient", False),
                            self.cohort_tester(3, 6, "focus_protected", False),
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/harness/cohort-evidence-check.py",
                    "--evidence",
                    str(evidence),
                ],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            payload = json.loads(
                Path(".harness/runtime/artifacts/cohort-evidence-check.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertIn("cohort-evidence-check: ok", result.stdout)
        self.assertEqual(payload["metrics"]["three_day_testers"], 5)
        self.assertEqual(payload["metrics"]["seven_day_testers"], 3)
        self.assertEqual(payload["metrics"]["would_miss_yes"], 2)
        self.assertTrue(payload["target_status"]["median_setup_minutes"]["passed"])

    def test_cohort_evidence_check_fails_below_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "cohort-evidence.json"
            evidence.write_text(
                json.dumps(
                    {
                        "testers": [
                            self.cohort_tester(
                                1,
                                12,
                                "dashboard_viewed",
                                False,
                            )
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/harness/cohort-evidence-check.py",
                    "--evidence",
                    str(evidence),
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("three_day_testers below target", result.stderr)
        self.assertIn("median_setup_minutes above target", result.stderr)
        self.assertIn("first_live_state", result.stderr)

    @staticmethod
    def cohort_tester(
        days_completed: int,
        setup_minutes: int,
        first_live_state: str,
        would_miss_next_week: bool,
    ) -> dict:
        return {
            "days_completed": days_completed,
            "setup_minutes": setup_minutes,
            "first_captured_app_or_window": "IntentOS Review Board",
            "first_live_state": first_live_state,
            "evening_review_completed": days_completed >= 1,
            "correction_themes": [],
            "would_miss_next_week": would_miss_next_week,
            "repeated_feedback_mapped_to": ["quality_note"],
        }

    @staticmethod
    def load_harness_script(name: str, relative_path: str):
        spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not load {relative_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


if __name__ == "__main__":
    unittest.main()
