"""Stable keys for beta review segments and correction matching."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


def segment_key_from_parts(item: dict[str, Any]) -> str:
    url = stable_url_pattern(item.get("url"))
    surface = clean_key(domain_for_url(item.get("url")) or item.get("surface"))
    title = clean_key(item.get("title"))
    return "|".join([clean_key(item.get("source_app")), surface, url or title])


def stable_url_pattern(url: object) -> str:
    if not isinstance(url, str) or not url.strip():
        return ""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path}".rstrip("/")


def domain_for_url(url: object) -> str:
    pattern = stable_url_pattern(url)
    return urlparse(pattern).netloc.removeprefix("www.") if pattern else ""


def clean_key(value: object) -> str:
    return " ".join(value.lower().split()) if isinstance(value, str) else ""
