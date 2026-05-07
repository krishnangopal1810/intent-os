import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from intentos.beta import daily_loop, daily_state, setup_flow, store


class BetaActivationTests(unittest.TestCase):
    def test_daily_loop_records_first_live_state_and_review_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            with store.connect(db) as conn:
                store.init_db(conn)
                setup_flow.mark_milestone(conn, "opened", "2026-01-01T09:00:00Z")
                daily_state.upsert_daily_intent(conn, "2026-04-27", "Ship docs", "LinkedIn feed")
                loop = daily_loop.daily_loop(
                    conn,
                    "2026-04-27",
                    str(db),
                    now=datetime(2026, 4, 27, 18, 0, tzinfo=timezone.utc),
                )
                activation = setup_flow.activation_status(conn)

        self.assertEqual(loop["focus_rescue"]["state"], "evidence_insufficient")
        self.assertEqual(loop["evening_receipt"]["status"], "collecting")
        self.assertIsNotNone(activation["first_live_state_at"])
        self.assertIsNotNone(activation["first_review_ready_at"])
        self.assertEqual(activation["app_opened_at"], "2026-01-01T09:00:00Z")

    def test_preflight_reports_tester_runtime_without_requiring_terminal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "runtime"
            bundle_runtime = root / "IntentOS.app/Contents/Resources/intent-os-runtime"
            bundle_runtime.mkdir(parents=True)
            (bundle_runtime / "Makefile").write_text("verify:\n", encoding="utf-8")
            db = runtime / "beta/intentos.sqlite"
            env = {
                **os.environ,
                "INTENTOS_RUNTIME_DIR": str(runtime),
                "INTENTOS_APP_BUNDLE_PATH": str(root / "IntentOS.app"),
                "INTENTOS_BUNDLED_RUNTIME_PATH": str(bundle_runtime),
                "INTENTOS_BUNDLED_RUNTIME_PRESENT": "1",
            }
            with patch.dict(os.environ, env, clear=True), store.connect(db) as conn:
                store.init_db(conn)
                store.set_status(conn, "service_state", "running")
                payload = setup_flow.preflight_status(conn, str(db))

        self.assertEqual(payload["state"], "ready")
        self.assertFalse(payload["normal_path_requires_terminal"])
        self.assertEqual(payload["checks"]["bundled_runtime_present"]["state"], "ok")
        self.assertEqual(payload["checks"]["local_port_available"]["state"], "ok")


if __name__ == "__main__":
    unittest.main()
