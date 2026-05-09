"""Focused harness lint checks."""

from __future__ import annotations

from .common import ROOT


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
        if "## Harness Impact" not in text:
            failures.append(
                f"{plan.relative_to(ROOT)} must include ## Harness Impact so "
                "future runtime, fixture, UI, diagnostics, and privacy work is explicit"
            )
        if "## Acceptance Criteria" not in text:
            failures.append(
                f"{plan.relative_to(ROOT)} must include ## Acceptance Criteria so "
                "implementation and review have a concrete completion gate"
            )
        else:
            for phrase in [
                "Runtime commands and artifacts",
                "Fixtures or fakes",
                "UI validation",
                "Structured logs",
                "Privacy, permission",
                "Docs or harness checks",
            ]:
                if phrase not in text:
                    failures.append(
                        f"{plan.relative_to(ROOT)} Harness Impact must mention {phrase!r}"
                    )


def check_parallel_plan_contract(failures: list[str]) -> None:
    """Validate multi-agent plans have a tracker and disjoint ownership."""
    base = ROOT / "docs/plans/parallel/macos-live-capture"
    tracker = base / "TRACKER.md"
    task_files = [
        base / "agent-1-capture-core.md",
        base / "agent-2-browser-redaction.md",
        base / "agent-3-replay-runtime.md",
    ]

    if not tracker.is_file():
        failures.append("missing docs/plans/parallel/macos-live-capture/TRACKER.md")
        return

    tracker_text = tracker.read_text(encoding="utf-8")
    for required in [
        "Integration Contract",
        "Merge Order",
        "Shared Interfaces",
        "Coordination Rules",
        "Agent 1",
        "Agent 2",
        "Agent 3",
    ]:
        if required not in tracker_text:
            failures.append(
                "docs/plans/parallel/macos-live-capture/TRACKER.md must "
                f"mention {required!r}"
            )

    ownership: dict[str, str] = {}
    required_sections = [
        "## Objective",
        "## Owned Files",
        "## Inputs",
        "## Required Implementation",
        "## Out of Scope",
        "## Verification",
        "## Handoff",
    ]
    for task in task_files:
        if not task.is_file():
            failures.append(f"missing {task.relative_to(ROOT)}")
            continue
        text = task.read_text(encoding="utf-8")
        for section in required_sections:
            if section not in text:
                failures.append(f"{task.relative_to(ROOT)} is missing {section}")
        owned = extract_owned_files(text)
        if not owned:
            failures.append(f"{task.relative_to(ROOT)} must list owned files")
        for path in owned:
            previous = ownership.get(path)
            if previous:
                failures.append(
                    f"parallel ownership conflict: {path} is owned by both "
                    f"{previous} and {task.relative_to(ROOT)}"
                )
            ownership[path] = str(task.relative_to(ROOT))


def extract_owned_files(text: str) -> list[str]:
    owned: list[str] = []
    in_section = False
    for line in text.splitlines():
        if line == "## Owned Files":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section or not line.startswith("- `"):
            continue
        end = line.find("`", 3)
        if end != -1:
            owned.append(line[3:end])
    return owned
