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
    result = {
        "status": "failed" if failures else "ok",
        "template": str(TEMPLATE.relative_to(ROOT)),
        "evidence": rel(evidence_path),
        "evidence_present": evidence_path.is_file(),
        "metrics": metrics,
        "failures": failures,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if failures:
        for failure in failures:
            print(f"cohort-evidence-check: {failure}", file=sys.stderr)
        return 1
    print(f"cohort-evidence-check: ok ({OUTPUT})")
    return 0


def check_template(template: dict[str, Any], failures: list[str]) -> None:
    required = set(template.get("required_fields_per_tester") or [])
    for field in [
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
            setup_minutes.append(float(tester["setup_minutes"]))
        if tester.get("would_miss_next_week") is True:
            would_miss += 1
        if int(tester.get("days_completed") or 0) >= 3:
            three_day += 1
        if int(tester.get("days_completed") or 0) >= 7:
            seven_day += 1
        for mapping in tester.get("repeated_feedback_mapped_to") or []:
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
