# Execution Plan: Live Capture Session Timeline

Date: 2026-04-26
Status: Completed

## Goal

Turn the one-shot live app/browser capture adapter into a short manual session
timeline that Codex can run, replay, inspect in the UI, and verify through
deterministic fixtures.

## Context

IntentOS can currently capture one metadata-only macOS frontmost app/window
sample and enrich supported browser tabs with URL/title/domain metadata when
local Automation permission allows it. The UI can prefer the latest live replay
summary. The next product step is a short session loop that samples repeatedly,
merges adjacent equivalent activity, and shows a timeline rather than a single
point-in-time event.

## Scope

- Add a manual short-session capture command that samples app/window/browser
  metadata at a fixed interval for a bounded duration.
- Merge adjacent samples with the same app, surface, title, URL, and privacy
  state into longer `ActivityEvent` rows.
- Preserve the existing metadata-only privacy contract: no keylogging, no raw
  screenshots, no clipboard reads, no page bodies, no cloud calls.
- Write session JSONL and replay summaries under `.harness/runtime/artifacts/`.
- Add deterministic fixture tests for session sampling, merging, privacy
  exclusion, and replay output.
- Update the UI to show the session timeline alongside aggregate labels.
- Keep `make verify` deterministic and permission-free.

## Non-Goals

- Always-on background capture.
- ScreenCaptureKit, OCR, local model inference, or cloud inference.
- Browser history database reads.
- Blocking, scheduling, or automated intervention.
- Real user-data uploads or outbound telemetry.

## Acceptance Criteria

- A developer can run a documented local command that captures a bounded manual
  session and writes inspectable JSONL plus replay artifacts.
- Adjacent equivalent samples are merged into coherent durations.
- Privacy exclusions can drop sensitive rows without breaking replay or UI
  diagnostics.
- The UI renders the session timeline from deterministic fixture artifacts and
  prefers live session artifacts when present.
- CI covers session behavior with fixtures or fake runners.
- `make validate-ui`, `make check-ui-screenshot`, and `make verify` pass.

## Verification

- `python3 -m unittest discover -s tests -p 'test_capture*.py'`
- `make validate-ui`
- `make check-ui-screenshot`
- `make verify`
- Manual `make observe-live` or the new session diagnostic when local macOS
  permissions are available.

## Implementation Notes

Start with the existing `ActivityEvent` boundary and one-shot capture helpers.
Do not add new sensors until the session loop, merge behavior, replay, and UI
timeline are fixture-tested. If a new harness command is needed, document it in
`docs/APP_RUNTIME.md`, `docs/RELIABILITY.md`, and `README.md`, then add lint or
audit checks so future agents keep it current.

## Progress Log

- 2026-04-26: Plan created after the one-shot macOS app/browser capture adapter,
  live UI artifact preference, and checked-in UI screenshot evidence shipped.
- 2026-04-26: Implemented `capture-session`, deterministic session fixtures,
  adjacent event merging, `make observe-session`, session replay artifacts, UI
  timeline rendering, validation checks, and refreshed screenshot evidence.

## Handoff Notes

The bounded session timeline is complete for metadata-only capture. Manual live
diagnostics stay in `make observe-session`; CI covers the same behavior through
`data/capture/fake_session_observations.json`, `tests/test_capture_session.py`,
`make validate-ui`, and `make verify`. Next product work should move toward
manual CSV/JSON import before adding ScreenCaptureKit, OCR, or model inference.
