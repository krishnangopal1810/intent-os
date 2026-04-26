"""Browser metadata normalization for metadata-only capture."""

from __future__ import annotations

from dataclasses import dataclass
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
