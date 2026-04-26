"""Privacy policy helpers for metadata-only capture."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_EXCERPT_LIMIT = 180


@dataclass(frozen=True)
class PrivacyPolicy:
    excluded_apps: tuple[str, ...] = ()
    excluded_bundle_ids: tuple[str, ...] = ()
    excluded_domains: tuple[str, ...] = ()
    excluded_url_substrings: tuple[str, ...] = ()
    excluded_window_title_substrings: tuple[str, ...] = ()
    sensitive_terms: tuple[str, ...] = ()
    private_browsing_terms: tuple[str, ...] = ()
    visible_text_limit: int = DEFAULT_EXCERPT_LIMIT


def load_privacy_policy(path: str | Path) -> PrivacyPolicy:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("privacy policy must be an object")
    visible_text_limit = raw.get("visible_text_limit", DEFAULT_EXCERPT_LIMIT)
    if not isinstance(visible_text_limit, int) or visible_text_limit <= 0:
        raise ValueError("privacy policy visible_text_limit must be positive")
    return PrivacyPolicy(
        excluded_apps=tuple_list(raw, "excluded_apps"),
        excluded_bundle_ids=tuple_list(raw, "excluded_bundle_ids"),
        excluded_domains=tuple_list(raw, "excluded_domains"),
        excluded_url_substrings=tuple_list(raw, "excluded_url_substrings"),
        excluded_window_title_substrings=tuple_list(
            raw, "excluded_window_title_substrings"
        ),
        sensitive_terms=tuple_list(raw, "sensitive_terms"),
        private_browsing_terms=tuple_list(raw, "private_browsing_terms"),
        visible_text_limit=visible_text_limit,
    )


def should_exclude(metadata: dict[str, Any], policy: PrivacyPolicy) -> bool:
    app_name = clean(metadata.get("app_name"))
    bundle_id = clean(metadata.get("bundle_id"))
    domain = clean(metadata.get("domain"))
    url = clean(metadata.get("url"))
    window_title = clean(metadata.get("window_title"))
    title = clean(metadata.get("title"))
    visible_text_excerpt = clean(metadata.get("visible_text_excerpt"))
    combined = " ".join(
        [app_name, bundle_id, domain, url, window_title, title, visible_text_excerpt]
    )

    return (
        exact_match(app_name, policy.excluded_apps)
        or exact_match(bundle_id, policy.excluded_bundle_ids)
        or domain_match(domain, policy.excluded_domains)
        or contains_any(url, policy.excluded_url_substrings)
        or contains_any(window_title, policy.excluded_window_title_substrings)
        or contains_any(title, policy.excluded_window_title_substrings)
        or contains_any(combined, policy.sensitive_terms)
        or contains_any(combined, policy.private_browsing_terms)
    )


def redact_metadata(metadata: dict[str, Any], policy: PrivacyPolicy) -> dict[str, Any]:
    redacted = dict(metadata)
    excerpt = redacted.get("visible_text_excerpt")
    if isinstance(excerpt, str):
        redacted["visible_text_excerpt"] = bound_text(excerpt, policy.visible_text_limit)
    return redacted


def bound_text(value: str, limit: int = DEFAULT_EXCERPT_LIMIT) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 3)].rstrip() + "..."


def tuple_list(raw: dict[str, Any], key: str) -> tuple[str, ...]:
    value = raw.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"privacy policy {key} must be a list of strings")
    return tuple(item.strip().lower() for item in value if item.strip())


def clean(value: object) -> str:
    return value.lower().strip() if isinstance(value, str) else ""


def exact_match(value: str, candidates: tuple[str, ...]) -> bool:
    return bool(value) and value in candidates


def domain_match(value: str, candidates: tuple[str, ...]) -> bool:
    return bool(value) and any(value == candidate or value.endswith("." + candidate) for candidate in candidates)


def contains_any(value: str, candidates: tuple[str, ...]) -> bool:
    return bool(value) and any(candidate in value for candidate in candidates)
