# macOS Live Activity Capture Prototype

Status: In Progress

## Goal

Build the first metadata-only macOS live capture slice so IntentOS can create
local `ActivityEvent` records from the user's current app, focused window, and
one browser's active tab metadata.

## Scope

- Use the parallel work package under
  [../parallel/macos-live-capture/TRACKER.md](../parallel/macos-live-capture/TRACKER.md)
  when splitting implementation across multiple Codex agents.
- Add a macOS capture adapter boundary that normalizes raw observations into
  `ActivityEvent`.
- Capture app name, bundle ID, process ID, focused window title, timestamps,
  and duration.
- Add one browser metadata adapter for active tab URL and title.
- Write captured events to local JSONL.
- Add replay support that classifies captured JSONL with the existing behavior
  classifier.
- Add fixture tests for normalization, redaction, and replay.
- Document manual permission setup and local-only data handling.

## Non-Goals

- No keylogging.
- No raw screenshot retention.
- No ScreenCaptureKit capture in the first live slice.
- No Vision OCR in the first live slice.
- No cloud inference.
- No always-on background daemon.
- No automatic blocking, scheduling, or intervention.

## Acceptance Criteria

- A developer can run a local capture smoke command and produce JSONL
  `ActivityEvent` records.
- CI can verify capture normalization and replay through fixtures or fakes.
- Sensitive app/domain/window exclusions are supported in configuration or
  documented for the first implementation.
- `make verify` passes without requiring macOS permissions or live sensors.
- The active plan records any manual smoke-test evidence.

## Verification

- `make harness-check`
- `make harness-lint`
- `make verify`
- Manual local smoke test for macOS capture when permissions are available.

## Progress Log

- 2026-04-26: Planned as the next live-capture slice. Harness and docs now
  require the live-capture privacy and on-device inference contract before
  implementation begins.
- 2026-04-26: Added a three-agent parallel work package with disjoint ownership
  for capture core, browser/privacy policy, and replay/runtime integration.
- 2026-04-26: Implemented all three parallel packages as a fake-sensor capture
  loop: app/window observations plus browser metadata normalize to
  `ActivityEvent` JSONL, privacy policy applies exclusions/redaction, and replay
  uses existing classifier reports. Live macOS sensor APIs are still pending.
- 2026-04-26: Added a manual macOS frontmost app/window adapter using
  `osascript`/System Events. It captures app name, bundle ID, process ID, and
  focused window title into the existing `ActivityEvent` JSONL path. Live
  browser tab metadata remains pending.
