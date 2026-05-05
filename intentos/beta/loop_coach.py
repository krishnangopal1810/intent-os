"""Deterministic daily-loop coaching helpers for the beta."""

from __future__ import annotations

from typing import Any

from intentos.youtube import format_duration


FOCUS_LABELS = {"deep_work", "learning", "active_creation"}
REACTIVE_LABELS = {"passive_consumption", "entertainment"}
REVIEW_LABELS = {"unknown"}
STOPWORDS = {
    "about", "after", "avoid", "before", "bound", "cap", "deep", "focus", "from",
    "keep", "limit", "note", "one", "open", "preserve", "protect", "reduce",
    "review", "ship", "stay", "the", "this", "today", "with", "work",
}


def label_seconds(report: dict[str, Any], wanted: set[str]) -> int:
    labels = report["summary"].get("labels", {})
    return sum(int(labels.get(label, {}).get("seconds", 0)) for label in wanted)


def significant_tokens(value: object) -> list[str]:
    if not isinstance(value, str):
        return []
    raw = "".join(ch.lower() if ch.isalnum() else " " for ch in value).split()
    seen: set[str] = set()
    tokens = []
    for token in raw:
        if len(token) < 3 or token in STOPWORDS or token in seen:
            continue
        seen.add(token)
        tokens.append(token)
    return tokens[:8]


def matching_item(
    query: object, items: list[dict[str, Any]], wanted_labels: set[str] | None = None
) -> dict[str, Any] | None:
    tokens = significant_tokens(query)
    if not tokens:
        return None
    ranked = []
    for item in items:
        if wanted_labels is not None and item.get("label") not in wanted_labels:
            continue
        haystack = item_haystack(item)
        matches = sum(1 for token in tokens if token in haystack)
        if matches:
            ranked.append((matches, item.get("duration_seconds", 0), item))
    ranked.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return ranked[0][2] if ranked else None


def top_item_for_labels(items: list[dict[str, Any]], wanted: set[str]) -> dict[str, Any] | None:
    rows = [item for item in items if item.get("label") in wanted]
    rows.sort(key=lambda item: item.get("duration_seconds", 0), reverse=True)
    return rows[0] if rows else None


