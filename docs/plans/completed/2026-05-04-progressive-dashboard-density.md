# Execution Plan: progressive-dashboard-density

Date: 2026-05-04
Status: Completed

## Goal

Reduce dashboard cognitive load by making the default surface action-first and
moving secondary metrics, queues, and raw evidence into progressive disclosure.

## Scope

- Keep the command center, daily intent, and next-step list visible by default.
- Shorten the action list so it reads as a small set of decisions.
- Move metrics, review queues, and evidence reports behind expandable sections.
- Preserve section navigation by opening the relevant disclosure before
  scrolling to Timeline or Activity.
- Update validation for the less dense default layout.

## Non-Goals

- No backend, classifier, schema, capture, menu bar, or notification changes.
- No new data model or daily-loop API changes.
- No redesign of correction controls beyond where they appear.

## Acceptance Criteria

- The first pass of the dashboard is less dense and focused on the next action.
- Supporting metrics, queues, and raw replay evidence remain available.
- Timeline and Activity navigation still works from the sidebar.
- Desktop and mobile UI validation pass.
- `make verify` passes.

## Harness Impact

- Runtime commands and artifacts: existing UI and beta validation commands cover
  this frontend-only layout change.
- Fixtures or fakes required for deterministic `make verify`: none.
- UI validation or screenshot evidence: refresh checked-in screenshot and
  update render checks for the shortened next-step list.
- Structured logs, metrics, or diagnostics: none.
- Privacy, permission, or local-only constraints: no data, permission, cloud,
  or telemetry behavior changes.
- Docs or harness checks to update: active plan, design notes, UI validation,
  beta validation, and harness lint.

## Verification

- Passed: `node --check web/app.js`
- Passed: `python3 -m py_compile scripts/product/ui_validation.py scripts/product/render-ui-check.py scripts/harness/lint.py`
- Passed: `bash -n scripts/product/validate-ui.sh scripts/product/validate-beta.sh`
- Passed: `make update-ui-screenshot`
- Passed: `make validate-ui`
- Passed: `make validate-beta`
- Passed: `make verify`

## Progress Log

- 2026-05-04: Plan created from feedback that the dashboard carries too much
  cognitive load.
- 2026-05-04: Shortened the visible next-step list and moved metrics, focus
  queues, and raw evidence behind supporting-detail disclosures.
