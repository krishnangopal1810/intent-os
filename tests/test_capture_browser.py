import json
import unittest
from pathlib import Path

from intentos.capture.browser import normalize_domain, parse_browser_tab


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


if __name__ == "__main__":
    unittest.main()
