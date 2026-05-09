import json
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

from intentos.beta import store
from intentos.beta.http_client import BetaHttpClient
from intentos.beta.service import ServiceConfig, make_handler


API_TOKEN = "test-token"
TRUSTED_ORIGIN = "http://127.0.0.1:4321"
BETA_DATE = "2026-04-27"


class BetaServiceHarness:
    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.db = self.root / "beta.sqlite"
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir()
        self.stale_report = self.artifacts / "beta-daily-review.json"
        self.stale_report.write_text("{}", encoding="utf-8")
        with store.connect(self.db) as conn:
            store.init_db(conn)
        config = ServiceConfig(
            db_path=self.db,
            privacy_policy_path=Path("data/capture/privacy_policy.json"),
            port=0,
            runtime_dir=self.root,
            permission_mode="fake",
            allow_system_open=False,
            api_token=API_TOKEN,
            allowed_origins=(TRUSTED_ORIGIN,),
        )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(config))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"
        self.client = BetaHttpClient(self.base_url, API_TOKEN)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.server.shutdown()
        self.server.server_close()
        self._tmp.cleanup()

    def get(self, path: str) -> dict:
        return self.client.get_json(path)

    def get_status(
        self,
        path: str,
        *,
        token: str | None = None,
        origin: str | None = None,
    ) -> int:
        return self.client.get_status(path, token=token, origin=origin)

    def post(self, path: str, payload: dict) -> dict:
        return self.client.post_json(path, payload)

    def post_status(self, path: str, payload: dict, *, token: str | None = None) -> int:
        return self.client.post_status(path, payload, token=token)

    def options_headers(self, path: str, origin: str):
        request = Request(
            self.client.url(path),
            headers=self.client.headers(origin=origin),
            method="OPTIONS",
        )
        with urlopen(request, timeout=3) as response:
            return response.headers

    def fixture_event(self, index: int = 0) -> dict:
        events = json.loads(Path("data/beta/fake_chrome_events.json").read_text())
        return events[index]

    def post_fixture_events(self) -> list[dict]:
        accepted = []
        for event in json.loads(Path("data/beta/fake_chrome_events.json").read_text()):
            accepted.append(self.post("/api/browser-event", event))
        return accepted

    def complete_setup(self) -> None:
        self.post("/api/permissions/check", {})
        self.post("/api/onboarding", {"action": "acknowledge_privacy"})
        self.post(
            "/api/daily-intent",
            {
                "date": BETA_DATE,
                "focus_text": "Ship beta loop",
                "avoid_text": "Feed drift",
            },
        )
        self.post("/api/onboarding", {"action": "complete"})
