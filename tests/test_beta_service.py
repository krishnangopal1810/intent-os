import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from intentos.beta import daily_state, store
from intentos.beta.service import ServiceConfig, make_handler

API_TOKEN = "test-token"
TRUSTED_ORIGIN = "http://127.0.0.1:4321"


class BetaServiceTests(unittest.TestCase):
    def test_api_persistence_correction_pause_and_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "beta.sqlite"
            config = ServiceConfig(
                db_path=db,
                privacy_policy_path=Path("data/capture/privacy_policy.json"),
                port=0,
                runtime_dir=Path(tmp),
                permission_mode="fake",
                allow_system_open=False,
                api_token=API_TOKEN,
                allowed_origins=(TRUSTED_ORIGIN,),
            )
            artifacts = Path(tmp) / "artifacts"
            artifacts.mkdir()
            stale_report = artifacts / "beta-daily-review.json"
            stale_report.write_text("{}", encoding="utf-8")
            with store.connect(db) as conn:
                store.init_db(conn)
            server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(config))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                raw = json.loads(Path("data/beta/fake_chrome_events.json").read_text())[0]
                unauthorized_read = get_json_status(f"{base}/api/status", token="wrong")
                unauthorized_write = post_json_status(
                    f"{base}/api/pause",
                    {"minutes": 15},
                    token="wrong",
                )
                blocked_origin = get_json_status(
                    f"{base}/api/status",
                    origin="https://evil.example",
                )
                trusted_headers = options_headers(f"{base}/api/status", TRUSTED_ORIGIN)
                heartbeat = post_json(f"{base}/api/extension-heartbeat", {"version": "test"})
                connected = get_json(f"{base}/api/status")
                accepted = post_json(f"{base}/api/browser-event", raw)
                status = get_json(f"{base}/api/status")
                onboarding = get_json(f"{base}/api/onboarding")
                permission_check = post_json(f"{base}/api/permissions/check", {})
                settings = post_json(f"{base}/api/open-system-settings", {"target": "automation"})
                early_complete = post_json_status(f"{base}/api/onboarding", {"action": "complete"})
                privacy_ack = post_json(f"{base}/api/onboarding", {"action": "acknowledge_privacy"})
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
                future_raw = dict(raw)
                future_raw["timestamp"] = "2026-04-27T09:45:00Z"
                future_raw["url"] = "https://chat.openai.com/c/future-intent-os-beta"
                future_raw["title"] = segment["title"]
                future_accepted = post_json(f"{base}/api/browser-event", future_raw)
                unrelated_future_raw = dict(raw)
                unrelated_future_raw["timestamp"] = "2026-04-27T09:50:00Z"
                unrelated_future_raw["url"] = "https://chat.openai.com/c/unrelated-domain-scope"
                unrelated_future_raw["title"] = "Casual ChatGPT thread"
                unrelated_accepted = post_json(f"{base}/api/browser-event", unrelated_future_raw)
                corrected_future = get_json(f"{base}/api/daily-review?date=2026-04-27")
                intent = post_json(
                    f"{base}/api/daily-intent",
                    {
                        "date": "2026-04-27",
                        "focus_text": "Ship beta loop",
                        "avoid_text": "Feed drift",
                    },
                )
                completed = post_json(f"{base}/api/onboarding", {"action": "complete"})
                setup_report = get_json(f"{base}/api/setup-report")
                loop = get_json(f"{base}/api/daily-loop?date=2026-04-27")
                rescue_key = loop["focus_rescue"]["rescue_key"]
                rescue_shown = post_json(
                    f"{base}/api/focus-rescue-action",
                    {
                        "date": "2026-04-27",
                        "rescue_key": rescue_key,
                        "action": "shown",
                        "evidence_id": loop["focus_rescue"]["primary_evidence"]["evidence_id"],
                    },
                )
                invalid_rescue = post_json_status(
                    f"{base}/api/focus-rescue-action",
                    {
                        "date": "2026-04-27",
                        "rescue_key": rescue_key,
                        "action": "invalid",
                    },
                )
                rescue_pause = post_json(
                    f"{base}/api/focus-rescue-action",
                    {
                        "date": "2026-04-27",
                        "rescue_key": rescue_key,
                        "action": "pause_capture",
                        "note": "Service test pause.",
                    },
                )
                paused_by_rescue = get_json(f"{base}/api/status")
                post_json(f"{base}/api/resume", {})
                weekly = get_json(f"{base}/api/weekly-patterns?week_start=2026-04-27")
                checkin = post_json(
                    f"{base}/api/review-checkin",
                    {
                        "date": "2026-04-27",
                        "outcome": "mixed",
                        "reflection_text": "Loop is visible.",
                        "next_adjustment": "Review before shutdown.",
                    },
                )
                completed_loop = get_json(f"{base}/api/daily-loop?date=2026-04-27")
                activation_after_review = get_json(f"{base}/api/status")
                pause = post_json(f"{base}/api/pause", {"minutes": 15})
                paused = get_json(f"{base}/api/status")
                delete = post_json(f"{base}/api/delete-local-data", {})
                deleted = get_json(f"{base}/api/status")
                weekly_after_delete = get_json(f"{base}/api/weekly-patterns?week_start=2026-04-27")
            finally:
                server.shutdown()
                server.server_close()

        self.assertEqual(unauthorized_read, 403)
        self.assertEqual(unauthorized_write, 403)
        self.assertEqual(blocked_origin, 403)
        self.assertEqual(trusted_headers["Access-Control-Allow-Origin"], TRUSTED_ORIGIN)
        self.assertEqual(heartbeat["status"], "connected")
        self.assertEqual(connected["extension"]["state"], "connected")
        self.assertEqual(accepted["status"], "accepted")
        self.assertEqual(status["row_counts"]["activity_events"], 1)
        self.assertEqual(status["extension"]["state"], "posting_events")
        self.assertFalse(onboarding["onboarding"]["completed"])
        self.assertEqual(permission_check["permissions"]["accessibility"]["state"], "ok")
        self.assertEqual(settings["status"], "validated")
        self.assertIn("browser entry", " ".join(settings["guidance"]["steps"]))
        self.assertEqual(early_complete, 400)
        self.assertTrue(privacy_ack["privacy_acknowledged"])
        self.assertTrue(completed["completed"])
        self.assertEqual(setup_report["setup_report"]["capture_preview"]["state"], "ok")
        self.assertNotIn("window_title", setup_report["setup_report"]["capture_preview"])
        self.assertIn("preflight", setup_report["setup_report"])
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
        self.assertEqual(intent["intent"]["focus_text"], "Ship beta loop")
        self.assertEqual(loop["intent"]["avoid_text"], "Feed drift")
        self.assertEqual(loop["correction_count"], 2)
        self.assertIn("intent_contract", loop)
        self.assertIn("next_block", loop)
        self.assertIn("correction_reward", loop)
        self.assertIn("evening_receipt", loop)
        self.assertEqual(loop["focus_rescue"]["state"], "focus_protected")
        self.assertEqual(rescue_shown["status"], "recorded")
        self.assertEqual(rescue_shown["action"]["action"], "shown")
        self.assertEqual(invalid_rescue, 400)
        self.assertEqual(rescue_pause["pause"]["status"], "paused")
        self.assertTrue(paused_by_rescue["pause"]["paused"])
        self.assertIsNotNone(paused_by_rescue["activation"]["intent_set_at"])
        self.assertIsNotNone(paused_by_rescue["activation"]["first_live_state_at"])
        self.assertIsNotNone(paused_by_rescue["activation"]["first_rescue_state_at"])
        self.assertIsNotNone(paused_by_rescue["activation"]["first_recovery_action_at"])
        self.assertEqual(len(weekly["patterns"]), 3)
        self.assertIn("week", weekly["narrative"].lower())
        self.assertEqual(checkin["review_checkin"]["outcome"], "mixed")
        self.assertEqual(completed_loop["prompt"]["state"], "review_complete")
        self.assertEqual(completed_loop["evening_receipt"]["status"], "complete")
        self.assertIsNotNone(activation_after_review["activation"]["first_review_ready_at"])
        self.assertIsNotNone(activation_after_review["activation"]["review_completed_at"])
        self.assertEqual(pause["status"], "paused")
        self.assertTrue(paused["pause"]["paused"])
        self.assertEqual(delete["status"], "deleted")
        self.assertIn(str(stale_report), delete["cleared_artifacts"])
        self.assertFalse(stale_report.exists())
        self.assertEqual(deleted["row_counts"]["activity_events"], 0)
        self.assertEqual(deleted["service"]["state"], "running")
        self.assertFalse(deleted["pause"]["paused"])
        self.assertIsNone(deleted["last_event_time"])
        self.assertEqual(deleted["extension"]["state"], "never_connected")
        self.assertEqual(deleted["capture_preview"]["state"], "unchecked")
        self.assertIsNone(deleted["capture_preview"]["app_name"])
        self.assertEqual(deleted["permissions"]["accessibility"]["state"], "unchecked")
        self.assertEqual(weekly_after_delete["best_focus_window"]["duration_seconds"], 0)
        with store.connect(db) as conn:
            store.init_db(conn)
            self.assertIsNone(daily_state.daily_intent(conn, "2026-04-27"))
            self.assertIsNone(daily_state.review_checkin(conn, "2026-04-27"))
            self.assertIsNone(daily_state.latest_focus_rescue_action(conn, "2026-04-27", rescue_key))


