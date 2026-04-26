# Execution Plans

Execution plans are first-class artifacts for substantial Codex work. They keep
intent, scope, progress, and verification visible inside the repo.

## Directories

- `active/`: plans currently being implemented.
- `completed/`: finished plans retained for history.
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
