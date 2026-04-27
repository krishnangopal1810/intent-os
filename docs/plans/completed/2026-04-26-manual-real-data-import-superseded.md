# Execution Plan: Manual Real-Data Import

Date: 2026-04-26
Status: Completed (Superseded)

## Goal

Let a user import local CSV or JSON activity records into the existing
`ActivityEvent` boundary, classify them through the current report path, and
inspect the resulting behavior summary in the UI.

## Supersession Note

This plan was superseded on 2026-04-27 by
[Automated Background Timeline](2026-04-27-automated-background-timeline.md).
The product direction is now user-first automated capture with no manual
export/import friction. Manual CSV/JSON records may still be useful as internal
developer fixtures, but they are no longer the recommended user-facing next
slice.

## Historical Scope

- Define a small documented import schema for local CSV and JSON files.
- Add an import command that validates user records and converts them into
  local `ActivityEvent` JSONL.
- Replay imported events through the existing classifier and report output.
- Add deterministic import fixtures for valid rows, validation errors, privacy
  exclusions, and mixed app/browser/chat activity.
- Keep all processing local and deterministic in CI.

## Historical Non-Goals

- Browser history database reads.
- ChatGPT export parsing.
- Always-on capture.
- Cloud sync, cloud inference, or telemetry.
- ScreenCaptureKit, OCR, or model-backed classification.

## Verification

No implementation was shipped from this plan. Supersession is documented by the
active automated background timeline plan and roadmap updates.

## Handoff Notes

Do not restart this as a product-facing import flow unless product direction
changes again. Prefer automated, permissioned, local capture sources.
