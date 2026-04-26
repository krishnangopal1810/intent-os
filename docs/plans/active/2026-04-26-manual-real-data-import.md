# Execution Plan: Manual Real-Data Import

Date: 2026-04-26
Status: Active

## Goal

Let a user import local CSV or JSON activity records into the existing
`ActivityEvent` boundary, classify them through the current report path, and
inspect the resulting behavior summary in the UI.

## Context

IntentOS now has deterministic YouTube classification, generic multi-app
`ActivityEvent` classification, one-shot macOS metadata capture, bounded session
capture, replay artifacts, and a local UI. The next useful product step is to
process user-supplied historical data without requiring always-on capture,
ScreenCaptureKit, OCR, or a local model.

## Scope

- Define a small documented import schema for local CSV and JSON files.
- Add an import command that validates user records and converts them into
  local `ActivityEvent` JSONL.
- Replay imported events through the existing classifier and report output.
- Add deterministic import fixtures for valid rows, validation errors, privacy
  exclusions, and mixed app/browser/chat activity.
- Update the UI only if import artifacts add a new user-visible report source.
- Add structured runtime events for import validation, row counts, excluded
  rows, output paths, and replay status.
- Keep all processing local and deterministic in CI.

## Non-Goals

- Browser history database reads.
- ChatGPT export parsing.
- Always-on capture.
- Cloud sync, cloud inference, or telemetry.
- ScreenCaptureKit, OCR, or model-backed classification.
- Editing imported records in the UI.

## Acceptance Criteria

- A user can run a documented command against a local CSV or JSON file and get
  inspectable `ActivityEvent` JSONL plus report artifacts.
- Invalid rows fail with actionable local errors that do not write partial
  misleading reports.
- Privacy exclusions and redaction apply before imported records are persisted
  to runtime artifacts.
- Deterministic fixtures cover representative records from coding, ChatGPT,
  YouTube, LinkedIn/X/Instagram, WhatsApp/Slack, docs, and admin websites.
- `make verify` covers import conversion, validation, replay, and any UI
  behavior with no live user data.

## Verification

- `python3 -m unittest discover -s tests`
- Import CLI smoke command against deterministic CSV and JSON fixtures.
- `make validate-ui` if UI artifacts change.
- `make check-ui-screenshot` if rendered UI evidence changes.
- `make verify`

## Implementation Notes

Reuse `ActivityEvent`, capture privacy helpers, JSONL persistence, and replay.
Do not introduce a second event model. Keep importer modules below the same
source-adapter -> event-boundary -> classifier -> reporting direction enforced
by `scripts/harness/lint.py`.

## Progress Log

- 2026-04-26: Plan created after completing the bounded live capture session
  timeline.
- 2026-04-26: Clarified runtime data modes before import work: `make dev` is
  fixture-only and clears live artifacts, while `make dev-live` runs a fresh
  bounded macOS session before serving the UI.

## Handoff Notes

Start with fixture-backed CSV/JSON import. Add any required harness support
before relying on manual inspection, especially validation artifacts, runtime
logs, and screenshot evidence for user-visible UI changes.
