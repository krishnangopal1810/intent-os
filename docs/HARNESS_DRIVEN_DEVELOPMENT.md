# Harness-Driven Development

IntentOS treats the harness as part of the product, not as after-the-fact test
coverage. Product feedback is only complete when the repo can catch the same
class of problem again without relying on memory, screenshots in chat, or
manual taste checks.

## Core Rule

Every product feedback item must have one of three outcomes before the related
work is considered done:

- An existing harness check already covers it, and the handoff names the exact
  command, fixture, probe field, or artifact that would fail.
- A new or updated harness check covers it in the same change as the product
  fix.
- The feedback is intentionally manual for now, with the reason documented in
  the active plan or [QUALITY.md](QUALITY.md), plus the nearest deterministic
  proxy check.

If none of those is true, the work is incomplete. Missing harness capability is
a product blocker.

## Feedback Loop

When humans give product feedback, first translate it into a harness question:
"What local check would have failed before this reached review?"

Then update the repo in this order:

1. Record the product expectation in the brief, spec, active plan, or relevant
   quality doc.
2. Pick the harness layer that can catch the regression deterministically.
3. Add or update a fixture, probe, lint rule, unit test, smoke, or rendered UI
   check before relying on manual validation.
4. Add a negative test or synthetic failing fixture when the behavior is easy
   to regress.
5. Run the focused harness command and the normal gate.
6. Name the harness evidence in the handoff.

Product polish, copy tone, density, navigation, setup guidance, classification
examples, privacy behavior, and service failures are all harness material when
they can be observed locally.

## Harness Layers

Use the smallest deterministic layer that catches the feedback:

- Rendered UI feedback: update `scripts/product/ui-render-probe.js`,
  `scripts/product/render-ui-check.py`, UI fixtures, or screenshot evidence.
- User-facing copy feedback: update `data/ui/visible_copy_policy.json` or a
  specific rendered text assertion.
- Workflow feedback: add a service-backed beta scenario through
  `scripts/product/validate_beta.py` / `scripts/product/beta_validation/` or a
  fixture workflow in `scripts/product/validate-ui.sh`.
- Classifier feedback: promote examples into `data/activity/evaluation_set.json`
  or the relevant evaluation fixture before classifier work is complete.
- Runtime or permission feedback: add deterministic service, CLI, fake
  permission, or adapter fixture coverage.
- Privacy feedback: update security/live-capture docs and add lint, fixture, or
  replay coverage that preserves the local-only contract.
- Documentation feedback: update docs and add or extend `harness-check`,
  `harness-lint`, or audit rules when drift should be mechanically visible.

Do not create a parallel manual checklist when the harness can express the
expectation. Add the harness rule instead.

## Definition Of Done

A product feedback fix is done only when:

- The feedback has a durable product expectation in docs or a plan.
- The harness covers the regression, or the manual exception is documented.
- The focused command for the changed layer passes.
- `make verify` passes, or a concrete blocker is recorded.
- The final handoff names what will fail next time if the regression returns.

For UI-facing feedback, browser-backed validation is required when Chrome or
Chromium is available locally, and CI requires rendered UI checks.
