# Execution Plan: sticky-daily-loop

Date: 2026-05-03
Status: Completed

## Goal

Make IntentOS sticky by adding a dogfood beta loop where the user sets today's
focus and thing to avoid, then completes an evening review that compares intent
against captured behavior and reinforces classification accuracy improvements.

## Scope

- Add local SQLite persistence for daily intents and review check-ins.
- Add service APIs for daily-loop state, daily intent upsert, and review
  check-in upsert.
- Add the intent and evening review workflow to the existing beta dashboard.
- Add menu bar entries and status labels for intent due and review due.
- Extend beta/UI validation, menu tests, docs, and screenshot evidence.

## Non-Goals

- No OS notification permission requests.
- No cloud sync, telemetry, scheduling automation, or calendar integration.
- No streaks, score chasing, blocking, public installer work, screenshots,
  page bodies, or keylogging.
- No new frontend framework or external dependency.

## Acceptance Criteria

- `GET /api/daily-loop?date=YYYY-MM-DD` returns intent, review check-in,
  prompt due state, correction count, low-confidence count, and plan-vs-actual
  summary.
- `POST /api/daily-intent` and `POST /api/review-checkin` upsert by date and
  stay local to the beta SQLite DB.
- The dashboard shows a compact Today's Intent module above the Action Queue,
  with missing-intent, intent-set, review-due, and review-complete states.
- The menu bar app exposes Set Today's Intent and Open Evening Review, and its
  status can show Intent Due or Review Due.
- Delete Local Data clears daily intents and review check-ins.
- No OS notifications, blocking, calendar integration, cloud sync, telemetry,
  screenshots, page bodies, or keylogging are added.

## Harness Impact

- Runtime commands and artifacts: existing `make beta-dev`, `make
  validate-beta`, `make validate-ui`, and `make verify` cover this slice; beta
  validation writes `beta-validation.json` and `beta-daily-review.json`.
- Fixtures or fakes required for deterministic `make verify`: use existing beta
  fixture rows plus API-driven fake intent and review check-in state in
  `scripts/product/validate-beta.sh`.
- UI validation or screenshot evidence: update `web/`,
  `scripts/product/validate-ui.sh`, beta render probes, and refresh
  `docs/assets/screenshots/intent-os-ui.png`.
- Structured logs, metrics, or diagnostics: no new long-running process; daily
  loop state is inspectable through local service APIs and existing beta status
  diagnostics.
- Privacy, permission, or local-only constraints: persist only user-entered
  focus/avoid/reflection text and derived metadata in local SQLite; delete all
  with existing delete-local-data.
- Docs or harness checks to update: update product/runtime/design/quality docs,
  Swift menu tests, beta validation, and this plan.

## Verification

- Focused beta unit tests passed with
  `python3 -m unittest discover -s tests -p 'test_beta_*.py'`.
- Syntax checks passed with `python3 -m py_compile` for the changed beta
  service, store, review, daily-loop, daily-state, schema, and harness modules.
- `make update-ui-screenshot` passed and refreshed
  `docs/assets/screenshots/intent-os-ui.png`.
- `make validate-beta` passed with intent POST, daily-loop readback, completed
  evening check-in, and desktop/mobile browser render probes.
- `make validate-ui` passed with the sticky-loop DOM bindings and
  desktop/mobile render probes.
- `make verify` passed.

## Progress Log

- 2026-05-03: Plan created from sticky daily loop proposal.
- 2026-05-03: Added local SQLite intent/check-in persistence, daily-loop
  service APIs, dashboard module, menu bar status affordances, focused tests,
  and harness token checks.
- 2026-05-03: Split sticky-loop state, read-model, and schema helpers into
  dedicated beta modules to keep files below the repo legibility limit.
- 2026-05-03: Refreshed UI screenshot evidence and passed the full verification
  gate.
