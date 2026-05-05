# Execution Plan: ui-ux-harness-guardrails

Date: 2026-05-04
Status: Completed

## Goal

Make recurring manual product feedback fail automatically in the local harness:
action-first daily review, lower first-screen density, friendly visible copy,
user-facing daily plan language, visible section navigation, permission and
service recovery guidance, live intent-preview clarity, fewer unguarded
classifier feedback regressions, and no clipped or scrambled text.

## Scope

- Extend rendered desktop and mobile UI probes with text layout diagnostics.
- Add a shared render probe injector used by fixture and beta validation.
- Validate a versioned probe schema covering copy policy, first viewport,
  default density, text layout, section navigation, intent preview, service
  state, and workflow probes.
- Add a visible-copy policy for recurring forbidden user-facing phrases and raw
  developer error leakage.
- Add default-surface density budgets for visible cards, stats, panels, and
  supporting-detail disclosure.
- Ensure Activity navigation opens the evidence drawer without scrolling the
  whole document or hiding navigation.
- Apply the same guardrails to fixture UI validation and beta UI validation.
- Cover fixture-default, fixture-long-text, beta-ready, beta-service-stale,
  beta-empty, beta-intent-missing, and beta-setup-needed rendered scenarios.
- Keep feedback-derived classifier examples covered by the activity evaluation
  set and keep promoted feedback tied to labeled activity fixtures.
- Document the new harness quality bar.

## Non-Goals

- No broad product UI redesign in this slice.
- No backend, classifier, SQLite, capture, menu bar, or notification changes.
- No visual diffing service or cloud telemetry.
- No screenshots of private user data or live macOS permission dependencies.

## Acceptance Criteria

- `make validate-ui` fails if visible text is cut off or clipped.
- `make validate-ui` fails if the default dashboard exposes dense supporting
  metrics or raw evidence instead of keeping them behind disclosure.
- `make validate-ui` and `make validate-beta` share the same rendered probe
  injector and schema validator.
- `make validate-beta` uses the same copy, layout, density, service-state,
  workflow, and intent-preview guardrails.
- Stale service and empty database renders show product-facing recovery
  language instead of raw fetch/developer errors or "No rows".
- Harness lint requires the UX guardrail probes to remain wired.
- Product quality docs mention the automated visual UX checks.
- `make verify` passes.

## Harness Impact

- Runtime commands and artifacts: `make validate-ui`, `make validate-beta`, and
  `make verify` emit richer rendered UI probe JSON artifacts. CI runs with
  `INTENTOS_UI_REQUIRE_BROWSER=1`; local runs may skip rendered browser checks
  only when the browser is not required.
- Fixtures or fakes required for deterministic `make verify`: none; existing
  fixture and beta fake-service data drive the probes.
- UI validation or screenshot evidence: rendered desktop/mobile DOM probes now
  measure copy policy, density, first viewport, text clipping, Activity
  navigation state, service recovery, workflow controls, and intent preview.
- Structured logs, metrics, or diagnostics: validation JSON includes default
  density, text layout, copy, section navigation, service, workflow, and intent
  preview diagnostics for debugging failures.
- Privacy, permission, or local-only constraints: checks run locally against
  generated artifacts and the fake beta service; no new data leaves the machine.
- Docs or harness checks to update: completed plan, runtime/design/quality
  notes, render checker, shared probe injector, UI validation, beta validation,
  and harness lint.

## Verification

- Passed: `python3 -m py_compile scripts/product/render-ui-check.py scripts/product/inject-ui-render-probe.py scripts/product/render-ui-browser.py scripts/harness/lint.py`
- Passed: `bash -n scripts/product/validate-ui.sh scripts/product/validate-beta.sh`
- Passed: `python3 -m unittest discover -s tests -p 'test_render_ui_check.py'`
- Passed: `make harness-lint`
- Passed: `make harness-check`
- Passed: `INTENTOS_UI_REQUIRE_BROWSER=1 make validate-ui`
- Passed: `INTENTOS_UI_REQUIRE_BROWSER=1 make validate-beta`
- Passed: `make verify`

## Progress Log

- 2026-05-04: Plan created from feedback that scrambled text and cognitive load
  should be automatically caught by the harness.
- 2026-05-04: Added shared rendered UI probes for first-screen density, guarded
  text cut-off checks, closed-detail visibility, copy policy, and workflow
  scenarios.
- 2026-05-04: Reduced the default action deck to one visible next-step card so
  the first viewport avoids partially clipped action rows.
- 2026-05-04: Expanded the guardrail slice to cover visible-copy policy,
  long-text fixture rendering, stale service recovery, empty beta state,
  missing-intent preview updates, setup-guidance workflow clicks, and
  feedback-derived activity classifier examples.
- 2026-05-04: Split beta scenario renders onto dedicated HTML entrypoints so
  stale-service and empty-state probe configs cannot race each other during
  screenshot and DOM capture.
