"""Deterministic beta API scenarios for validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from intentos.beta import permissions as beta_permissions
from intentos.beta import state, store as beta_store

from .artifacts import BETA_DATE, read_json, redacted_config, write_json
from .client import BetaHttpClient
from .runtime import RuntimeContext
from .scenario_assertions import (
    validate_activation,
    validate_daily_loop,
    validate_setup_report,
    validate_setup_status,
)
from .scenario_constants import SCENARIO_EXPECTATIONS, UI_TOKENS


def run_api_scenario(ctx: RuntimeContext) -> None:
    client = BetaHttpClient(ctx.service_url, ctx.api_token)
    status = client.get_json("/api/status")
    onboarding = client.get_json("/api/onboarding")
    permissions = client.post_json("/api/permissions/check", {})
    heartbeat = client.post_json("/api/extension-heartbeat", {"version": "validate-beta"})
    connected_status = client.get_json("/api/status")
    if connected_status["extension"]["state"] != "connected":
        raise AssertionError("extension heartbeat did not move bridge to connected")

    raw_bridge_event = fake_bridge_event()
    bridge_post = client.post_json("/api/browser-event", raw_bridge_event)
    posting_status = client.get_json("/api/status")
    if posting_status["extension"]["state"] != "posting_events":
        raise AssertionError("bridge event did not move bridge to posting_events")

    opened = {
        target: client.post_json("/api/open-system-settings", {"target": target})
        for target in ["accessibility", "automation", "chrome_extensions"]
    }
    early_complete = client.post_status("/api/onboarding", {"action": "complete"})
    if early_complete != 400:
        raise AssertionError("onboarding completion should require privacy, capture preview, and daily focus")
    privacy_ack = client.post_json("/api/onboarding", {"action": "acknowledge_privacy"})
    review = client.get_json(f"/api/daily-review?date={BETA_DATE}")
    validate_setup_status(status, permissions, opened, privacy_ack, review)

    segment = review["items"][0]
    correction = client.post_json(
        "/api/corrections",
        {"segment": segment, "corrected_label": "learning", "apply_to_future": True},
    )
    corrected = client.get_json(f"/api/daily-review?date={BETA_DATE}")
    if corrected["items"][0]["label"] != "learning":
        raise AssertionError("correction did not update rendered report")

    sticky_loop_post, sticky_loop_item, unrelated_post, unrelated_item = validate_future_correction(
        client,
        raw_bridge_event,
        segment,
    )
    daily_intent = client.post_json(
        "/api/daily-intent",
        {
            "date": BETA_DATE,
            "focus_text": "Ship the sticky IntentOS loop",
            "avoid_text": "LinkedIn feed",
            "note": "Validation fixture intent",
        },
    )
    completed = client.post_json("/api/onboarding", {"action": "complete"})
    setup_report = client.get_json("/api/setup-report")
    validate_setup_report(completed, setup_report)
    loop_with_intent = client.get_json(f"/api/daily-loop?date={BETA_DATE}")
    validate_daily_loop(loop_with_intent)
    rescue_continue = client.post_json(
        "/api/focus-rescue-action",
        {
            "date": BETA_DATE,
            "rescue_key": loop_with_intent["focus_rescue"]["rescue_key"],
            "action": "continue_intentionally",
            "evidence_id": loop_with_intent["focus_rescue"]["primary_evidence"]["evidence_id"],
            "note": "Validation fixture continued intentionally.",
        },
    )
    loop_after_rescue = client.get_json(f"/api/daily-loop?date={BETA_DATE}")
    if loop_after_rescue["focus_rescue"]["state"] != "avoid_leaking":
        raise AssertionError("focus rescue action did not update daily-loop state")
    activation_after_rescue = client.get_json("/api/status").get("activation", {})
    validate_activation(activation_after_rescue)
    weekly_patterns = client.get_json(f"/api/weekly-patterns?week_start={BETA_DATE}")
    if len(weekly_patterns.get("patterns", [])) != 3:
        raise AssertionError("weekly patterns endpoint must return three cards")
    if "narrative" not in weekly_patterns:
        raise AssertionError("weekly patterns endpoint must include a narrative")
    review_checkin = client.post_json(
        "/api/review-checkin",
        {
            "date": BETA_DATE,
            "outcome": "mixed",
            "reflection_text": "The fixture stayed readable.",
            "next_adjustment": "Keep the avoid target visible.",
        },
    )
    loop_completed = client.get_json(f"/api/daily-loop?date={BETA_DATE}")
    if loop_completed["prompt"]["state"] != "review_complete":
        raise AssertionError("review check-in did not complete the daily loop")
    if loop_completed["review_checkin"]["next_adjustment"] != "Keep the avoid target visible.":
        raise AssertionError("review check-in next adjustment was not persisted")
    activation_after_review = client.get_json("/api/status").get("activation", {})
    if not activation_after_review.get("review_completed_at"):
        raise AssertionError("activation diagnostics missing review_completed_at")
    pause = client.post_json("/api/pause", {"minutes": 15})
    paused = client.get_json("/api/status")
    if not paused["pause"]["paused"]:
        raise AssertionError("pause state was not set")
    client.post_json("/api/resume", {})
    config = validate_static_ui(ctx.ui_url)
    permission_scenarios = validate_permission_scenarios(ctx.paths.validation_json)

    write_json(ctx.paths.daily_review_json, corrected)
    write_json(
        ctx.paths.validation_json,
        {
            "status": "ok",
            "service_url": ctx.service_url,
            "ui_url": ctx.ui_url,
            "initial_rows": status["row_counts"],
            "onboarding": onboarding,
            "early_onboarding_complete_status": early_complete,
            "permissions": permissions["permissions"],
            "setup_report": setup_report["setup_report"],
            "extension_heartbeat": heartbeat,
            "extension_post": bridge_post,
            "sticky_loop_event": sticky_loop_post,
            "sticky_loop_future_correction": sticky_loop_item,
            "sticky_loop_same_domain_unrelated": {"post": unrelated_post, "item": unrelated_item},
            "permission_scenarios": permission_scenarios,
            "open_settings": opened,
            "correction": correction,
            "daily_intent": daily_intent,
            "daily_loop": loop_completed,
            "focus_rescue_action": rescue_continue,
            "focus_rescue_after_action": loop_after_rescue["focus_rescue"],
            "activation": activation_after_review,
            "weekly_patterns": weekly_patterns,
            "review_checkin": review_checkin,
            "pause": pause,
            "delete": {"status": "deferred_until_after_render"},
            "config": config,
        },
    )


def reset_onboarding(db_path: Path) -> None:
    with beta_store.connect(db_path) as conn:
        beta_store.init_db(conn)
        state.update_onboarding(conn, "reset")


def run_delete_scenario(ctx: RuntimeContext) -> None:
    client = BetaHttpClient(ctx.service_url, ctx.api_token)
    delete = client.post_json("/api/delete-local-data", {})
    deleted = client.get_json("/api/status")
    deleted_weekly = client.get_json(f"/api/weekly-patterns?week_start={BETA_DATE}")
    if deleted["row_counts"]["activity_events"] != 0:
        raise AssertionError("delete-local-data did not clear activity events")
    if deleted_weekly["best_focus_window"]["duration_seconds"] != 0:
        raise AssertionError("delete-local-data did not clear weekly source state")
    payload = read_json(ctx.paths.validation_json)
    payload["delete"] = delete
    payload["post_delete_rows"] = deleted["row_counts"]
    payload["post_delete_weekly"] = deleted_weekly
    write_json(ctx.paths.validation_json, payload)


def validate_future_correction(client: BetaHttpClient, raw: dict[str, Any], segment: dict[str, Any]):
    sticky_loop_event = dict(raw)
    sticky_loop_event.update(
        timestamp="2026-04-27T12:00:00Z",
        duration_seconds=7200,
        url="https://chat.openai.com/c/sticky-loop-validation",
        title=segment["title"],
    )
    sticky_loop_post = client.post_json("/api/browser-event", sticky_loop_event)
    unrelated_event = dict(raw)
    unrelated_event.update(
        timestamp="2026-04-27T12:30:00Z",
        duration_seconds=900,
        url="https://chat.openai.com/c/unrelated-domain-scope",
        title="Casual ChatGPT thread",
    )
    unrelated_post = client.post_json("/api/browser-event", unrelated_event)
    review = client.get_json(f"/api/daily-review?date={BETA_DATE}")
    sticky_item = next(item for item in review["items"] if (item.get("url") or "").endswith("/sticky-loop-validation"))
    if sticky_item.get("label") != "learning" or sticky_item.get("corrected_label") != "learning":
        raise AssertionError("apply_to_future correction did not match a future segment key")
    unrelated_item = next(item for item in review["items"] if (item.get("url") or "").endswith("/unrelated-domain-scope"))
    if unrelated_item.get("corrected_label") == "learning":
        raise AssertionError("apply_to_future correction matched an unrelated same-domain segment")
    return sticky_loop_post, sticky_item, unrelated_post, unrelated_item


def validate_static_ui(ui_url: str) -> dict[str, Any]:
    with urlopen(ui_url, timeout=3) as response:
        html = response.read().decode("utf-8")
    scripts_js = []
    for script in [
        "js/state.js",
        "js/api.js",
        "js/navigation.js",
        "js/format.js",
        "js/render-summary.js",
        "js/render-coach.js",
        "js/render-review.js",
        "js/render-daily-loop.js",
        "js/render-beta-queues.js",
        "js/render-onboarding.js",
        "js/boot.js",
    ]:
        with urlopen(ui_url.replace("index.html", script), timeout=3) as response:
            scripts_js.append(response.read().decode("utf-8"))
    with urlopen(ui_url.replace("index.html", "beta-config.json"), timeout=3) as response:
        config = json.loads(response.read().decode("utf-8"))
    for token in UI_TOKENS:
        if token not in html + "\n".join(scripts_js):
            raise AssertionError(f"missing beta UI token: {token}")
    return redacted_config(config)


def validate_permission_scenarios(validation_path: Path) -> dict[str, dict[str, Any]]:
    permission_scenarios = {}
    for scenario, expected in SCENARIO_EXPECTATIONS.items():
        scenario_db = validation_path.with_name(f"beta-permission-{scenario}.sqlite")
        scenario_db.unlink(missing_ok=True)
        with beta_store.connect(scenario_db) as conn:
            beta_store.init_db(conn)
            payload = beta_permissions.apply_fake_scenario(conn, scenario, str(scenario_db))
        summary = {
            "accessibility": payload["permissions"]["accessibility"]["state"],
            "browser_automation": payload["permissions"]["browser_automation"]["state"],
            "native_recorder": payload["native_recorder"]["state"],
            "extension": payload["extension"]["state"],
            "paused": payload["pause"]["paused"],
            "readiness": payload["readiness"]["state"],
        }
        if tuple(summary.values()) != expected:
            raise AssertionError(f"fake scenario {scenario} produced {summary}, expected {expected}")
        permission_scenarios[scenario] = summary
    return permission_scenarios


def fake_bridge_event() -> dict[str, Any]:
    return json.loads(Path("data/beta/fake_chrome_events.json").read_text(encoding="utf-8"))[0]
