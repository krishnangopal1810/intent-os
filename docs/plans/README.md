# Execution Plans

Execution plans are first-class artifacts for substantial Codex work. They keep
intent, scope, progress, and verification visible inside the repo.

## Directories

- `active/`: plans currently being implemented.
- `completed/`: finished plans retained for history.
- `parallel/`: multi-agent work packages with shared trackers and disjoint
  owned-file lists.
- `templates/`: reusable plan templates.

## Create a Plan

```sh
scripts/harness/new-plan.sh short-slug
```

## Plan Requirements

Each active plan must include:

- Goal
- Scope
- Non-Goals
- Acceptance Criteria
- Verification
- Progress Log

Keep progress entries short and factual. If the implementation changes the
product or architecture direction, update the relevant docs too.

## Parallel Work

Use a parallel work package when a slice can be split into disjoint ownership
areas. Each package should include a tracker plus one task file per agent.

Historical package:

- [parallel/macos-live-capture/TRACKER.md](parallel/macos-live-capture/TRACKER.md)

Rules:

- Each agent gets a clear owned-file list.
- Shared interfaces live in the tracker.
- The coordinator owns tracker updates and final integration.
- `make harness-lint` checks the macOS live-capture package for required task
  sections and ownership conflicts. Create a new parallel package when an
  active automated source plan is split across multiple agents.
