"""Sticky daily-loop read model for the dogfood beta."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from intentos.beta import daily_state, focus_rescue, loop_coach, review, store
from intentos.youtube import format_duration


def daily_loop(
    conn: sqlite3.Connection,
    date: str,
    db_path: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    report = review.daily_review(conn, date, db_path)
    intent = daily_state.daily_intent(conn, date)
    checkin = daily_state.review_checkin(conn, date)
    items = report["items"]
    focus_seconds = loop_coach.label_seconds(report, loop_coach.FOCUS_LABELS)
    reactive_seconds = loop_coach.label_seconds(report, loop_coach.REACTIVE_LABELS)
    correction_count = sum(1 for item in items if item.get("corrected_label"))
    low_confidence_count = len(report.get("low_confidence_segments") or [])
    prompt = loop_prompt_state(
        report["summary"]["total_seconds"],
        bool(intent),
        bool(checkin),
        now,
    )
    plan_vs_actual = loop_coach.compare_plan_to_actual(
        intent,
        items,
        focus_seconds,
        reactive_seconds,
        correction_count,
        low_confidence_count,
    )
    preliminary_focus_rescue = focus_rescue.build_focus_rescue(
        date,
        intent,
        items,
        latest_action=None,
    )
    latest_focus_rescue_action = daily_state.latest_focus_rescue_action(
        conn,
        date,
        preliminary_focus_rescue.get("rescue_key"),
    )
    rescue = focus_rescue.build_focus_rescue(
        date,
        intent,
        items,
        latest_focus_rescue_action,
    )
    record_activation_rescue_state(conn, rescue)
    status = store.status(conn, db_path)
    return {
        "date": date,
        "generated_at": store.utc_now(),
        "intent": intent,
        "review_checkin": checkin,
        "prompt": prompt,
        "correction_count": correction_count,
        "low_confidence_count": low_confidence_count,
        "plan_vs_actual": plan_vs_actual,
        "focus_rescue": rescue,
        "intent_contract": loop_coach.build_intent_contract(intent, items),
        "next_block": loop_coach.build_next_block(
            intent,
            plan_vs_actual,
            items,
            low_confidence_count,
        ),
        "correction_reward": loop_coach.build_correction_reward(
            items,
            correction_count,
            low_confidence_count,
        ),
        "summary": report["summary"],
        "status": status,
    }


def loop_prompt_state(
    total_seconds: int,
    has_intent: bool,
    has_checkin: bool,
    now: datetime | None = None,
) -> dict[str, Any]:
    local_now = (now or datetime.now()).astimezone()
    review_ready = local_now.hour >= 17 or total_seconds >= 7200
    intent_due = not has_intent
    review_due = has_intent and review_ready and not has_checkin
    if intent_due:
        state = "intent_due"
    elif review_due:
        state = "review_due"
    elif has_checkin:
        state = "review_complete"
    else:
        state = "running"
    return {
        "state": state,
        "intent_due": intent_due,
        "review_due": review_due,
        "review_ready": review_ready,
        "review_completed": has_checkin,
        "local_hour": local_now.hour,
        "captured_seconds": total_seconds,
        "reason": prompt_reason(state, review_ready, total_seconds),
    }


def prompt_reason(state: str, review_ready: bool, total_seconds: int) -> str:
    if state == "intent_due":
        return "Set one focus and one thing to avoid for today's review."
    if state == "review_due":
        return "Evening review is ready because the day has enough signal."
    if state == "review_complete":
        return "Today's review check-in is complete."
    if review_ready:
        return "Review is ready after 5pm or 2h of captured activity."
    return f"Review will unlock after 5pm or 2h captured; {format_duration(total_seconds)} is available."


def record_activation_rescue_state(conn: sqlite3.Connection, rescue: dict[str, Any]) -> None:
    if rescue.get("state") in {"focus_protected", "recovery_available", "avoid_leaking"}:
        store.set_status_once(conn, "activation_first_rescue_state_at", store.utc_now())
