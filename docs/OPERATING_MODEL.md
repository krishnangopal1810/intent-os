# Agent Operating Model

IntentOS should be built so Codex can drive changes end to end with minimal
hidden human coordination.

## Roles

- Humans specify product direction, acceptance criteria, and judgment calls.
- Codex updates specs, implementation, tests, docs, scripts, and follow-up fixes.
- Review feedback should become either code, tests, docs, or harness rules.
- Product feedback should become a harness rule whenever it is locally
  observable.

## Standard Change Loop

1. Read `AGENTS.md`, product docs, architecture docs, and the active plan.
2. Validate the current repo state.
3. Reproduce or specify the requested behavior.
4. Identify the harness layer that should catch regressions for the behavior.
5. Implement the smallest complete slice.
6. Update or name the relevant harness check.
7. Run product and harness verification.
8. Capture runtime evidence when the app has UI or service behavior.
9. Update docs, quality notes, and the active plan.
10. Prepare a PR when requested.

## Harness-Driven Feedback

Follow [HARNESS_DRIVEN_DEVELOPMENT.md](HARNESS_DRIVEN_DEVELOPMENT.md) for any
manual product feedback. Feedback is not resolved by product code alone; the
handoff must say which fixture, probe, lint, smoke, or evaluation case will fail
if the regression returns. If the feedback cannot be automated yet, document the
manual exception and the closest deterministic proxy.

## Review Loop

When working on a PR or review feedback:

- Run `make review-status` when local GitHub tooling is available so branch,
  PR, and check state are captured in `.harness/runtime/artifacts/review-status.json`.
- Fetch unresolved review threads and CI status.
- Address actionable findings in code, tests, or docs.
- Reply with the exact change made and verification run.
- Re-run failing checks before handing off.
- Convert repeated review themes into docs or harness checks.
- Convert product feedback into harness checks before closing the feedback loop.

## Merge Criteria

A change is ready only when:

- Acceptance criteria are satisfied.
- `make verify` passes, or the blocker is explicitly documented.
- Runtime/UI validation evidence exists for UI behavior once a UI exists.
- Checked-in UI screenshot evidence is refreshed when rendered UI behavior
  changes.
- Product assumptions are recorded in docs.
- Known residual risks are captured in the active plan or quality scorecard.

## CI Failure Recovery

Codex should treat CI failures as first-class work:

- Inspect failing job logs.
- Reproduce locally when possible.
- Fix the underlying issue.
- Re-run the relevant local command.
- Update harness scripts when CI failed because the harness was incomplete or
  misleading.

## Recurring Cleanup

Entropy should be handled continuously:

- Keep `docs/QUALITY.md` current.
- Move completed plans out of `docs/plans/active/`.
- Delete or revise stale docs.
- Promote repeated manual review comments into automated checks.
- Keep `AGENTS.md` short and move detail into indexed docs.
- Run `make cleanup-check` before creating cleanup PRs.
- Run `make diagnose-json` before handing off confusing runtime failures so
  the next agent has structured status, log summaries, and artifact paths.
