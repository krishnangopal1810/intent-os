"""Browser metadata normalization for metadata-only capture."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from string import Template
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class BrowserTab:
    browser_name: str
    bundle_id: str | None
    url: str
    title: str
    domain: str
    source: str = "fake_browser"


class BrowserCaptureError(RuntimeError):
    """Raised when browser metadata capture cannot run."""


BROWSER_APP_NAMES = {
    "arc": "Arc",
    "brave browser": "Brave Browser",
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "microsoft edge": "Microsoft Edge",
    "safari": "Safari",
}

BROWSER_BUNDLE_NAMES = {
    "com.apple.safari": "Safari",
    "com.brave.browser": "Brave Browser",
    "com.google.chrome": "Google Chrome",
    "com.microsoft.edgemac": "Microsoft Edge",
    "company.thebrowser.browser": "Arc",
}

CHROMIUM_TAB_SCRIPT = Template(
    """
tell application "$app_name"
  if (count of windows) is 0 then return ""
  set tabTitle to title of active tab of front window
  set tabUrl to URL of active tab of front window
end tell
return tabTitle & linefeed & tabUrl
""".strip()
)

SAFARI_TAB_SCRIPT = """
tell application "Safari"
  if (count of windows) is 0 then return ""
  set tabTitle to name of current tab of front window
  set tabUrl to URL of current tab of front window
end tell
return tabTitle & linefeed & tabUrl
""".strip()


def parse_browser_tab(item: dict[str, Any], index: int = 0) -> BrowserTab:
    if not isinstance(item, dict):
        raise ValueError(f"browser tab {index} must be an object")

    url = require_text(item, "url", index)
    return BrowserTab(
        browser_name=require_text(item, "browser_name", index),
        bundle_id=optional_text(item, "bundle_id", index),
        url=url,
        title=require_text(item, "title", index),
        domain=normalize_domain(url),
        source=optional_text(item, "source", index) or "fake_browser",
    )


def normalize_domain(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("browser tab url must be http or https")
    return parsed.netloc.removeprefix("www.").lower()


def browser_tab_metadata(tab: BrowserTab) -> dict[str, str]:
    metadata = {
        "browser_name": tab.browser_name,
        "source": tab.source,
        "domain": tab.domain,
    }
    if tab.bundle_id:
        metadata["bundle_id"] = tab.bundle_id
    return metadata


def active_browser_tab(
    app_name: str,
    bundle_id: str | None = None,
    runner=None,
) -> BrowserTab | None:
    browser_name = browser_application_name(app_name, bundle_id)
    if browser_name is None:
        return None

    script = tab_script(browser_name)
    completed = (runner or run_command)(["osascript", "-e", script])
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise BrowserCaptureError(permission_help(browser_name, detail))

    lines = completed.stdout.splitlines()
    if len(lines) < 2 or not lines[0].strip() or not lines[1].strip():
        return None
    url = lines[1].strip()
    try:
        domain = normalize_domain(url)
    except ValueError:
        return None

    return BrowserTab(
        browser_name=app_name,
        bundle_id=bundle_id,
        url=url,
        title=lines[0].strip(),
        domain=domain,
        source="live_browser_osascript",
    )


def browser_application_name(app_name: str, bundle_id: str | None = None) -> str | None:
    if bundle_id:
        mapped = BROWSER_BUNDLE_NAMES.get(bundle_id.lower())
        if mapped:
            return mapped
    return BROWSER_APP_NAMES.get(app_name.lower())


def tab_script(browser_name: str) -> str:
    if browser_name == "Safari":
        return SAFARI_TAB_SCRIPT
    return CHROMIUM_TAB_SCRIPT.substitute(app_name=browser_name)


def run_command(command) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            list(command),
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except FileNotFoundError as exc:
        raise BrowserCaptureError("osascript is required for browser capture") from exc
    except subprocess.TimeoutExpired as exc:
        raise BrowserCaptureError("browser capture timed out while reading active tab") from exc


def permission_help(browser_name: str, detail: str) -> str:
    message = (
        f"{browser_name} active tab capture failed. Grant Automation permission "
        "from the terminal or Codex host app to the browser, then rerun "
        "make observe-live."
    )
    if detail:
        return f"{message} Browser said: {detail}"
    return message


def require_text(item: dict[str, Any], key: str, index: int) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"browser tab {index} {key} must be non-empty text")
    return value.strip()


def optional_text(item: dict[str, Any], key: str, index: int) -> str | None:
    value = item.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"browser tab {index} {key} must be text when present")
    value = value.strip()
    return value or None
