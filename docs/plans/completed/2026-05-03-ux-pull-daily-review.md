# Execution Plan: ux-pull-daily-review

Date: 2026-05-03
Status: Completed

## Goal

Make the daily review feel worth returning to by turning local behavior data
into an opinionated, action-oriented review surface instead of a passive
dashboard.

## Context

The current UI is legible and verified, but the first screen mostly restates
time buckets. The target user should immediately see what was worth repeating,
where attention leaked, what evidence needs correction, and what to do next.

## Scope

- Rework the first-screen daily review hierarchy in `web/index.html`.
- Add deterministic client-side insight rendering in `web/app.js` from existing
  activity, capture, and beta daily-review artifacts.
- Reduce review-time unknown noise where current live logs show clear,
  deterministic metadata patterns.
- Aggregate and sort low-confidence beta review rows so the trust queue leads
  with the largest remaining ambiguity.
- Refresh responsive styling in `web/styles.css` while preserving the local
  utility-app design language.
- Add harness checks that require the new decision surface and rendered
  desktop/mobile UX evidence.
- Update UX docs, quality notes, and screenshot evidence.

## Non-Goals

- No new sensors, permissions, cloud services, model inference, or persistence.
- No changes to classifier labels or taxonomy behavior.
- No new frontend framework or external dependency.

## Acceptance Criteria

- The first viewport leads with a clear daily verdict and next move, not just a
  chart.
- The UI exposes repeatable focus, attention leak, trust/correction, and next
  action cards derived from local artifacts.
- The first screen avoids an oversized dashboard-template feel by using a
  compact review board, action queue, and evidence ledger.
- Fixture, live-session, live-capture, and beta modes still render without
  fixture fallback violations.
- The legacy YouTube domain slice does not appear as a standalone navigation
  tab or report panel.
- Mobile and desktop layouts avoid clipped text and horizontal overflow.
- `make validate-ui` fails if the decision surface bindings disappear or if
  rendered desktop/mobile probes detect blank UI, overflow, missing events, or
  clipped text.
- Checked-in screenshot evidence is refreshed after the visual change.

## Harness Impact

- Runtime commands and artifacts: existing `make dev`, `make validate-ui`, and
  `make update-ui-screenshot` cover this static UI shell; `make validate-ui`
  will emit desktop and mobile render evidence for UX regressions when
  Chrome/Chromium exists.
- Fixtures or fakes required for deterministic `make verify`: use existing
  activity, capture, session-capture, YouTube, and beta validation fixtures.
- UI validation or screenshot evidence: update `scripts/product/validate-ui.sh`
  and `scripts/product/render-ui-check.py`, run `make validate-ui`, and refresh
  `docs/assets/screenshots/intent-os-ui.png`.
- Structured logs, metrics, or diagnostics: no new runtime logging expected;
  existing UI validation artifacts remain sufficient.
- Privacy, permission, or local-only constraints: preserve metadata-only,
  local-only copy and do not add network calls beyond the local beta service.
- Docs or harness checks to update: update `docs/DESIGN.md`, `docs/QUALITY.md`,
  this plan, and screenshot metadata.

## Verification

- `make validate-ui` passed with desktop and mobile rendered UI probes.
- `make validate-beta` passed with service-backed decision-card and next-move
  render coverage.
- `make verify` passed.

## Implementation Notes

Keep all derived UX in the browser from already loaded reports. Prefer concise
copy and stable responsive dimensions over new product concepts that require
backend state.

## Progress Log

- 2026-05-03: Plan created.
- 2026-05-03: Read product, architecture, runtime, design, and verification
  docs; confirmed no active implementation plan existed.
- 2026-05-03: Generated fixture artifacts with `scripts/product/dev.sh` and
  identified the passive-dashboard gap in the current review surface.
- 2026-05-03: Expanded scope per user request to include UI/UX harness support.
- 2026-05-03: Inspected live beta SQLite rows and service logs after user
  reported excessive unknown time; identified clear classifier gaps for
  developer docs, local IntentOS review, GitHub repositories, sports video,
  personal logistics, shopping/product research, and social feed/status pages.
- 2026-05-03: Added the daily decision surface, next-move rendering,
  desktop/mobile UI probes, and refreshed screenshot evidence.
- 2026-05-03: `make validate-ui` passed with decision cards and desktop/mobile
  rendered screenshots.
- 2026-05-03: Full `make verify` exposed that beta UI render probes still used
  the older UX shape; updated `make validate-beta` coverage to require decision
  cards and next move text too.
- 2026-05-03: `make validate-beta` passed after beta probe updates.
- 2026-05-03: `make verify` passed.
- 2026-05-03: Fixed `make dev` to launch the background sampler as a detached
  process; `make app-status` now reports both UI and capture running.
- 2026-05-03: Isolated `make validate-ui` runtime artifacts so validation stays
  deterministic while the local app and background sampler are running.
- 2026-05-03: Extended UI render probes to wait for settled daily-review data
  before validating stats, decision cards, and next move text.
- 2026-05-03: Removed the legacy YouTube tab and report panel from the web
  shell; validation now rejects the old standalone domain section.
- 2026-05-03: Reworked the visual system from dashboard cards into a denser
  production-style review board with compact score, action queue rows, and
  tighter product copy.

## Handoff Notes

Implemented and verified. The local dashboard now opens on an action-oriented
daily review with a verdict, next move, decision cards, behavior mix, and
capture replay evidence. UI harness coverage now checks the decision surface in
fixture and beta modes, plus desktop/mobile browser rendering when available.
The local fixture app is running for handoff with a healthy background timeline.
UI validation now uses an isolated runtime and mirrors evidence back to the
normal diagnostic artifact directory.
