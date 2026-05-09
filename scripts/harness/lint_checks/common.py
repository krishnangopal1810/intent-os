"""Shared helpers for harness lint checks."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def import_targets(tree: ast.AST) -> set[str]:
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                targets.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            targets.add(node.module)
    return targets


def check_labeled_fixture(
    failures: list[str], path: Path, required_labels: set[str], minimum: int
) -> None:
    if not path.is_file():
        failures.append(f"missing {path.relative_to(ROOT)}")
        return

    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"{path.relative_to(ROOT)} is invalid JSON: {exc}")
        return

    if not isinstance(rows, list) or len(rows) < minimum:
        failures.append(
            f"{path.relative_to(ROOT)} must contain at least {minimum} labeled examples"
        )
        return

    labels = {row.get("expected_label") for row in rows if isinstance(row, dict)}
    for required in sorted(required_labels):
        if required not in labels:
            failures.append(
                f"{path.relative_to(ROOT)} must include at least one {required} example"
            )
