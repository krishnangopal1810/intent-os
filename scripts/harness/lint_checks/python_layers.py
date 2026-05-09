"""Focused harness lint checks."""

from __future__ import annotations

import ast
import subprocess

from .common import ROOT, import_targets
from .layer_map import ALLOWED_IMPORTS, EXPECTED_LAYERS, MAX_PYTHON_LINES, PYTHON_DISCOVERY_ROOTS


def check_required_python_files(failures: list[str]) -> None:
    discovered = discover_python_files()
    for path in sorted(discovered - EXPECTED_LAYERS):
        failures.append(
            f"unregistered Python file {path}; add it to EXPECTED_LAYERS and "
            "ALLOWED_IMPORTS so architecture and size checks apply"
        )
    for path in sorted(EXPECTED_LAYERS):
        if not (ROOT / path).is_file():
            failures.append(
                f"missing {path}; keep the MVP layer map in docs/ARCHITECTURE.md "
                "and scripts/harness/lint_checks/layer_map.py aligned"
            )


def discover_python_files() -> set[str]:
    paths: set[str] = set()
    for root_name in PYTHON_DISCOVERY_ROOTS:
        for path in (ROOT / root_name).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            paths.add(str(path.relative_to(ROOT)))
    return paths


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
        if path in {"intentos/youtube.py", "intentos/activity.py"}:
            forbidden = sorted(
                target
                for target in imported
                if target.startswith("intentos.") and target != path.removesuffix(".py").replace("/", ".")
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
