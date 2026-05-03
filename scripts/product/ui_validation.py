#!/usr/bin/env python3
"""Validate the local UI shell through HTTP, DOM, and visual evidence."""

from __future__ import annotations

import argparse
import json
import os
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.request import urlopen

from png_validation import assert_useful_png


ROOT = Path(__file__).resolve().parents[2]


class Element:
    def __init__(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tag = tag
        self.attrs = dict(attrs)
        self.children: list[Element] = []
        self.text_parts: list[str] = []

    def text(self) -> str:
        values = list(self.text_parts)
        for child in self.children:
            values.append(child.text())
        return " ".join(" ".join(values).split())

    def all(self) -> list["Element"]:
        values = [self]
        for child in self.children:
            values.extend(child.all())
        return values


class TreeBuilder(HTMLParser):
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta"}

    def __init__(self) -> None:
        super().__init__()
        self.root = Element("document", [])
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        element = Element(tag, attrs)
        self.stack[-1].children.append(element)
        if tag not in self.VOID_TAGS:
            self.stack.append(element)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.stack[-1].text_parts.append(data.strip())


def parse_html(html: str) -> Element:
    parser = TreeBuilder()
    parser.feed(html)
    return parser.root


def has_attr(element: Element, name: str, value: str | None = None) -> bool:
    if name not in element.attrs:
        return False
    return value is None or element.attrs.get(name) == value


def elements_with(root: Element, *, tag: str | None = None, attr: str | None = None) -> list[Element]:
    return [
        element
        for element in root.all()
        if (tag is None or element.tag == tag) and (attr is None or attr in element.attrs)
    ]


def assert_true(condition: object, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def fetch(base: str, path: str) -> str:
    last_error: Exception | None = None
    for _ in range(30):
        try:
            with urlopen(base + path, timeout=1) as response:
                return response.read().decode("utf-8")
        except Exception as exc:
            last_error = exc
            time.sleep(0.1)
    raise RuntimeError(f"failed to fetch {path}: {last_error}")

def validate_static_dom(html: str) -> dict[str, object]:
    root = parse_html(html)
    page_text = root.text()
    required_text = ["IntentOS", "Activity", "Action Queue", "Capture Replay"]
    for text in required_text:
        assert_true(text in page_text, f"missing UI text: {text}")

    assert_true(elements_with(root, tag="main", attr="data-ui-root"), "missing data-ui-root")
    report_sections = [
        element
        for element in elements_with(root, tag="section")
        if has_attr(element, "aria-label", "Behavior reports")
    ]
    assert_true(report_sections, "missing Behavior reports region")
    for attr in [
        "data-status",
        "data-primary-narrative",
        "data-stats",
        "data-activity-source",
        "data-activity-bars",
        "data-capture-events",
    ]:
        assert_true(elements_with(root, attr=attr), f"missing DOM binding: {attr}")

    scripts = [element for element in elements_with(root, tag="script") if has_attr(element, "src", "./app.js")]
    styles = [element for element in elements_with(root, tag="link") if has_attr(element, "href", "./styles.css")]
    assert_true(scripts, "missing app.js script tag")
    assert_true(styles, "missing styles.css link tag")
    assert_true("youtube-title" not in html, "legacy YouTube section should not be visible in the UI")
    assert_true(len(elements_with(root, tag="article")) >= 3, "expected report panels and review cards")
    return {
        "binding_count": sum(1 for element in root.all() for attr in element.attrs if attr.startswith("data-")),
        "panel_count": len(elements_with(root, tag="article")),
    }


def validate_reports(activity: dict[str, object], capture: dict[str, object], youtube: dict[str, object]) -> None:
    for name, report in [("activity", activity), ("capture", capture), ("youtube", youtube)]:
        summary = report.get("summary")
        if not isinstance(summary, dict):
            raise AssertionError(f"{name} report missing summary")
        if not summary.get("narrative"):
            raise AssertionError(f"{name} report missing narrative")
    if not capture.get("items"):
        raise AssertionError("capture report missing replay items")


def find_browser() -> str | None:
    configured = os.environ.get("INTENTOS_BROWSER_BIN")
    if configured and Path(configured).is_file():
        return configured
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    for command_name in ["google-chrome", "chromium", "chromium-browser"]:
        resolved = shutil.which(command_name)
        if resolved:
            return resolved
    return None


def render_with_browser(base: str, artifact_dir: Path, browser: str) -> dict[str, object]:
    screenshot = artifact_dir / "ui-rendered-screenshot.png"
    profile_dir = artifact_dir.parent / "browser-profile"
    log_path = artifact_dir.parent / "logs" / "ui-render-browser.log"
    command = [
        browser,
        "--headless=new",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-extensions",
        "--disable-gpu",
        "--disable-sync",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--run-all-compositor-stages-before-draw",
        "--timeout=5000",
        f"--user-data-dir={profile_dir}",
        "--window-size=1280,900",
        f"--screenshot={screenshot}",
        f"{base}/site/index.html",
    ]
    timed_out = False
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=30)
        log_path.write_text(result.stderr + result.stdout, encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"browser render failed with exit {result.returncode}; see {log_path}")
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        log_path.write_text(
            stderr + stdout + "\nui-validation: browser timed out after writing PNG\n",
            encoding="utf-8",
        )
    screenshot_stats = assert_useful_png(screenshot, min_width=1000, min_height=700)
    return {
        "status": "ok",
        "browser": browser,
        "timed_out_after_png": timed_out,
        "screenshot_path": str(screenshot),
        "screenshot": screenshot_stats,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--text-output", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--snapshot-output", required=True)
    args = parser.parse_args()

    artifact_dir = Path(args.artifact_dir)
    text_output = Path(args.text_output)
    json_output = Path(args.json_output)
    snapshot_output = Path(args.snapshot_output)
    base = f"http://127.0.0.1:{args.port}"

    html = fetch(base, "/site/index.html")
    app_js = fetch(base, "/site/app.js")
    activity = json.loads(fetch(base, "/artifacts/activity-summary.json"))
    capture = json.loads(fetch(base, "/artifacts/capture-summary.json"))
    youtube = json.loads(fetch(base, "/artifacts/youtube-summary.json"))

    static_dom = validate_static_dom(html)
    validate_reports(activity, capture, youtube)
    for token in [
        "data-primary-narrative",
        "activity-summary.json",
        "capture-summary.json",
        "live-capture-summary.json",
    ]:
        assert_true(token in app_js, f"missing app binding: {token}")

    snapshot_output.write_text(html, encoding="utf-8")
    checked_screenshot = assert_useful_png(
        ROOT / "docs/assets/screenshots/intent-os-ui.png",
        min_width=1024,
        min_height=700,
    )

    render_browser = os.environ.get("INTENTOS_UI_RENDER_BROWSER") == "1"
    require_browser = os.environ.get("INTENTOS_UI_REQUIRE_BROWSER") == "1"
    browser = find_browser() if render_browser or require_browser else None
    browser_validation: dict[str, object]
    if browser:
        browser_validation = render_with_browser(base, artifact_dir, browser)
    elif require_browser:
        raise AssertionError("Chrome or Chromium is required for rendered UI validation")
    else:
        reason = "set INTENTOS_UI_RENDER_BROWSER=1 to enable Chrome/Chromium rendering"
        browser_validation = {"status": "skipped", "reason": reason}

    validation = {
        "status": "ok",
        "url": f"{base}/site/index.html",
        "activity_narrative": activity["summary"]["narrative"],
        "capture_items": len(capture.get("items", [])),
        "youtube_narrative": youtube["summary"]["narrative"],
        "snapshot_path": str(snapshot_output),
        "static_dom": static_dom,
        "checked_screenshot": checked_screenshot,
        "browser_render": browser_validation,
    }
    json_output.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    lines = [
        "ui-validation: ok",
        f"url={validation['url']}",
        f"activity={validation['activity_narrative']}",
        f"capture_items={validation['capture_items']}",
        f"youtube={validation['youtube_narrative']}",
        f"static_dom_bindings={static_dom['binding_count']}",
        f"checked_screenshot={checked_screenshot['width']}x{checked_screenshot['height']}",
        f"browser_render={browser_validation['status']}",
        f"snapshot={snapshot_output}",
    ]
    if browser_validation["status"] == "ok":
        lines.append(f"rendered_screenshot={browser_validation['screenshot_path']}")
    text_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(text_output.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
