# Execution Plan: Dogfood Beta Harness

Date: 2026-04-27
Status: Completed

## Goal

Make IntentOS runnable as a dogfood beta: a local menu bar app launches a local
service, the service stores activity in SQLite, Chrome metadata can enter
through a local bridge, the dashboard reads service APIs, and users can pause,
delete data, and correct labels without manual imports.

## Scope

- Add a standard-library Python beta service with SQLite persistence, local HTTP
  APIs, daily review generation, privacy filtering, corrections, pause/resume,
  retention cleanup, and delete-local-data support.
- Add deterministic fake Chrome extension fixtures plus a Chrome MV3 extension
  shell that posts bounded tab metadata to the local service.
- Add beta harness commands for dev, status, stop, validation, and local Swift
  menu bar packaging.
- Add a minimal Swift menu bar wrapper that starts/stops the Python beta
  service, opens the dashboard, pauses/resumes, deletes local data, opens
  diagnostics, and quits cleanly.
- Keep all beta verification deterministic and permission-free.

## Non-Goals

- Public distribution, notarization, auto-update, cloud sync, telemetry,
  authentication, billing, OCR, local LLM inference, website blocking, or
  scheduling automation.
- Capturing page bodies, cookies, tokens, clipboard contents, keystrokes, or raw
  screenshots.
- Safari/Arc extension support in this slice.

## Acceptance Criteria

- `make beta-dev` starts the beta service, UI, fake Chrome bridge seed, and
  optional live recorder with status recorded under `.harness/runtime/beta/`.
- `make beta-status` shows service, DB, capture, extension, pause, counts, and
  log paths.
- `make beta-stop` stops beta service/capture/UI processes.
- `make validate-beta` verifies APIs, SQLite persistence, privacy filtering,
  correction behavior, delete-local-data, and UI loading against a temp DB.
- `make package-beta` builds an unsigned local menu bar app when macOS Swift
  tools are available and skips with a clear message otherwise.
- `make verify` remains deterministic and permission-free.

## Harness Impact

- Runtime commands and artifacts: `make beta-dev`, `make beta-status`,
  `make beta-stop`, `make validate-beta`, and `make package-beta` write
  `.harness/runtime/beta/app.env`,
  `.harness/runtime/beta/intentos.sqlite`,
  `.harness/runtime/logs/beta-service.log`,
  `.harness/runtime/artifacts/beta-validation.json`, and
  `.harness/runtime/artifacts/beta-daily-review.json`.
- Fixtures or fakes: fake Chrome tab events, fixture DB rows, fake idle/long-gap
  metadata, and service API validation with a temp DB.
- UI validation: service-backed dashboard mode must load through local
  `beta-config.json` and expose correction controls.
- Structured logs: beta service, fake bridge, UI build, and runtime lifecycle
  events must be written under `.harness/runtime/logs/` and
  `.harness/runtime/logs/events.jsonl`.
- Privacy: keep local-only processing, 30-day retention, pause/resume, delete
  all local data, redaction/exclusions before persistence, no page bodies.
- Privacy, permission, and local-only behavior: no screenshots, no keylogging,
  no page bodies, no cookies, no cloud calls, and permission-dependent macOS
  live capture must stay outside deterministic validation.
- Docs or harness checks: update runtime, architecture, security, reliability, quality,
  feature contracts, next steps, Makefile, harness lint, and product verify.

## Verification

- `python3 -m unittest tests.test_beta_store tests.test_beta_service tests.test_beta_extension`
- `make validate-beta`
- `make package-beta`
- `make verify`

## Progress Log

- 2026-04-27: Plan created from dogfood beta product direction.
- 2026-04-27: Implemented local beta service, SQLite persistence, fake Chrome
  bridge, Chrome MV3 shell, service-backed UI corrections, beta harness
  commands, Swift packaging, deterministic tests, docs, screenshot evidence,
  and full `make verify` gate.
