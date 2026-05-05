"""Focus rescue state helpers for the dogfood beta daily loop."""

from __future__ import annotations

import hashlib
from typing import Any

from intentos.beta import loop_coach
from intentos.youtube import format_duration


THRESHOLD_SECONDS = 5 * 60


def build_focus_rescue(
    date: str,
    intent: dict[str, Any] | None,
    items: list[dict[str, Any]],
    latest_action: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not intent:
        return payload(
            "intent_needed",
            "Intent needed",
            "Set one focus and one thing to avoid so IntentOS knows what to protect.",
            None,
            0,
            0,
            None,
            [],
            latest_action,
        )

    focus_tokens = loop_coach.significant_tokens(intent.get("focus_text"))
    avoid_tokens = loop_coach.significant_tokens(intent.get("avoid_text"))
    focus_items = strict_token_items(items, focus_tokens, loop_coach.FOCUS_LABELS)
    avoid_items = strict_token_items(items, avoid_tokens, loop_coach.REACTIVE_LABELS)
    focus_seconds = sum(int(item.get("duration_seconds") or 0) for item in focus_items)
    avoid_seconds = sum(int(item.get("duration_seconds") or 0) for item in avoid_items)
    focus_item = loop_coach.compact_item(top_by_duration(focus_items))
    avoid_item = loop_coach.compact_item(top_by_duration(avoid_items))
    primary = avoid_item or focus_item
    rescue_key = focus_rescue_key(date, intent, primary)
    receipts = receipts_for(focus_item, avoid_item, latest_action)

    if avoid_seconds >= THRESHOLD_SECONDS and avoid_item:
        return avoid_payload(
            rescue_key,
            focus_seconds,
            avoid_seconds,
            avoid_item,
            receipts,
            latest_action,
        )
    if focus_seconds > 0:
        return payload(
            "focus_protected",
            "Focus protected",
            f"{format_duration(focus_seconds)} matched the focus pattern and the avoid pattern stayed below the rescue threshold.",
            rescue_key,
            focus_seconds,
            avoid_seconds,
            focus_item,
            receipts,
            latest_action,
        )
    return payload(
        "evidence_insufficient",
        "Need evidence",
        "IntentOS has not seen enough strict focus or avoid-pattern evidence for a rescue call yet.",
        rescue_key,
        focus_seconds,
        avoid_seconds,
        primary,
        receipts,
        latest_action,
    )


def avoid_payload(
    rescue_key: str,
    focus_seconds: int,
    avoid_seconds: int,
    avoid_item: dict[str, Any],
    receipts: list[dict[str, Any]],
    latest_action: dict[str, Any] | None,
) -> dict[str, Any]:
    action_name = (latest_action or {}).get("action")
    if action_name in {"continue_intentionally", "pause_capture"}:
        return payload(
            "avoid_leaking",
            "Avoid leaking",
            action_reason(action_name, avoid_item, avoid_seconds),
            rescue_key,
            focus_seconds,
            avoid_seconds,
            avoid_item,
            receipts,
            latest_action,
        )
    if action_name in {"return_to_focus", "corrected_evidence"}:
        return payload(
            "focus_protected",
            "Focus protected",
            action_reason(action_name, avoid_item, avoid_seconds),
            rescue_key,
            focus_seconds,
            avoid_seconds,
            avoid_item,
            receipts,
            latest_action,
        )
    return payload(
        "recovery_available",
        "Recovery available",
        f"{loop_coach.surface_name(avoid_item)} matched the avoid pattern for {format_duration(avoid_seconds)}.",
        rescue_key,
        focus_seconds,
        avoid_seconds,
        avoid_item,
        receipts,
        latest_action,
    )


def strict_token_items(
    items: list[dict[str, Any]],
    tokens: list[str],
    wanted_labels: set[str],
) -> list[dict[str, Any]]:
    if not tokens:
        return []
    return [
        item
        for item in items
        if item.get("label") in wanted_labels
        and any(token in loop_coach.item_haystack(item) for token in tokens)
    ]


def top_by_duration(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    rows = list(items)
    rows.sort(key=lambda item: item.get("duration_seconds", 0), reverse=True)
    return rows[0] if rows else None


def focus_rescue_key(
    date: str,
    intent: dict[str, Any],
    primary: dict[str, Any] | None,
) -> str:
    evidence_id = loop_coach.text_or_empty(primary.get("evidence_id") if primary else "")
    source = "|".join(
        [
            date,
            loop_coach.text_or_empty(intent.get("focus_text")),
            loop_coach.text_or_empty(intent.get("avoid_text")),
            evidence_id or "no-evidence",
        ]
    )
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]


def payload(
    state: str,
    label: str,
    reason: str,
    rescue_key: str | None,
    focus_seconds: int,
    avoid_seconds: int,
    primary: dict[str, Any] | None,
    receipts: list[dict[str, Any]],
    latest_action: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "state": state,
        "label": label,
        "reason": reason,
        "rescue_key": rescue_key,
        "threshold_seconds": THRESHOLD_SECONDS,
        "threshold_duration": format_duration(THRESHOLD_SECONDS),
        "protected_focus_seconds": focus_seconds,
        "protected_focus_duration": format_duration(focus_seconds),
        "avoid_seconds": avoid_seconds,
        "avoid_duration": format_duration(avoid_seconds),
        "primary_evidence": primary,
        "receipts": receipts,
        "latest_action": latest_action,
        "available_choices": choices(state),
    }


def choices(state: str) -> list[dict[str, str]]:
    if state not in {"recovery_available", "avoid_leaking"}:
        return []
    return [
        {"action": "return_to_focus", "label": "Return to focus", "kind": "primary"},
        {
            "action": "continue_intentionally",
            "label": "Continue intentionally",
            "kind": "secondary",
        },
        {"action": "pause_capture", "label": "Pause capture", "kind": "secondary"},
        {"action": "correct_evidence", "label": "Correct evidence", "kind": "secondary"},
    ]


def receipts_for(
    focus_item: dict[str, Any] | None,
    avoid_item: dict[str, Any] | None,
    latest_action: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    receipts = []
    if focus_item:
        receipts.append({"kind": "focus", "label": "Focus evidence", **focus_item})
    if avoid_item:
        receipts.append({"kind": "avoid", "label": "Avoid evidence", **avoid_item})
    if latest_action:
        receipts.append(
            {
                "kind": "choice",
                "label": "Latest choice",
                "title": action_label(latest_action.get("action")),
                "duration": "",
                "surface": latest_action.get("note") or latest_action.get("created_at"),
                "evidence_id": latest_action.get("evidence_id"),
            }
        )
    return receipts[:3]


def action_label(action: object) -> str:
    labels = {
        "shown": "Recovery shown",
        "return_to_focus": "Return to focus",
        "continue_intentionally": "Continue intentionally",
        "pause_capture": "Pause capture",
        "corrected_evidence": "Corrected evidence",
    }
    return labels.get(action, "No choice recorded")


def action_reason(action: object, item: dict[str, Any], seconds: int) -> str:
    target = loop_coach.surface_name(item)
    duration = format_duration(seconds)
    if action == "continue_intentionally":
        return f"You chose to continue intentionally after {target} matched the avoid pattern for {duration}."
    if action == "pause_capture":
        return f"Capture was paused after {target} matched the avoid pattern for {duration}."
    if action == "return_to_focus":
        return f"You chose to return to focus after {target} matched the avoid pattern."
    if action == "corrected_evidence":
        return f"The avoid evidence was corrected after {target} matched the avoid pattern."
    return f"{target} matched the avoid pattern for {duration}."