def get_json(url, token=API_TOKEN):
    with urlopen(auth_request(url, token=token), timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json_status(url, token=API_TOKEN, origin=None):
    try:
        with urlopen(auth_request(url, token=token, origin=origin), timeout=3) as response:
            return response.status
    except HTTPError as exc:
        return exc.code


def options_headers(url, origin):
    request = Request(
        url,
        headers=auth_headers(origin=origin),
        method="OPTIONS",
    )
    with urlopen(request, timeout=3) as response:
        return response.headers


def post_json(url, payload, token=API_TOKEN):
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=auth_headers(token, {"Content-Type": "application/json"}),
        method="POST",
    )
    with urlopen(request, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json_status(url, payload, token=API_TOKEN):
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=auth_headers(token, {"Content-Type": "application/json"}),
        method="POST",
    )
    try:
        with urlopen(request, timeout=3) as response:
            return response.status
    except HTTPError as exc:
        return exc.code


def auth_request(url, token=API_TOKEN, origin=None):
    return Request(url, headers=auth_headers(token, origin=origin))


def auth_headers(token=API_TOKEN, extra=None, origin=None):
    headers = dict(extra or {})
    if token:
        headers["X-IntentOS-Token"] = token
    if origin:
        headers["Origin"] = origin
    return headers


if __name__ == "__main__":
    unittest.main()
