# Execution Plan: harness-completion

Date: 2026-05-03
Status: Completed

## Goal

Close the identified harness gaps while keeping `make verify` deterministic and
permission-free.

## Scope

- Add feature-class plan scaffolding, adapter fixture manifest validation,
  structured JSON diagnostics, privacy-redacted correction candidate export,
  optional PR/check review status, and installed Chrome bridge smoke.
- Expand beta validation for fake permission scenarios, Chrome bridge heartbeat
  and posting transitions, desktop/mobile rendering, and UI workflow probes.
- Strengthen active-plan, adapter-fixture, and architecture-flow harness lints.
- Update runtime, reliability, quality, operating, architecture, and harness
  docs for the new commands and evidence.

## Non-Goals

- Public notarization, installer distribution, cloud storage, cloud inference,
  or CI dependence on live macOS or Chrome extension permissions.

## Acceptance Criteria

- New public harness commands are exposed through `make`.
- `make verify` remains deterministic and permission-free.
- Real installed Chrome bridge evidence stays in a manual smoke command.
- Feedback-derived fixture candidates do not export raw titles or URLs.
- Harness linting mechanically enforces plan hygiene, adapter fixture
  registration, and core data-flow direction.

## Harness Impact

- Runtime commands and artifacts: added `make new-feature`,
  `make adapter-fixture-check`, `make chrome-bridge-smoke`,
  `make diagnose-json`, `make feedback-fixture-candidates`, and
  `make review-status`.
- Fixtures or fakes required for deterministic `make verify`: added
  `data/capture/adapter_fixture_manifest.json` and fake permission scenario
  coverage.
- UI validation: expanded beta desktop/mobile render checks and workflow probes
  for onboarding, setup guidance, and correction controls.
- Structured logs: added `diagnose.json` summaries and preserved existing
  runtime event/log paths.
- Privacy, permission: kept live Chrome/macOS validation manual, hashed
  correction title/URL candidates, and kept fake scenarios deterministic.
- Docs or harness checks: updated runtime, architecture, reliability, quality,
  operating, next-step, harness audit, harness feature, lint, and audit docs.

## Verification

- `make adapter-fixture-check`
- `make validate-beta`
- `make validate-ui`
- `make diagnose-json`
- `make feedback-fixture-candidates`
- `make review-status`
- `make cleanup-check`
- `python3 -m unittest discover -s tests`
- `make verify`

## Progress Log

- 2026-05-03: Implemented harness completion commands, fixtures, lints, docs,
  beta validation expansion, and deterministic tests.
- 2026-05-03: Fixed a shell heredoc issue in UI validation and moved beta
  workflow assertions into the reusable render checker.

## Handoff Notes

`make verify` passed. `make chrome-bridge-smoke` remains a manual real-machine
command for an installed Chrome extension and was not run as part of
deterministic verification.
