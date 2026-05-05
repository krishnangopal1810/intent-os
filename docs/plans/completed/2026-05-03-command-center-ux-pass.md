# Execution Plan: command-center-ux-pass

Date: 2026-05-03
Status: Completed

## Goal

Make the dashboard feel like a production-grade operating surface: the first
screen should immediately answer what to do now, what to trust or correct, and
what tonight's review will ask.

## Scope

- Add a compact command center above the main review cards.
- Surface "Now", "Trust", and "Tonight" as action-oriented shortcuts.
- Reuse workspace-only scrolling for command shortcuts.
- Tighten the narrow layout so navigation and status consume less vertical
  space.
- Extend validation so the command center is present and rendered.

## Non-Goals

- No backend, schema, classifier, capture, menu bar, or notification changes.
- No new automation, blocking, scheduling, streaks, or cloud behavior.
- No change to the core daily-loop API contract.

## Acceptance Criteria

- The first viewport shows a clear command center with Now, Trust, and Tonight.
- Command links move within the workspace pane without hiding navigation.
- Mobile/narrow layouts keep navigation compact and readable.
- UI and beta validation pass with desktop and mobile render probes.
- `make verify` passes.

## Harness Impact

- Runtime commands and artifacts: existing UI and beta validation cover this
  frontend slice.
- Fixtures or fakes required for deterministic `make verify`: none.
- UI validation or screenshot evidence: refresh checked-in screenshot and add
  command-center DOM/render checks.
- Structured logs, metrics, or diagnostics: none.
- Privacy, permission, or local-only constraints: no data changes.
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

- 2026-05-03: Plan created from broad UX feedback to make the dashboard feel
  more compelling and production-grade.
- 2026-05-03: Added the first-viewport command center, workspace-only command
  shortcuts, compact narrow navigation, and validation probes for Now, Trust,
  and Tonight.
