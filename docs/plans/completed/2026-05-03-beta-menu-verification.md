# Execution Plan: beta-menu-verification

Date: 2026-05-03
Status: Completed

## Goal

Verify and harden every IntentOSBeta menu option so the menu behaves safely
across running, stopped, and stale beta runtime states.

## Scope

- Audit menu item wiring in `macos/IntentOSBeta/IntentOSBeta.swift`.
- Make dashboard, start/restart/stop, setup, pause/resume, delete-data,
  diagnostics, and quit actions handle stale runtime state predictably.
- Keep destructive data deletion behind explicit confirmation.
- Add deterministic tests for menu labels, action wiring, and runtime isolation
  assumptions.
- Run beta service validation and package the Swift menu app.

## Non-Goals

- Notarization, installer distribution, or changing macOS permission policy.
- New capture sensors or Chrome extension behavior.

## Acceptance Criteria

- Every IntentOSBeta menu item has deterministic behavior in running, stopped,
  and stale runtime states.
- Destructive local data deletion requires explicit confirmation.
- Menu status labels reflect beta service, dashboard, recorder, and paused
  states without stale URLs.
- Tests or harness checks cover menu wiring and runtime isolation assumptions.

## Harness Impact

- Runtime commands and artifacts: exercise `make beta-status`,
  `make validate-beta`, and `make package-beta`.
- Fixtures or fakes required for deterministic `make verify`: use existing beta
  service and permission fixtures; add menu fixtures only if implementation
  requires them.
- UI validation: service-backed beta dashboard render checks should remain
  covered by `make validate-beta`.
- Structured logs: keep beta service, native recorder, and menu diagnostics
  visible through existing runtime logs.
- Privacy, permission: preserve local-only metadata capture and confirmation
  before delete-local-data.
- Docs or harness checks: update runtime, operating, or quality docs if menu
  behavior or verification changes.

## Verification

- `python3 -m pytest tests/test_beta_menu_app.py tests/test_beta_service.py tests/test_beta_permissions.py`
- `make package-beta`
- `make validate-beta`
- `make beta-status`

## Progress Log

- 2026-05-03: Plan created after audit found stale URL/service handling and
  destructive-action safety gaps in the native menu wrapper.
- 2026-05-03: Hardened dashboard/start/restart/stop behavior, service retry
  handling, delete confirmation, local-calendar pause-until-tomorrow, and
  runtime-dir isolation for beta-stop.
- 2026-05-03: Added static menu-wrapper tests and expanded beta validation to
  cover Accessibility, Automation, and Chrome extension setup targets.
- 2026-05-03: `python3 -m pytest tests/test_beta_menu_app.py
  tests/test_beta_service.py tests/test_beta_permissions.py`, `make
  package-beta`, `make validate-beta`, `make beta-status`, and `make verify`
  passed.

## Handoff Notes

Implemented and verified. The live dogfood beta remained running on the
original service/UI PIDs during validation.
