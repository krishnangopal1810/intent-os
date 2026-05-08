#!/usr/bin/env python3
"""Validate trusted-beta cohort evidence scaffolding and optional results."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "data/beta/cohort_evidence_template.json"
DEFAULT_EVIDENCE = ROOT / ".harness/runtime/artifacts/cohort-evidence.json"
OUTPUT = ROOT / ".harness/runtime/artifacts/cohort-evidence-check.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", default=str(DEFAULT_EVIDENCE))
    args = parser.parse_args()
    failures: list[str] = []
    template = load_json(TEMPLATE, failures, required=True) or {}
    check_template(template, failures)
    evidence_path = Path(args.evidence)
    evidence = load_json(evidence_path, failures, required=False)
    metrics = check_evidence(evidence, template, failures) if evidence else {}
    target_status = check_success_targets(metrics, template, failures) if evidence else {}
    result = {
        "status": "failed" if failures else "ok",
        "template": str(TEMPLATE.relative_to(ROOT)),
        "evidence": rel(evidence_path),
        "evidence_present": evidence_path.is_file(),
        "metrics": metrics,
        "target_status": target_status,
        "failures": failures,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if failures:
        for failure in failures:
            print(f"cohort-evidence-check: {failure}", file=sys.stderr)
        return 1
    print(f"cohort-evidence-check: ok ({OUTPUT})")
    return 0


def check_template(template: dict[str, Any], failures: list[str]) -> None:
    required = set(template.get("required_fields_per_tester") or [])
    for field in [
        "days_completed",
        "setup_minutes",
        "first_captured_app_or_window",
        "first_live_state",
        "evening_review_completed",
        "correction_themes",
        "would_miss_next_week",
        "repeated_feedback_mapped_to",
    ]:
        if field not in required:
            failures.append(f"cohort evidence template missing tester field {field}")
    privacy = template.get("privacy") or {}
    for key in ["raw_sqlite_shared", "screenshots_required", "raw_titles_or_urls_required"]:
        if privacy.get(key) is not False:
            failures.append(f"cohort evidence template must keep {key}=false")
    allowed_states = template.get("allowed_first_live_states")
    expected_states = {
        "focus_protected",
        "avoid_leaking",
        "recovery_available",
        "evidence_insufficient",
    }
    if set(allowed_states or []) != expected_states:
        failures.append("cohort evidence template must list the first live states")


def check_evidence(
    evidence: dict[str, Any],
    template: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    testers = evidence.get("testers")
    if not isinstance(testers, list):
        failures.append("cohort evidence must include testers list")
        return {}
    required = set(template.get("required_fields_per_tester") or [])
    mappings = set(template.get("allowed_feedback_mappings") or [])
    allowed_states = set(template.get("allowed_first_live_states") or [])
    setup_minutes: list[float] = []
    would_miss = 0
    three_day = 0
    seven_day = 0
    for index, tester in enumerate(testers, start=1):
        if not isinstance(tester, dict):
            failures.append(f"tester {index} must be an object")
            continue
        missing = sorted(field for field in required if field not in tester)
        if missing:
            failures.append(f"tester {index} missing {', '.join(missing)}")
        if isinstance(tester.get("setup_minutes"), (int, float)):
            value = float(tester["setup_minutes"])
            if value < 0:
                failures.append(f"tester {index} setup_minutes must be non-negative")
            else:
                setup_minutes.append(value)
        else:
            failures.append(f"tester {index} setup_minutes must be numeric")
        if tester.get("first_live_state") not in allowed_states:
            failures.append(
                f"tester {index} first_live_state must be one of "
                f"{', '.join(sorted(allowed_states))}"
            )
        captured = tester.get("first_captured_app_or_window")
        if not isinstance(captured, str) or not captured.strip():
            failures.append(f"tester {index} first_captured_app_or_window must be non-empty")
        if not isinstance(tester.get("evening_review_completed"), bool):
            failures.append(f"tester {index} evening_review_completed must be boolean")
        if not isinstance(tester.get("would_miss_next_week"), bool):
            failures.append(f"tester {index} would_miss_next_week must be boolean")
        if not isinstance(tester.get("correction_themes"), list):
            failures.append(f"tester {index} correction_themes must be a list")
        if tester.get("would_miss_next_week") is True:
            would_miss += 1
        days_completed = tester.get("days_completed")
        if not isinstance(days_completed, int) or days_completed < 0:
            failures.append(f"tester {index} days_completed must be a non-negative integer")
            days_completed = 0
        if days_completed >= 3:
            three_day += 1
        if days_completed >= 7:
            seven_day += 1
        feedback_mappings = tester.get("repeated_feedback_mapped_to")
        if not isinstance(feedback_mappings, list):
            failures.append(f"tester {index} repeated_feedback_mapped_to must be a list")
            feedback_mappings = []
        for mapping in feedback_mappings:
            if mapping not in mappings:
                failures.append(f"tester {index} has unknown feedback mapping {mapping}")
    median_setup = statistics.median(setup_minutes) if setup_minutes else None
    return {
        "tester_count": len(testers),
        "three_day_testers": three_day,
        "seven_day_testers": seven_day,
        "would_miss_yes": would_miss,
        "median_setup_minutes": median_setup,
    }


def check_success_targets(
    metrics: dict[str, Any],
    template: dict[str, Any],
    failures: list[str],
) -> dict[str, Any]:
    targets = template.get("success_targets") or {}
    status: dict[str, Any] = {}
    minimum_targets = [
        "three_day_testers",
        "seven_day_testers",
        "would_miss_yes",
    ]
    for key in minimum_targets:
        target = targets.get(key)
        actual = metrics.get(key)
        passed = isinstance(target, int) and isinstance(actual, int) and actual >= target
        status[key] = {"actual": actual, "target": target, "passed": passed}
        if not passed:
            failures.append(f"cohort evidence {key} below target: {actual} < {target}")

    setup_target = targets.get("median_setup_minutes")
    setup_actual = metrics.get("median_setup_minutes")
    setup_passed = (
        isinstance(setup_target, (int, float))
        and isinstance(setup_actual, (int, float))
        and setup_actual <= float(setup_target)
    )
    status["median_setup_minutes"] = {
        "actual": setup_actual,
        "target": setup_target,
        "passed": setup_passed,
    }
    if not setup_passed:
        failures.append(
            "cohort evidence median_setup_minutes above target: "
            f"{setup_actual} > {setup_target}"
        )
    return status


def load_json(path: Path, failures: list[str], required: bool) -> dict[str, Any] | None:
    if not path.is_file():
        if required:
            failures.append(f"missing {rel(path)}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"{rel(path)} is invalid JSON: {exc}")
        return None
    return payload if isinstance(payload, dict) else None


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
