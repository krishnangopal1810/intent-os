# Execution Plan: intent-contract-preview

Date: 2026-05-03
Status: Completed

## Goal

Make the daily intent form explain how natural-language focus and avoid text
becomes a trackable daily review contract.

## Scope

- Add a live tracking-contract preview to the Today's Intent form.
- Show the concrete focus signal, avoid signal, and evening review question
  derived from the current input text.
- Tighten saved intent labels so plan-vs-actual reads as protected focus,
  avoided surface, accuracy, and handoff.
- Extend UI and beta harness checks for the new contract binding.

## Non-Goals

- No new classifier behavior, model inference, scheduling, notifications, or
  persistence schema changes.
- No change to the daily-loop API contract.
- No new frontend dependency.

## Acceptance Criteria

- The missing-intent form visibly answers what the user's natural language will
  help track before the user saves it.
- The preview updates while typing and remains stable on desktop/mobile.
- Validation fails if the tracking-contract DOM binding disappears.
- `make validate-beta`, `make validate-ui`, and `make verify` pass.

## Harness Impact

- Runtime commands and artifacts: existing beta and UI validation paths cover
  this frontend-only slice.
- Fixtures or fakes required for deterministic `make verify`: no new fixtures.
- UI validation or screenshot evidence: update UI token checks and refresh the
  checked-in screenshot if rendered evidence changes.
- Structured logs, metrics, or diagnostics: none.
- Privacy, permission, or local-only constraints: no new data capture; the form
  preview is client-side copy derived from local input values.
- Docs or harness checks to update: update this plan, design/runtime notes as
  needed, and harness token checks.

## Verification

- Syntax checks passed with `node --check web/app.js`,
  `bash -n scripts/product/validate-ui.sh scripts/product/validate-beta.sh`,
  and `python3 -m py_compile` for the changed Python harness modules.
- `make update-ui-screenshot` passed.
- `make validate-ui` passed with desktop and mobile render probes.
- `make validate-beta` passed with service-backed daily-loop render probes.
- `make verify` passed.

## Progress Log

- 2026-05-03: Plan created from product feedback on the intent form.
- 2026-05-03: Added the live tracking-contract preview, updated saved-state
  labels, restarted the beta runtime for inspection, refreshed screenshot
  evidence, and passed verification.