def compact_item(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if item is None:
        return None
    return {
        "source_app": item.get("source_app"), "surface": item.get("surface"),
        "title": item.get("title"), "label": item.get("label"),
        "duration": item.get("duration") or format_duration(item.get("duration_seconds", 0)),
        "duration_seconds": item.get("duration_seconds", 0), "confidence": item.get("confidence"),
        "evidence_id": item.get("segment_key"),
    }


def compare_plan_to_actual(
    intent: dict[str, Any] | None,
    items: list[dict[str, Any]],
    focus_seconds: int,
    reactive_seconds: int,
    correction_count: int,
    low_confidence_count: int,
) -> dict[str, Any]:
    focus_match = matching_item(intent.get("focus_text"), items, FOCUS_LABELS) if intent else None
    avoid_match = matching_item(intent.get("avoid_text"), items, REACTIVE_LABELS) if intent else None
    if focus_match is None:
        focus_match = top_item_for_labels(items, FOCUS_LABELS)
    if avoid_match is None:
        avoid_match = top_item_for_labels(items, REACTIVE_LABELS)
    focus_item = compact_item(focus_match)
    avoid_item = compact_item(avoid_match)
    return {
        "focus_duration": format_duration(focus_seconds),
        "focus_seconds": focus_seconds,
        "reactive_duration": format_duration(reactive_seconds),
        "reactive_seconds": reactive_seconds,
        "matched_focus": focus_item,
        "matched_avoid": avoid_item,
        "protected_focus": plan_side(intent, "focus_text", focus_seconds, focus_item, "matched"),
        "avoid_target": plan_side(intent, "avoid_text", reactive_seconds, avoid_item, "leaked"),
        "actual_summary": actual_summary_text(focus_seconds, reactive_seconds, low_confidence_count),
        "verdict": plan_verdict(intent, focus_seconds, reactive_seconds, low_confidence_count),
        "receipts": plan_receipts(focus_item, avoid_item, items),
        "accuracy_note": accuracy_note(correction_count, low_confidence_count),
    }


def build_intent_contract(intent: dict[str, Any] | None, items: list[dict[str, Any]]) -> dict[str, Any]:
    focus_text = text_or_empty(intent.get("focus_text") if intent else "")
    avoid_text = text_or_empty(intent.get("avoid_text") if intent else "")
    note = text_or_empty(intent.get("note") if intent else "")
    focus_tokens = significant_tokens(focus_text)
    avoid_tokens = significant_tokens(avoid_text)
    return {
        "focus_text": focus_text,
        "avoid_text": avoid_text,
        "note": note,
        "focus_tokens": focus_tokens,
        "avoid_tokens": avoid_tokens,
        "note_tokens": significant_tokens(note),
        "matched_focus_signals": matched_signals(focus_tokens, items),
        "matched_avoid_signals": matched_signals(avoid_tokens, items),
        "explanation": contract_explanation(focus_tokens, avoid_tokens),
    }


def build_next_block(
    intent: dict[str, Any] | None,
    plan: dict[str, Any],
    items: list[dict[str, Any]],
    low_confidence_count: int,
) -> dict[str, Any]:
    focus_item = plan.get("matched_focus")
    avoid_item = plan.get("matched_avoid")
    total_seconds = plan.get("focus_seconds", 0) + plan.get("reactive_seconds", 0)
    if total_seconds == 0:
        return next_block(
            "Work normally for 20 minutes",
            "IntentOS will compare activity to today's plan once enough local signal lands.",
            None, "Keep IntentOS running while you work.", 0.35, [],
        )
    if avoid_item and plan.get("reactive_seconds", 0) > 0:
        target = surface_name(avoid_item)
        return next_block(
            f"Close {target} before the next block",
            f"{target} touched the avoid side for {avoid_item.get('duration', 'a visible block')}.",
            target, f"Close or cap {target} before starting focused work.", 0.82, evidence_ids([avoid_item]),
        )
    unclear = top_unclear_item(items)
    if unclear or low_confidence_count:
        compact = compact_item(unclear) if unclear else None
        target = surface_name(compact) if compact else "unclear evidence"
        return next_block(
            "Fix the trust gap first",
            f"{target} needs a label check before the review should drive behavior changes.",
            target, "Correct the label so tomorrow's review is sharper.", 0.7,
            evidence_ids([compact] if compact else []),
        )
    if focus_item:
        target = surface_name(focus_item)
        avoid_text = text_or_empty(intent.get("avoid_text") if intent else "")
        constraint = f"Start with {target} open"
        if avoid_text:
            constraint += f" and keep {avoid_text} closed"
        return next_block(
            f"Start with {target}",
            f"{target} matched the focus side for {focus_item.get('duration', 'a focused block')}.",
            target, constraint + ".", 0.78, evidence_ids([focus_item]),
        )
    return next_block(
        "Name the next 20-minute block",
        "The review has activity, but no clear focus match has emerged yet.",
        None, "Pick one surface to open first and one surface to leave closed.", 0.46, [],
    )


def build_correction_reward(
    items: list[dict[str, Any]],
    correction_count: int,
    low_confidence_count: int,
) -> dict[str, Any]:
    surfaces = []
    seen: set[str] = set()
    for item in sorted(items, key=lambda row: row.get("duration_seconds", 0), reverse=True):
        if not item.get("corrected_label"):
            continue
        name = item.get("surface") or item.get("source_app") or item.get("title")
        if name and name not in seen:
            surfaces.append(name)
            seen.add(name)
    noun = "correction" if correction_count == 1 else "corrections"
    message = f"{correction_count} {noun} applied; future reviews will classify these surfaces better."
    if correction_count == 0:
        message = "Corrections will appear here when a label makes future reviews sharper."
    return {
        "correction_count": correction_count, "improved_surfaces": surfaces[:3],
        "low_confidence_count": low_confidence_count, "message": message,
    }


def plan_side(
    intent: dict[str, Any] | None,
    key: str,
    seconds: int,
    match: dict[str, Any] | None,
    matched_status: str,
) -> dict[str, Any]:
    return {
        "text": text_or_empty(intent.get(key) if intent else ""),
        "status": matched_status if match else "waiting", "duration": format_duration(seconds),
        "duration_seconds": seconds, "matched_signal": match,
    }


def plan_verdict(intent: dict[str, Any] | None, focus_seconds: int, reactive_seconds: int, low_confidence_count: int) -> str:
    if not intent:
        return "Set today's plan so IntentOS can compare it with actual activity."
    if focus_seconds == 0 and reactive_seconds == 0:
        return "Work normally for 20 minutes; IntentOS will compare activity to today's plan."
    if reactive_seconds > 0 and reactive_seconds >= focus_seconds:
        return "The avoid target leaked and needs a clearer boundary."
    if low_confidence_count:
        return "Focus held, but a few unclear rows need correction before the review is fully trustworthy."
    if focus_seconds > 0 and reactive_seconds == 0:
        return "The day matched the plan: focus stayed protected and the avoid side stayed quiet."
    return "Some focus held, with a small avoid-side leak to tighten next."


def plan_receipts(focus_item: dict[str, Any] | None, avoid_item: dict[str, Any] | None, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    receipts = []
    if focus_item:
        receipts.append({"kind": "focus", "label": "Focus signal", **focus_item})
    if avoid_item:
        receipts.append({"kind": "avoid", "label": "Avoid signal", **avoid_item})
    unclear = top_unclear_item(items)
    if unclear:
        receipts.append({"kind": "trust", "label": "Needs review", **compact_item(unclear)})
    return receipts[:3]


def matched_signals(tokens: list[str], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not tokens:
        return []
    rows = []
    for item in items:
        for kind, field in [("app", "source_app"), ("surface", "surface"), ("title", "title"), ("url", "url"), ("label", "label")]:
            value = text_or_empty(item.get(field))
            if value and any(token in value.lower() for token in tokens):
                rows.append({"kind": kind, "value": value[:96], "label": item.get("label"), "evidence_id": item.get("segment_key")})
                break
        if len(rows) >= 5:
            break
    return rows


def next_block(title: str, detail: str, target_surface: str | None, suggested_constraint: str, confidence: float, source_evidence_ids: list[str]) -> dict[str, Any]:
    return {
        "title": title, "detail": detail, "target_surface": target_surface,
        "suggested_constraint": suggested_constraint, "confidence": confidence,
        "source_evidence_ids": source_evidence_ids,
    }


def top_unclear_item(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    rows = [item for item in items if item.get("label") in REVIEW_LABELS or float(item.get("confidence") or 1) < 0.55]
    rows.sort(key=lambda item: item.get("duration_seconds", 0), reverse=True)
    return rows[0] if rows else None


def actual_summary_text(focus_seconds: int, reactive_seconds: int, low_confidence_count: int) -> str:
    if focus_seconds == 0 and reactive_seconds == 0:
        return "No strong behavior signal has landed yet."
    if reactive_seconds > focus_seconds:
        return f"{format_duration(reactive_seconds)} was reactive; the avoid target needs a boundary."
    if low_confidence_count:
        return f"{format_duration(focus_seconds)} was high-value, with {low_confidence_count} unclear rows to review."
    return f"{format_duration(focus_seconds)} was high-value and {format_duration(reactive_seconds)} was reactive."


def accuracy_note(correction_count: int, low_confidence_count: int) -> str:
    correction_word = "correction" if correction_count == 1 else "corrections"
    row_word = "row" if low_confidence_count == 1 else "rows"
    return (
        f"{correction_count} {correction_word} applied; "
        f"{low_confidence_count} low-confidence {row_word} still need review."
    )


def contract_explanation(focus_tokens: list[str], avoid_tokens: list[str]) -> str:
    if not focus_tokens and not avoid_tokens:
        return "Add a focus and an avoid target; IntentOS will match app names, domains, titles, URLs, and behavior labels."
    focus = quoted_terms(focus_tokens) or "the focus words"
    avoid = quoted_terms(avoid_tokens) or "the avoid words"
    return (
        f"Tonight's review checks {focus} against high-value signals and {avoid} "
        "against reactive app, domain, title, URL, and label evidence."
    )


def surface_name(item: dict[str, Any] | None) -> str:
    if not item:
        return "the target surface"
    return text_or_empty(item.get("surface") or item.get("title") or item.get("source_app")) or "the target surface"


def evidence_ids(items: list[dict[str, Any] | None]) -> list[str]:
    return [str(item.get("evidence_id")) for item in items if item and item.get("evidence_id")]


def item_haystack(item: dict[str, Any]) -> str:
    return " ".join(str(item.get(field) or "") for field in ["source_app", "surface", "title", "url", "label"]).lower()


def quoted_terms(tokens: list[str]) -> str:
    return ", ".join(f'"{token}"' for token in tokens[:5])


def text_or_empty(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""
