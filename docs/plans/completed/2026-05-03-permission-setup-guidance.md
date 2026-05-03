# Execution Plan: permission-setup-guidance

Date: 2026-05-03
Status: Completed

## Goal

Make beta permission repair actions explain exactly what to do after opening
macOS settings or Chrome extension setup.

## Context

The current menu bar and dashboard setup actions open the relevant system page
but do not tell a dogfood user which checkbox, app entry, or Chrome install
step to complete afterward. This leaves first-run setup ambiguous even though
the product already has permission probes and onboarding state.

## Scope

- Add target-specific setup guidance to the beta permission/open-settings API.
- Show the guidance in the dashboard onboarding panel after a setup action.
- Show the same guidance from the native menu bar after opening a target.
- Cover the deterministic API shape with tests and beta validation.
- Update durable docs/quality notes for the improved permission UX.

## Non-Goals

- Public notarized installer or automatic permission granting.
- Making the Chrome bridge required for first beta value.
- Adding new capture sensors or changing privacy defaults.

## Acceptance Criteria

- Accessibility, Automation, Chrome bridge, and diagnostics actions return
  clear next steps and a verification instruction.
- Dashboard onboarding does not dead-end after opening a settings target.
- Menu bar setup actions surface the same steps without requiring the user to
  read logs.
- `make validate-beta` and targeted tests cover the new guidance contract.

## Harness Impact

- Runtime commands and artifacts: `make validate-beta` should record the
  guidance payload in `beta-validation.json`.
- Fixtures or fakes required for deterministic `make verify`: none beyond the
  existing fake permission mode.
- UI validation or screenshot evidence: dashboard onboarding UI changes require
  `make validate-ui`; refresh checked-in screenshot only if rendered fixture UI
  changes.
- Structured logs, metrics, or diagnostics: no new log channel.
- Privacy, permission, or local-only constraints: preserve local-only
  metadata-only capture; guidance must not imply cloud sync or page-body access.
- Docs or harness checks to update: product/runtime docs or quality notes if
  the known UX gap changes.

## Verification

- `python3 -m unittest discover -s tests -p 'test_beta_permissions.py'`
- `python3 -m unittest discover -s tests -p 'test_beta_service.py'`
- `make validate-beta`
- `make validate-ui`
- `make check-ui-screenshot`
- `make package-beta`
- `make verify`

## Implementation Notes

Keep the source of setup instructions centralized in the beta permission
module so the service, dashboard, validation, and native wrapper do not drift.

## Progress Log

- 2026-05-03: Plan created.
- 2026-05-03: Reproduced the UX gap from the current permission API and menu
  bar wiring: settings pages open without follow-up instructions.
- 2026-05-03: Added centralized setup guidance, dashboard rendering, menu bar
  alerts, deterministic API tests, beta validation checks, and refreshed UI
  screenshot evidence.
- 2026-05-03: `make verify` reached product validation once, then failed only
  at stale screenshot evidence; after refresh, rerun failed in `harness-lint`
  because `intentos/beta/store.py` is 343 lines against the 320-line limit.
- 2026-05-03: Repaired overlapping beta status/test regressions so
  permission tests and `make validate-beta` pass again; `make harness-lint`
  then reported only the unrelated `intentos/beta/store.py` size limit.
- 2026-05-03: Split SQLite health helpers out of `store.py`, reran
  `make verify`, and completed the plan with the full gate passing.
- 2026-05-03: Follow-up fix: native menu bar `Run Permission Check` now shows
  a readiness/permission result alert instead of silently discarding the API
  response.
- 2026-05-03: Follow-up fix: the permission result alert now includes exact
  Chrome bridge install steps and the local unpacked extension path when the
  bridge is unchecked.

## Handoff Notes

Implemented and verified. `make verify` passes for the completed slice.
