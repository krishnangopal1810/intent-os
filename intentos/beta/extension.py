"""Chrome extension bridge validation for bounded tab metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from intentos.activity import ActivityEvent
from intentos.capture.browser import normalize_domain
from intentos.capture.privacy import PrivacyPolicy, redact_metadata, should_exclude


FORBIDDEN_KEYS = {
    "body",
    "page_body",
    "content",
    "cookies",
    "cookie",
    "authorization",
    "token",
    "password",
}
SENSITIVE_URL_PARTS = (
    "access_token=",
    "id_token=",
    "password=",
    "/checkout",
    "/payment",
    "/login",
    "/maps/dir/",
    "/maps/place/",
    "/maps/@",
)


def chrome_event_to_activity(
    item: dict[str, Any], policy: PrivacyPolicy, index: int = 0
) -> ActivityEvent | None:
    if not isinstance(item, dict):
        raise ValueError(f"browser event {index} must be an object")
    reject_forbidden_payload(item, index)

    url = require_text(item, "url", index)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"browser event {index} url must be http or https")
    if contains_sensitive_url(url):
        return None
    safe_url = storage_safe_url(parsed)

    title = bound_text(require_text(item, "title", index), 160)
    observed_at = parse_observed_at(item.get("timestamp") or item.get("observed_at"), index)
    duration = optional_positive_int(item, "duration_seconds") or 30
    domain = normalize_domain(url)
    metadata = {
        "browser_name": optional_text(item, "browser_name") or "Google Chrome",
        "bundle_id": optional_text(item, "bundle_id") or "com.google.Chrome",
        "domain": domain,
        "tab_id": optional_int(item, "tab_id"),
        "window_id": optional_int(item, "window_id"),
        "active": bool(item.get("active", True)),
        "source": "chrome_extension_bridge",
    }
    for key in ["page_kind", "media_title", "document_title"]:
        value = optional_text(item, key)
        if value:
            metadata[key] = bound_text(value, 120)

    privacy_metadata = {
        "app_name": "Google Chrome",
        "bundle_id": metadata["bundle_id"],
        "domain": domain,
        "url": url,
        "title": title,
        "window_title": title,
    }
    if should_exclude(privacy_metadata, policy):
        return None
    return ActivityEvent(
        source_app="Google Chrome",
        surface=domain,
        title=title,
        started_at=observed_at,
        duration_seconds=duration,
        url=safe_url,
        metadata=redact_metadata({k: v for k, v in metadata.items() if v is not None}, policy),
    )


def reject_forbidden_payload(item: dict[str, Any], index: int) -> None:
    found = sorted(key for key in item if key.lower() in FORBIDDEN_KEYS)
    if found:
        raise ValueError(f"browser event {index} contains unsupported private fields: {', '.join(found)}")


def contains_sensitive_url(url: str) -> bool:
    lowered = url.lower()
    return any(part in lowered for part in SENSITIVE_URL_PARTS)


def storage_safe_url(parsed) -> str:
    return parsed._replace(query="", fragment="").geturl()


def parse_observed_at(value: object, index: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"browser event {index} timestamp must be text")
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"browser event {index} timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def require_text(item: dict[str, Any], key: str, index: int) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"browser event {index} {key} must be non-empty text")
    return value.strip()


def optional_text(item: dict[str, Any], key: str) -> str | None:
    value = item.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else None


def optional_int(item: dict[str, Any], key: str) -> int | None:
    value = item.get(key)
    return value if isinstance(value, int) else None


def optional_positive_int(item: dict[str, Any], key: str) -> int | None:
    value = optional_int(item, key)
    return value if value and value > 0 else None


def bound_text(value: str, limit: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 3)].rstrip() + "..."
