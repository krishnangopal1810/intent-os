"""Assertions shared by beta validation scenarios."""

from __future__ import annotations

from typing import Any


def validate_setup_status(
    status: dict[str, Any],
    permissions: dict[str, Any],
    opened: dict[str, Any],
    privacy_ack: dict[str, Any],
    review: dict[str, Any],
) -> None:
    if status["row_counts"]["activity_events"] < 3:
        raise AssertionError("expected fixture browser events")
    if permissions["permissions"]["accessibility"]["state"] != "ok":
        raise AssertionError("fake permission check did not pass")
    if permissions["capture_preview"]["state"] != "ok":
        raise AssertionError("fake permission check must produce a capture preview")
    expected_titles = {"accessibility": "Accessibility", "automation": "Automation", "chrome_extensions": "Chrome"}
    for target, payload in opened.items():
        if payload["status"] != "validated":
            raise AssertionError(f"settings endpoint did not validate {target}")
        if not payload.get("guidance", {}).get("steps"):
            raise AssertionError(f"settings endpoint must include setup guidance for {target}")
        if expected_titles[target] not in payload["guidance"].get("title", ""):
            raise AssertionError(f"settings guidance must name {target}")
    if not privacy_ack["privacy_acknowledged"]:
        raise AssertionError("privacy acknowledgment was not persisted")
    if not review["items"]:
        raise AssertionError("daily review must include timeline items")



def validate_setup_report(completed: dict[str, Any], setup_report: dict[str, Any]) -> None:
    if not completed["completed"]:
        raise AssertionError("onboarding completion was not persisted after required setup")
    report = setup_report["setup_report"]
    if report["capture_preview"]["state"] != "ok":
        raise AssertionError("setup report must include redacted capture preview state")
    if "window_title" in report["capture_preview"]:
        raise AssertionError("setup report must not expose raw window titles")
    if "preflight" not in report:
        raise AssertionError("setup report must include preflight diagnostics")
    activation = report.get("activation", {})
    if activation.get("time_to_capture_ready_seconds") is None:
        raise AssertionError("setup report must include time_to_capture_ready_seconds")
    if activation["time_to_capture_ready_seconds"] > 60:
        raise AssertionError("capture preview should be verified within 60s in validation")


def validate_daily_loop(loop: dict[str, Any]) -> None:
    if loop["intent"]["focus_text"] != "Ship the sticky IntentOS loop":
        raise AssertionError("daily intent did not persist into daily-loop")
    if loop["prompt"]["state"] != "review_due":
        raise AssertionError("daily-loop should be review_due after 2h captured activity")
    for field in ["correction_count", "low_confidence_count"]:
        if not isinstance(loop.get(field), int):
            raise AssertionError(f"daily-loop must expose {field}")
    for field in ["intent_contract", "next_block", "correction_reward"]:
        if field not in loop:
            raise AssertionError(f"daily-loop must expose {field}")
    receipt = loop.get("evening_receipt") or {}
    if not receipt.get("summary") or not receipt.get("protected_focus"):
        raise AssertionError("daily-loop must expose an evening receipt summary")
    if "linkedin" not in loop["intent_contract"].get("avoid_tokens", []):
        raise AssertionError("daily-loop intent contract did not expose avoid tokens")
    if not loop["next_block"].get("title"):
        raise AssertionError("daily-loop next_block needs a title")
    focus_rescue = loop.get("focus_rescue") or {}
    if focus_rescue.get("state") != "recovery_available":
        raise AssertionError(f"daily-loop focus_rescue should be recovery_available, got {focus_rescue.get('state')}")
    if focus_rescue.get("avoid_seconds", 0) < 300:
        raise AssertionError("daily-loop focus_rescue must expose avoid seconds above threshold")
    if not focus_rescue.get("primary_evidence"):
        raise AssertionError("daily-loop focus_rescue must expose primary evidence")
    if len(focus_rescue.get("available_choices", [])) < 3:
        raise AssertionError("daily-loop focus_rescue must expose local choices")


def validate_activation(activation: dict[str, Any]) -> None:
    for key in ["intent_set_at", "first_live_state_at", "first_rescue_state_at", "first_recovery_action_at", "first_review_ready_at"]:
        if not activation.get(key):
            raise AssertionError(f"activation diagnostics missing {key}")
    if activation.get("app_opened_at") != activation.get("opened_at"):
        raise AssertionError("activation diagnostics must normalize app_opened_at")


