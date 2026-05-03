import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

from intentos.beta import store
from intentos.beta.service import ServiceConfig, make_handler


class BetaServiceTests(unittest.TestCase):
    def test_api_persistence_correction_pause_and_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            config = ServiceConfig(
                db_path=db,
                privacy_policy_path=Path("data/capture/privacy_policy.json"),
                port=0,
                permission_mode="fake",
                allow_system_open=False,
            )
            with store.connect(db) as conn:
                store.init_db(conn)
            server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(config))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                raw = json.loads(Path("data/beta/fake_chrome_events.json").read_text())[0]
                heartbeat = post_json(f"{base}/api/extension-heartbeat", {"version": "test"})
                connected = get_json(f"{base}/api/status")
                accepted = post_json(f"{base}/api/browser-event", raw)
                status = get_json(f"{base}/api/status")
                onboarding = get_json(f"{base}/api/onboarding")
                permission_check = post_json(f"{base}/api/permissions/check", {})
                settings = post_json(f"{base}/api/open-system-settings", {"target": "automation"})
                completed = post_json(f"{base}/api/onboarding", {"action": "complete"})
                report = get_json(f"{base}/api/daily-review?date=2026-04-27")
                segment = report["items"][0]
                correction = post_json(
                    f"{base}/api/corrections",
                    {
                        "segment": segment,
                        "corrected_label": "learning",
                        "apply_to_future": True,
                    },
                )
                corrected = get_json(f"{base}/api/daily-review?date=2026-04-27")
                pause = post_json(f"{base}/api/pause", {"minutes": 15})
                paused = get_json(f"{base}/api/status")
                delete = post_json(f"{base}/api/delete-local-data", {})
                deleted = get_json(f"{base}/api/status")
            finally:
                server.shutdown()
                server.server_close()

        self.assertEqual(heartbeat["status"], "connected")
        self.assertEqual(connected["extension"]["state"], "connected")
        self.assertEqual(accepted["status"], "accepted")
        self.assertEqual(status["row_counts"]["activity_events"], 1)
        self.assertEqual(status["extension"]["state"], "posting_events")
        self.assertFalse(onboarding["onboarding"]["completed"])
        self.assertEqual(permission_check["permissions"]["accessibility"]["state"], "ok")
        self.assertEqual(settings["status"], "validated")
        self.assertTrue(completed["completed"])
        self.assertEqual(correction["status"], "corrected")
        self.assertEqual(corrected["items"][0]["label"], "learning")
        self.assertEqual(pause["status"], "paused")
        self.assertTrue(paused["pause"]["paused"])
        self.assertEqual(delete["status"], "deleted")
        self.assertEqual(deleted["row_counts"]["activity_events"], 0)


def get_json(url):
    with urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url, payload):
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
