"""Evaluation for generic multi-app ActivityEvent classification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from intentos.activity import parse_event
from intentos.classifier import BehaviorLabel, classify_event


def evaluate(path: str | Path) -> dict[str, Any]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("evaluation set must be a JSON array")

    rows: list[dict[str, Any]] = []
    correct = 0
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"item {index} must be an object")
        event = parse_event(item, index)
        expected = item.get("expected_label")
        if expected not in {label.value for label in BehaviorLabel}:
            raise ValueError(f"item {index} expected_label must be a known behavior label")

        classification = classify_event(event)
        actual = classification.label.value
        passed = actual == expected
        correct += 1 if passed else 0
        rows.append(
            {
                "title": event.title,
                "source_app": event.source_app,
                "expected": expected,
                "actual": actual,
                "confidence": classification.confidence,
                "passed": passed,
                "reason": classification.reason,
            }
        )

    total = len(rows)
    accuracy = round((correct / total) * 100, 1) if total else 0.0
    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate multi-app ActivityEvent classification fixtures."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="data/activity/evaluation_set.json",
        help="Path to a labeled ActivityEvent evaluation JSON file.",
    )
    parser.add_argument(
        "--min-accuracy",
        type=float,
        default=85.0,
        help="Minimum required accuracy percentage.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    result = evaluate(args.input)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"Activity evaluation accuracy: {result['accuracy']}% "
            f"({result['correct']}/{result['total']})"
        )
        for row in result["rows"]:
            status = "PASS" if row["passed"] else "FAIL"
            print(
                f"- {status}: {row['source_app']} - {row['title']} "
                f"expected={row['expected']} actual={row['actual']}"
            )

    if result["accuracy"] < args.min_accuracy:
        print(
            f"Evaluation failed: accuracy {result['accuracy']}% is below "
            f"{args.min_accuracy}%."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
