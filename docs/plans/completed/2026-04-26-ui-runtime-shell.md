# Execution Plan: UI Runtime Shell

Status: Completed

## Goal

Give IntentOS a local UI runtime that Codex and the user can open as product
features land.

## Context

The product currently exposes behavior reports through CLI output and JSON
artifacts. The harness needs a real UI shell, local serving path, and validation
loop before future UI slices are built.

## Scope

- Create the first local UI shell so IntentOS can expose product slices as they
  land.
- Read deterministic runtime artifacts from `.harness/runtime/artifacts/`.
- Serve the shell through `make dev`.
- Validate the shell through `make validate-ui`.

## Non-Goals

- Add browser screenshot automation.
- Add user accounts, persistence, settings, or live capture controls.
- Replace the CLI reports.

## Acceptance Criteria

- `make dev` generates current product artifacts and serves a local UI URL.
- `make app-status` exposes the UI URL, process, logs, and artifact paths.
- `make validate-ui` verifies the page shell and JSON artifacts.
- `make verify` includes UI validation.
- UI source files are repository-local and documented.
- Harness lint/audit checks fail if the UI shell or validator disappears.

## Verification

- `make validate-ui`
- `make dev`
- `make app-status`
- `make observe`
- `make verify`

## Progress Log

- 2026-04-26: Started the UI runtime shell plan after deciding the product
  should expose new behavior through a local UI as features land.
- 2026-04-26: Added `web/` UI shell, `scripts/product/start-ui.sh`,
  `scripts/product/validate-ui.sh`, `make dev` UI serving, and `make verify`
  UI validation.

## Implementation Notes

Use standard-library tooling where possible so `make verify` remains dependency
free.

## Handoff Notes

Completed with `make validate-ui`, `make verify`, `make cleanup-check`, and
`git diff --check`.
