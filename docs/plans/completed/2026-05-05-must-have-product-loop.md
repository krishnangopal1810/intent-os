# Execution Plan: must-have-product-loop

Status: Completed

## Goal

Turn the beta dashboard from an activity report into a daily intent coach. The
first product moment should explain: what the user planned, what actually
happened, what IntentOS learned, and the one next block to run.

## Scope

- Extend `/api/daily-loop` with intent contract, next block, correction reward,
  and richer plan-vs-actual review data.
- Add a local `/api/weekly-patterns` read model derived from SQLite activity,
  correction, and daily-loop state.
- Rework the first screen around a plan-vs-actual coach hero with 2-3 inline
  receipts, one next-block recommendation, a visible intent contract, and
  collapsed evidence/weekly details.
- Update the Swift menu bar app so status labels and menu anchors match the
  daily coach loop.
- Update unit tests, beta validation, UI render probes, visible-copy policy,
  docs, and screenshot evidence.

## Non-Goals

- No cloud sync, telemetry, screenshots, keylogging, page bodies, calendar
  integration, blocking, scheduling automation, OS notifications, or public
  installer work.
- No model-backed natural-language inference in this slice; contract extraction
  stays deterministic and inspectable.
- No streaks, scores, or gamified reward loops.

## Acceptance Criteria

- `/api/daily-loop?date=YYYY-MM-DD` includes `intent_contract`, `next_block`,
  `correction_reward`, and plan-vs-actual receipts/verdict.
- `/api/weekly-patterns?week_start=YYYY-MM-DD` returns three local weekly
  pattern cards plus a plain-language narrative.
- The default beta viewport leads with the daily contract review and one
  next-block action, while metrics, queues, and replay evidence stay collapsed.
- Empty states guide the user to work normally for 20 minutes and never expose
  raw "No rows", fetch, SQLite, harness, or developer copy.
- Menu bar status labels include Intent Due, Review Ready, Focus Holding, Avoid
  Leaking, Needs Correction, Paused, and Running; menu items open Set Intent,
  Evening Review, Next Block, Weekly Patterns, Pause, Resume, and Diagnostics.
- Runtime commands and artifacts remain deterministic and local-only.
- Fixtures or fakes cover intent contract, next-block, correction reward, weekly
  patterns, and empty-day preview behavior.
- UI validation fails when the coach hero, next block, daily intent module,
  weekly disclosure, or evidence disclosure disappears.
- Structured logs and validation JSON include the new beta loop and weekly
  payloads without raw personal content beyond existing fixture metadata.
- Privacy, permission, and local-only behavior remain unchanged.
- Docs or harness checks name the new product loop and guard against regression.

## Harness Impact

- Runtime commands and artifacts: extend `make validate-beta`, refreshed UI
  screenshot evidence, and existing beta render artifacts.
- Fixtures or fakes: reuse deterministic Chrome bridge events and add unit
  fixtures for focus, leak, trust-gap, no-data, and weekly aggregation cases.
- UI validation: add DOM/probe assertions for the coach hero, next block, weekly
  patterns, first-viewport density, friendly empty states, and visible copy.
- Structured logs: write the daily-loop and weekly-pattern API results into
  beta validation JSON for inspection.
- Privacy, permission: keep all state local in SQLite and do not add
  screenshots, page bodies, notifications, blocking, or cloud calls.
- Docs or harness checks: update product/design/architecture/quality docs and
  harness lint expectations for the new endpoint and UI bindings.

## Verification

- `python3 -m unittest tests.test_beta_daily_loop tests.test_beta_service tests.test_beta_menu_app tests.test_render_ui_check`
- `make update-ui-screenshot`
- `make validate-ui`
- `make validate-beta`
- `make verify`

## Progress Log

- 2026-05-05: Created active plan and mapped implementation to API, UI,
  menu-bar, harness, docs, and screenshot updates.
- 2026-05-05: Added deterministic intent contract, plan-vs-actual receipts,
  next-block recommendation, correction reward, weekly patterns endpoint, coach
  UI, menu anchors/status labels, and harness guards for density, copy,
  navigation, empty states, and required DOM bindings.
- 2026-05-05: Focused unit tests, `make validate-ui`, and `make validate-beta`
  passed; checked-in UI screenshot evidence was refreshed.
