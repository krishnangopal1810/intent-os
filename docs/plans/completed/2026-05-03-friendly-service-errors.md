# Execution Plan: friendly-service-errors

Date: 2026-05-03
Status: Completed

## Goal

Replace developer-facing empty/error language in the beta dashboard with clear
user-facing recovery guidance.

## Scope

- Add a top-level user-facing notice for local service or data loading problems.
- Route beta service load failures through that notice instead of raw fetch
  errors in the main headline.
- Replace empty-state strings such as "No rows" and "Check the local service"
  with plain product language.
- Extend UI harness checks for the new notice binding.

## Non-Goals

- No backend service changes.
- No new persistence, telemetry, notifications, or installer behavior.
- No changes to classifier behavior or capture policy.

## Acceptance Criteria

- A stale or unavailable beta service shows a friendly explanation at the top
  of the dashboard.
- Empty activity states avoid developer phrases such as "No rows" and "Check
  the local service".
- Validation fails if the service notice binding disappears.
- `make validate-ui`, `make validate-beta`, and `make verify` pass.

## Harness Impact

- Runtime commands and artifacts: existing UI and beta validation cover this
  frontend slice.
- Fixtures or fakes required for deterministic `make verify`: none.
- UI validation or screenshot evidence: update DOM/token checks and refresh the
  checked-in screenshot after UI source changes.
- Structured logs, metrics, or diagnostics: none.
- Privacy, permission, or local-only constraints: no new data capture.
- Docs or harness checks to update: update this plan and relevant UI/runtime
  docs.

## Verification

- Syntax checks passed with `node --check web/app.js`,
  `bash -n scripts/product/validate-ui.sh scripts/product/validate-beta.sh`,
  and `python3 -m py_compile` for changed Python harness modules.
- A manual stale-service render using an invalid beta service URL showed the
  top-level "Reconnect IntentOS" notice and no "No rows" or "Check the local
  service" copy.
- `make update-ui-screenshot` passed.
- `make validate-ui` passed with desktop and mobile render probes.
- `make validate-beta` passed with desktop and mobile render probes.
- `make verify` passed.

## Progress Log

- 2026-05-03: Plan created from UX feedback on developer-facing error copy.
- 2026-05-03: Added a user-facing service notice, routed beta load failures
  through it, replaced developer empty-state copy, refreshed screenshot
  evidence, and passed verification.
