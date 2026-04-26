# Agent Operating Model

IntentOS should be built so Codex can drive changes end to end with minimal
hidden human coordination.

## Roles

- Humans specify product direction, acceptance criteria, and judgment calls.
- Codex updates specs, implementation, tests, docs, scripts, and follow-up fixes.
- Review feedback should become either code, tests, docs, or harness rules.

## Standard Change Loop

1. Read `AGENTS.md`, product docs, architecture docs, and the active plan.
2. Validate the current repo state.
3. Reproduce or specify the requested behavior.
4. Implement the smallest complete slice.
5. Run product and harness verification.
6. Capture runtime evidence when the app has UI or service behavior.
7. Update docs, quality notes, and the active plan.
8. Prepare a PR when requested.

## Review Loop

When working on a PR or review feedback:

- Fetch unresolved review threads and CI status.
- Address actionable findings in code, tests, or docs.
- Reply with the exact change made and verification run.
- Re-run failing checks before handing off.
- Convert repeated review themes into docs or harness checks.

## Merge Criteria

A change is ready only when:

- Acceptance criteria are satisfied.
- `make verify` passes, or the blocker is explicitly documented.
- Runtime/UI validation evidence exists for UI behavior once a UI exists.
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
