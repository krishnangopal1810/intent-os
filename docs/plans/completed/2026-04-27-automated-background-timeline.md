# Execution Plan: Automated Background Timeline

Date: 2026-04-27
Status: Completed

## Goal

Turn the current live app/window/browser sampler into an automated local
background timeline that is easy for a user to understand: start the app once,
grant local permissions when needed, and see a continuously refreshed
privacy-filtered timeline without manual exports or imports.

## Context

IntentOS already has frontmost macOS app/window capture, best-effort active
browser tab enrichment, bounded session capture, replay artifacts, and a local
UI. The current background sampler appends raw live samples during `make dev`,
but the user-facing experience should be a timeline of meaningful activity
segments rather than a list of repeated polling rows.

Manual user-data imports are not the preferred product path because they add
user friction. Fixture imports may still exist for deterministic verification,
but real product value should come from automated, permissioned, local capture.

## Scope

- Keep the existing metadata-only capture path: app/window metadata and
  best-effort browser URL/title/domain enrichment.
- Add a merged background timeline artifact derived from live samples.
- Refresh the user-facing live summary from the merged timeline, not raw
  repeated samples.
- Expose timeline artifact paths, merged row counts, and latest status through
  local status JSON and `make app-status`.
- Update UI labels so live background capture reads as an automated timeline.
- Keep fixtures and tests deterministic; live macOS permissions remain outside
  CI.

## Non-Goals

- Manual CSV/JSON import as a user-facing feature.
- Browser history database reads.
- Browser extension capture.
- Calendar or planned-intent integration.
- Always-on packaged app launch outside the current harness runtime.
- ScreenCaptureKit, OCR, keylogging, clipboard capture, or cloud inference.
- Raw screenshot retention or full page/body/conversation capture.

## Acceptance Criteria

- Starting the local app starts the background sampler and writes both raw
  diagnostic samples and a merged live timeline artifact.
- The UI prefers the merged live timeline summary when background capture is
  running.
- Adjacent equivalent activity is merged so the user sees stable segments such
  as "Chrome - ChatGPT" for a continuous span, not duplicate polling rows.
- `make app-status` exposes capture state, raw sample count, merged event
  count, output paths, and the last known update.
- Deterministic tests cover timeline merging, status fields, and summary
  refresh behavior.
- Privacy exclusions and redaction still apply before any user-derived row is
  persisted.

## Harness Impact

- Runtime commands and artifacts: extend `capture-live` so `make dev` writes
  `live-capture-events.jsonl`, `live-capture-timeline-events.jsonl`,
  `live-capture-summary.txt`, `live-capture-summary.json`, and
  `live-capture-status.json`.
- Fixtures or fakes required for deterministic `make verify`: extend existing
  live capture unit tests with fake macOS/browser providers and no live
  permissions.
- UI validation or screenshot evidence: update UI copy and validation only for
  the live summary artifact path already used by the UI.
- Structured logs, metrics, or diagnostics: status JSON must include raw sample
  counts, merged event counts, timeline path, summary path, interval, and state;
  structured runtime events should continue to identify the background timeline
  process and artifact paths.
- Privacy, permission, or local-only constraints: preserve current metadata-only
  capture, local privacy filtering, no screenshots, no keylogging, and local
  runtime artifacts.
- Docs or harness checks to update: update product, architecture, runtime,
  reliability, quality, next-step, and active-plan docs where the roadmap or
  artifact contract changes. Keep [../../HARNESS_FEATURES.md](../../HARNESS_FEATURES.md)
  aligned for future automated source slices.

## Verification

- `python3 -m unittest discover -s tests -p 'test_capture_live.py'`
- `python3 -m unittest discover -s tests`
- `make validate-ui`
- `make verify`

## Implementation Notes

Reuse the existing `ActivityEvent`, privacy, JSONL, replay, and
`merge_adjacent_events` helpers. The background sampler should keep raw samples
available for diagnostics while making the merged timeline the user-facing
summary. The deterministic tests should use fake providers rather than live
macOS state. Avoid adding a separate event model.

## Progress Log

- 2026-04-27: Plan created after product direction changed toward automated
  background timeline capture and away from manual user imports.
- 2026-04-27: Implemented merged live background timeline artifacts, status
  fields, harness wiring, UI copy, docs, screenshot evidence, and verification.
