# Execution Plan: Next Feature Harness Readiness

Date: 2026-04-27
Status: Completed

## Goal

Make the harness explicitly support the upcoming IntentOS feature sequence:
manual real-data import, browser history import, ChatGPT export parsing, daily
behavior narratives, ScreenCaptureKit/OCR fallback, local model second-pass
classification, and richer UI automation.

## Scope

- Add a durable harness contract for each upcoming feature family.
- Add a local import product spec before importer implementation starts.
- Update repository indexes and runtime docs so Codex can find the new
  contracts.
- Add mechanical checks that keep next-feature docs and active-plan readiness
  visible.
- Preserve deterministic CI and local-only privacy defaults.

## Non-Goals

- Implement the importers, browser history parser, ChatGPT parser, OCR, local
  model runtime, or UI narrative product behavior.
- Add new external dependencies.
- Add permission-dependent commands to `make verify`.

## Acceptance Criteria

- Future feature harness requirements are documented in a single indexed file.
- Import-specific product requirements are documented before implementation.
- Harness checks fail if required next-feature contracts disappear.
- The manual real-data import active plan points future implementation to the
  harness contracts.
- Existing verification continues to pass.

## Verification

- `make harness-check`
- `make harness-lint`
- `make cleanup-check`
- `make verify`

## Progress Log

- 2026-04-27: Added next-feature harness contracts, local import spec, roadmap
  links, active-plan readiness notes, and lint/audit enforcement.
