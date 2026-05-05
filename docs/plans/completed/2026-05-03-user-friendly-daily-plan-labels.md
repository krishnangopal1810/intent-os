# Execution Plan: user-friendly-daily-plan-labels

Date: 2026-05-03
Status: Completed

## Goal

Replace internal sticky-loop, beta, dogfood, and tracking-contract wording in
the daily intent UI with plain user-facing language.

## Scope

- Rename the visible daily-loop eyebrow from "Sticky loop" to daily planning
  language.
- Replace empty/unavailable copy that mentions beta or dogfood with direct
  recovery guidance.
- Rename "Tracking contract" and its save action so the user understands how
  the text will help tonight's review.
- Translate setup/status labels that expose implementation terms such as
  recorder, bridge, service, and database.
- Update design and harness checks so the dashboard keeps customer-facing copy.

## Non-Goals

- No persistence schema, API, classifier, capture, notification, installer, or
  menu bar behavior changes.
- No rename of internal beta harness commands, files, or source modules.

## Acceptance Criteria

- The dashboard does not show "Sticky loop", "Beta only", "dogfood beta",
  "Tracking contract", "Local beta service", or "SQLite daily timeline".
- The daily intent module reads as a daily plan and evening review workflow.
- Setup/status labels use product language for app access, browser detail,
  local storage, and activity capture.
- UI and harness validation pass.

## Harness Impact

- Runtime commands and artifacts: existing UI and beta validation cover this
  frontend slice.
- Fixtures or fakes required for deterministic `make verify`: none.
- UI validation or screenshot evidence: refresh checked-in UI screenshot and
  update required text tokens.
- Structured logs, metrics, or diagnostics: none.
- Privacy, permission, or local-only constraints: no new data capture.
- Docs or harness checks to update: `docs/DESIGN.md`, `docs/APP_RUNTIME.md`,
  UI validation scripts, and harness lint.

## Verification

- Syntax checks passed with `node --check web/app.js`,
  `bash -n scripts/product/validate-ui.sh scripts/product/validate-beta.sh`,
  and `python3 -m py_compile` for changed Python harness modules.
- `make update-ui-screenshot` passed.
- `make validate-ui` passed with desktop and mobile render probes.
- `make validate-beta` passed with service-backed desktop and mobile render
  probes.
- `make verify` passed.
- Post-completion `make harness-check` and `make harness-lint` passed.

## Progress Log

- 2026-05-03: Plan created from product feedback on internal daily-loop labels.
- 2026-05-03: Replaced visible sticky-loop, beta, dogfood, tracking-contract,
  service, database, recorder, and bridge wording with product-facing daily
  plan/review copy; refreshed screenshot evidence and passed verification.
