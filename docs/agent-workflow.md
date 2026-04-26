# Codex Product Build Workflow

Use this workflow for product work. The objective is to keep Codex able to move
from prompt to shipped slice without relying on hidden context.

## 1. Intake

Before implementation, make sure [product/BRIEF.md](product/BRIEF.md) contains:

- Target user
- Problem being solved
- Product promise
- Non-goals
- Constraints
- First useful slice
- Acceptance criteria

If the user gives new product direction, update the brief or a product spec
before coding.

## 2. Plan

Create an execution plan for meaningful work:

```sh
scripts/harness/new-plan.sh short-slug
```

The plan must define scope, acceptance criteria, verification, and a progress
log. Keep the plan active until the work is implemented, verified, and handed
off.

For parallel work, create or use a package under `docs/plans/parallel/`. The
package must include a shared tracker, one task file per agent, explicit
owned-file lists, shared interfaces, and merge order. Agents should not edit
outside their owned files unless the coordinator changes the tracker.

## 3. Design

For new system boundaries or stack choices:

- Update [ARCHITECTURE.md](ARCHITECTURE.md).
- Add a decision record under [decisions](decisions) when the decision affects
  future work.
- Keep dependencies boring and inspectable unless requirements justify
  otherwise.

## 4. Implement

Build the smallest complete vertical slice that satisfies the active plan.
Prefer product behavior over scaffolding. Update tests, docs, and verification
commands in the same change.

## 5. Verify

Run:

```sh
make verify
```

When product code exists, verification must include runtime legibility:

- `make dev` starts the app for the current worktree in fixture-only mode.
- `make dev-live` captures a fresh bounded macOS session and starts the UI with
  that live session artifact preferred.
- `make app-status` confirms the app URL, process, and logs.
- `make validate-ui` validates the local UI shell and product artifacts.
- `make update-ui-screenshot` refreshes checked-in visual evidence whenever UI
  source, fixture inputs, or report output changes.
- `make check-ui-screenshot` verifies screenshot evidence freshness.
- `make observe` exposes local logs and runtime signals.
- `make diagnose` prints app state, structured runtime events, UI validation
  evidence, and recent logs.
- `make observe-live` manually exercises live local sensors when the task
  changes macOS capture behavior. Do not put this in CI; use fixtures for
  deterministic verification.
- `make observe-session` manually exercises the bounded live timeline loop when
  the task changes repeated capture or session merge behavior. Keep it outside
  CI and cover session behavior with deterministic fixtures.

Capture screenshots, logs, or notes in the active plan when visual or runtime
behavior matters. For UI changes, update
`docs/assets/screenshots/intent-os-ui.png` before handoff unless the change is
purely non-visual.

## 6. Handoff

Before ending a task:

- Record completed work and verification results in the active plan.
- Move completed plans to `docs/plans/completed/` when they no longer need
  active tracking.
- Update [QUALITY.md](QUALITY.md) with any newly discovered gap.
- State remaining risks or blockers clearly.
