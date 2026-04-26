# Execution Plan: Live Browser UI Artifacts

Date: 2026-04-26
Status: Completed

## Goal

Wire real metadata-only app/browser capture data into the existing IntentOS UI.

## Context

The UI currently reads deterministic fixture artifacts. `make observe-live`
captures the real frontmost macOS app/window but does not enrich active browser
tabs or publish a live replay artifact that the UI can prefer.

## Scope

- Add best-effort active browser tab metadata capture for supported macOS
  browsers.
- Enrich `capture-macos` output with real browser URL/title/domain when
  permissions allow.
- Make `make observe-live` write live replay text and JSON artifacts.
- Make the UI prefer live replay artifacts when present.
- Update docs, lint, audit, and tests.

## Non-Goals

- Add always-on background capture.
- Add screenshots, OCR, or keylogging.
- Add cloud inference or cloud storage.
- Require browser Automation permission in CI.

## Acceptance Criteria

- Real app/window capture still works when browser metadata is unavailable.
- Browser tab enrichment has deterministic fixture tests.
- `make observe-live` writes `live-capture-events.jsonl` and
  `live-capture-summary.json`.
- The UI uses `live-capture-summary.json` when it exists and falls back to
  fixture replay otherwise.
- `make verify` remains deterministic.

## Verification

- `python3 -m unittest discover -s tests -p 'test_capture*.py'`
- `make validate-ui`
- `make verify`

## Implementation Notes

Use `osascript` browser automation only as a local manual sensor. CI must use
fake runners and fixtures.

## Progress Log

- 2026-04-26: Plan created after the UI shell landed and live capture needed to
  feed UI artifacts.
- 2026-04-26: Added best-effort browser active-tab enrichment, live replay
  summary artifacts, UI live-artifact preference, deterministic fixtures, tests,
  and documentation updates.

## Handoff Notes

Completed with capture tests, `make validate-ui`, `make cleanup-check`, and
`make verify`.
