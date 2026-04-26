#!/usr/bin/env python3
"""Repository structural checks for agent-legible development."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAX_PYTHON_LINES = 320
EXPECTED_LAYERS = {
    "intentos/youtube.py",
    "intentos/cli.py",
    "intentos/evaluate.py",
    "tests/test_youtube_mvp.py",
}
ALLOWED_IMPORTS = {
    "intentos/cli.py": {"intentos.youtube"},
    "intentos/evaluate.py": {"intentos.youtube"},
    "tests/test_youtube_mvp.py": {"intentos.youtube"},
}


def main() -> int:
    failures: list[str] = []
    check_required_python_files(failures)
    check_python_syntax_and_imports(failures)
    check_file_sizes(failures)
    check_generated_files_not_tracked(failures)
    check_no_stale_active_plans(failures)
    check_quality_scorecard(failures)
    check_evaluation_set(failures)

    if failures:
        for failure in failures:
            print(f"harness-lint: {failure}", file=sys.stderr)
        return 1

    print("harness-lint: ok")
    return 0


def check_required_python_files(failures: list[str]) -> None:
    for path in sorted(EXPECTED_LAYERS):
        if not (ROOT / path).is_file():
            failures.append(
                f"missing {path}; keep the MVP layer map in docs/ARCHITECTURE.md "
                "and scripts/harness/lint.py aligned"
            )


def check_python_syntax_and_imports(failures: list[str]) -> None:
    for path in sorted(EXPECTED_LAYERS):
        full_path = ROOT / path
        if not full_path.is_file():
            continue
        try:
            tree = ast.parse(full_path.read_text(encoding="utf-8"), filename=path)
        except SyntaxError as exc:
            failures.append(f"{path} has invalid Python syntax: {exc}")
            continue

        imported = import_targets(tree)
        if path == "intentos/youtube.py":
            forbidden = sorted(
                target
                for target in imported
                if target.startswith("intentos.") and target != "intentos.youtube"
            )
            if forbidden:
                failures.append(
                    f"{path} is the domain layer and must not import other "
                    f"IntentOS layers; remove {', '.join(forbidden)}"
                )
            continue

        allowed = ALLOWED_IMPORTS.get(path, set())
        forbidden = sorted(
            target
            for target in imported
            if target.startswith("intentos.") and target not in allowed
        )
        if forbidden:
            failures.append(
                f"{path} imports disallowed IntentOS layer(s): {', '.join(forbidden)}; "
                "update the architecture doc and linter if this boundary is intentional"
            )


def import_targets(tree: ast.AST) -> set[str]:
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                targets.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            targets.add(node.module)
    return targets


def check_file_sizes(failures: list[str]) -> None:
    for path in sorted(EXPECTED_LAYERS):
        full_path = ROOT / path
        if not full_path.is_file():
            continue
        line_count = len(full_path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_PYTHON_LINES:
            failures.append(
                f"{path} is {line_count} lines; split it before it exceeds "
                f"the {MAX_PYTHON_LINES}-line agent-legibility limit"
            )


def check_generated_files_not_tracked(failures: list[str]) -> None:
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.splitlines()
    generated = [
        path
        for path in tracked
        if "__pycache__/" in path
        or path.endswith(".pyc")
        or path.startswith(".harness/runtime/")
    ]
    if generated:
        failures.append(
            "generated runtime/cache files are tracked: "
            + ", ".join(sorted(generated))
            + "; remove them from git"
        )


def check_no_stale_active_plans(failures: list[str]) -> None:
    active_dir = ROOT / "docs/plans/active"
    for plan in sorted(active_dir.glob("*.md")):
        text = plan.read_text(encoding="utf-8")
        if "Status: Completed" in text:
            failures.append(
                f"{plan.relative_to(ROOT)} is completed but still active; move it "
                "to docs/plans/completed/"
            )
        if "TBD" in text:
            failures.append(
                f"{plan.relative_to(ROOT)} still contains TBD; resolve or narrow "
                "the plan before implementation"
            )


def check_quality_scorecard(failures: list[str]) -> None:
    text = (ROOT / "docs/QUALITY.md").read_text(encoding="utf-8")
    required_rows = [
        "| Product definition |",
        "| Architecture |",
        "| Verification |",
        "| Security |",
        "| Reliability |",
        "| UX |",
    ]
    for row in required_rows:
        if row not in text:
            failures.append(f"docs/QUALITY.md is missing scorecard row {row}")
    if "| Verification | Green |" not in text:
        failures.append(
            "docs/QUALITY.md should mark verification Green once make verify "
            "runs product tests and evaluation"
        )


def check_evaluation_set(failures: list[str]) -> None:
    path = ROOT / "data/youtube/evaluation_set.json"
    if not path.is_file():
        failures.append("missing data/youtube/evaluation_set.json")
        return

    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"data/youtube/evaluation_set.json is invalid JSON: {exc}")
        return

    if not isinstance(rows, list) or len(rows) < 6:
        failures.append("evaluation set must contain at least 6 labeled examples")
        return

    labels = {row.get("expected_label") for row in rows if isinstance(row, dict)}
    for required in {"learning", "entertainment", "unknown"}:
        if required not in labels:
            failures.append(
                f"evaluation set must include at least one {required} example"
            )


if __name__ == "__main__":
    raise SystemExit(main())
