"""Context cue helpers for the generic ActivityEvent classifier."""

from __future__ import annotations

from urllib.parse import parse_qsl, unquote_plus, urlparse

from intentos.activity import ActivityEvent, event_text


DEVELOPER_DOC_DOMAINS = {
    "bazel.build",
    "developer.mozilla.org",
    "docs.python.org",
}

PRODUCT_RESEARCH_DOMAINS = {
    "amazon.in",
    "store.google.com",
}

PERSONAL_LOGISTICS_DOMAINS = {
    "cravebyleena.com",
    "natureville.in",
    "visaguide.cloud",
}

SEARCH_DEVELOPER_TERMS = {
    "bazel",
    "build",
    "github",
    "python",
}

SEARCH_ADMIN_TERMS = {
    "brunch",
    "cafe",
    "restaurant",
    "rice cooker",
    "secondary market",
    "share price",
    "stock",
    "visa",
}


def classification_text(event: ActivityEvent) -> str:
    return " ".join([event_text(event), url_text(event.url)]).lower()


def context_cues(event: ActivityEvent, text: str) -> dict[str, dict[str, int]]:
    cues: dict[str, dict[str, int]] = {}
    parsed = parsed_event_url(event)
    domain = event_domain(event, parsed)
    path = parsed.path.lower() if parsed else ""
    query = search_query_text(parsed)

    if domain in DEVELOPER_DOC_DOMAINS:
        add_context(cues, "learning", f"developer docs:{domain}", 4)
    if "bazel" in text:
        add_context(cues, "learning", "developer reference:bazel", 3)

    if domain == "github.com" and looks_like_github_repo(path):
        add_context(cues, "deep_work", "github repository", 4)

    if is_localhost_domain(domain) and ("intentos" in text or "intent-os" in text):
        add_context(cues, "deep_work", "local IntentOS review", 4)

    if domain in PRODUCT_RESEARCH_DOMAINS:
        add_context(cues, "admin", f"product research:{domain}", 4)

    if domain in PERSONAL_LOGISTICS_DOMAINS:
        add_context(cues, "admin", f"personal logistics:{domain}", 4)

    if domain == "google.com" and path == "/search" and query:
        if contains_any(query, SEARCH_DEVELOPER_TERMS):
            add_context(cues, "learning", "developer search query", 3)
        if contains_any(query, SEARCH_ADMIN_TERMS):
            add_context(cues, "admin", "personal admin search query", 3)

    if domain == "youtube.com" and contains_any(
        text,
        {
            "asia cup",
            "cricket",
            "england v india",
            "extended highlights",
            "india vs pakistan",
            "ipl",
            "lord's test",
            "nail-biting",
        },
    ):
        add_context(cues, "entertainment", "sports video", 4)

    if domain == "x.com" and (path == "/home" or "/status/" in path):
        add_context(cues, "passive_consumption", "x feed or status", 3)

    if domain == "instagram.com":
        add_context(cues, "passive_consumption", "instagram surface", 4)

    if domain == "linkedin.com" and path.startswith("/in/"):
        add_context(cues, "learning", "linkedin profile research", 3)

    if domain == "reddit.com" and "startup" in text:
        add_context(cues, "learning", "startup research forum", 3)

    return cues


def add_context(
    cues: dict[str, dict[str, int]],
    label: str,
    cue: str,
    weight: int,
) -> None:
    cues.setdefault(label, {})[cue] = weight


def url_text(url: str | None) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    parts = [
        parsed.netloc,
        unquote_plus(parsed.path.replace("/", " ").replace("-", " ").replace("_", " ")),
        search_query_text(parsed),
    ]
    return " ".join(part for part in parts if part)


def parsed_event_url(event: ActivityEvent):
    if not event.url:
        return None
    parsed = urlparse(event.url)
    if not parsed.netloc:
        return None
    return parsed


def event_domain(event: ActivityEvent, parsed) -> str:
    if parsed:
        return parsed.netloc.lower().removeprefix("www.")
    metadata_domain = (event.metadata or {}).get("domain")
    if isinstance(metadata_domain, str) and metadata_domain.strip():
        return metadata_domain.lower().removeprefix("www.")
    return event.surface.lower().removeprefix("www.")


def search_query_text(parsed) -> str:
    if not parsed:
        return ""
    values = [
        value
        for key, value in parse_qsl(parsed.query, keep_blank_values=False)
        if key.lower() in {"q", "query", "search", "k", "keywords"}
    ]
    return " ".join(unquote_plus(value) for value in values).lower()


def looks_like_github_repo(path: str) -> bool:
    parts = [part for part in path.strip("/").split("/") if part]
    return len(parts) >= 2 and parts[1] not in {"followers", "following", "repositories"}


def is_localhost_domain(domain: str) -> bool:
    return (
        domain == "localhost"
        or domain.startswith("localhost:")
        or domain == "127.0.0.1"
        or domain.startswith("127.0.0.1:")
    )


def contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)
