import json
import subprocess
import unittest
from pathlib import Path

from intentos.capture.browser import (
    BrowserCaptureError,
    active_browser_tab,
    browser_application_name,
    normalize_domain,
    parse_browser_tab,
)


class CaptureBrowserTest(unittest.TestCase):
    def test_normalizes_domain(self):
        self.assertEqual(
            normalize_domain("https://www.linkedin.com/feed/"),
            "linkedin.com",
        )

    def test_rejects_non_http_urls(self):
        with self.assertRaisesRegex(ValueError, "http or https"):
            normalize_domain("file:///tmp/example.html")

    def test_parses_browser_tab_fixture(self):
        raw = json.loads(Path("data/capture/fake_browser_tabs.json").read_text())
        tabs = [parse_browser_tab(item, i) for i, item in enumerate(raw)]

        self.assertEqual(tabs[0].browser_name, "Chrome")
        self.assertEqual(tabs[0].domain, "linkedin.com")
        self.assertEqual(tabs[1].domain, "incometax.gov.in")

    def test_parses_live_browser_tab_fixture(self):
        fixture = json.loads(
            Path("data/capture/browser_active_tab_snapshot.json").read_text(
                encoding="utf-8"
            )
        )

        tab = active_browser_tab(
            fixture["app_name"],
            fixture["bundle_id"],
            lambda command: subprocess.CompletedProcess(
                command,
                0,
                stdout=fixture["stdout"],
                stderr="",
            ),
        )

        self.assertIsNotNone(tab)
        self.assertEqual(tab.browser_name, fixture["expected"]["browser_name"])
        self.assertEqual(tab.url, fixture["expected"]["url"])
        self.assertEqual(tab.title, fixture["expected"]["title"])
        self.assertEqual(tab.domain, fixture["expected"]["domain"])
        self.assertEqual(tab.source, fixture["expected"]["source"])

    def test_live_browser_tab_ignores_non_browser_app(self):
        tab = active_browser_tab(
            "Codex",
            "com.openai.codex",
            lambda command: self.fail("non-browser apps should not call osascript"),
        )

        self.assertIsNone(tab)

    def test_live_browser_tab_reports_permission_help(self):
        with self.assertRaisesRegex(BrowserCaptureError, "Automation permission"):
            active_browser_tab(
                "Chrome",
                "com.google.Chrome",
                lambda command: subprocess.CompletedProcess(
                    command,
                    1,
                    stdout="",
                    stderr="Not authorized",
                ),
            )

    def test_live_browser_tab_ignores_internal_browser_urls(self):
        tab = active_browser_tab(
            "Chrome",
            "com.google.Chrome",
            lambda command: subprocess.CompletedProcess(
                command,
                0,
                stdout="Settings\nchrome://settings\n",
                stderr="",
            ),
        )

        self.assertIsNone(tab)

    def test_maps_browser_bundle_ids(self):
        self.assertEqual(
            browser_application_name("Unknown", "com.apple.Safari"),
            "Safari",
        )


if __name__ == "__main__":
    unittest.main()
