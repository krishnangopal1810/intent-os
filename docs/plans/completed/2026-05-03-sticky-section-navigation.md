# Execution Plan: sticky-section-navigation

Date: 2026-05-03
Status: Completed

## Goal

Keep the Review, Decisions, Timeline, and Activity navigation visible while the
dashboard content scrolls.

## Scope

- Change the dashboard shell to an app-style viewport where the content pane
  scrolls independently of the navigation.
- Preserve narrow/mobile layout while keeping the navigation available after
  section jumps.
- Update nav active state from the current hash/scroll position.
- Add harness coverage so section navigation does not regress.

## Non-Goals

- No backend, capture, classifier, persistence, menu bar, or API changes.
- No redesign of the information architecture or section names.

## Acceptance Criteria

- Clicking Activity, Timeline, Decisions, or Review does not scroll the
  navigation out of view.
- The active navigation item follows hash clicks and scroll position.
- Desktop and mobile render probes still pass.
- `make verify` passes.

## Harness Impact

- Runtime commands and artifacts: existing UI and beta validation cover this
  frontend slice.
- Fixtures or fakes required for deterministic `make verify`: none.
- UI validation or screenshot evidence: refresh checked-in UI screenshot and
  add section-nav checks.
- Structured logs, metrics, or diagnostics: none.
- Privacy, permission, or local-only constraints: no data changes.
- Docs or harness checks to update: active plan, design notes, and UI render
  validation.

## Verification

- Syntax checks passed with `node --check web/app.js`,
  `bash -n scripts/product/validate-ui.sh scripts/product/validate-beta.sh`,
  and `python3 -m py_compile` for changed Python harness modules.
- `make update-ui-screenshot` passed.
- `make validate-ui` passed with desktop and mobile section-nav probes.
- `make validate-beta` passed with service-backed desktop and mobile
  section-nav probes.
- `make verify` passed.
- Post-completion `make harness-check` and `make harness-lint` passed.

## Progress Log

- 2026-05-03: Plan created from feedback that section anchor jumps hide the
  navigation on narrow screens.
- 2026-05-03: Changed the shell to a fixed app viewport with independent
  workspace scrolling, routed section links through workspace-only scroll, added
  active nav updates, refreshed screenshot evidence, and passed verification.
