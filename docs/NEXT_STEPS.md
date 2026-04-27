# Next Steps

This document lists the next useful slices for IntentOS. Prefer turning one item
at a time into an execution plan under `docs/plans/active/`.

## Recently Completed Slice

Automated background timeline.

Goal: make the existing live sampler feel like a user-first timeline: starting
the local app automatically captures current app/window/browser metadata, keeps
raw diagnostic samples separate, merges adjacent equivalent activity into stable
segments, and refreshes the UI from that merged timeline with no manual exports
or imports.

Why this mattered:

- The user should not have to export, clean, or import data before seeing value.
- The previous background sampler appended repeated raw polling rows; the UI
  now gets merged activity segments.
- The status path now exposes raw row count, merged timeline row count, output
  paths, interval, state, and latest event.
- It keeps raw diagnostic evidence available without making duplicate samples
  the user-facing experience.

Completed acceptance criteria:

- `make dev` starts a visible automated background timeline after the UI starts.
- Raw live rows are written to `live-capture-events.jsonl`, while merged
  timeline rows are written to `live-capture-timeline-events.jsonl`.
- `live-capture-summary.json` is refreshed from the merged timeline.
- App status exposes capture mode, raw row count, timeline row count, output
  paths, interval, state, and latest event.
- Deterministic tests cover the timeline path without macOS permissions.
- Preserve local-only processing, privacy exclusions, no screenshots, and no
  keylogging.
- Refresh checked-in UI screenshot evidence with `make update-ui-screenshot`.

## Recommended Next Slice

Browser extension capture.

Goal: enrich the automated background timeline with reliable browser context:
tab changes, URL/title updates, single-page app state, YouTube metadata, and
document titles without requiring the user to export browser history.

Why this is next:

- Browser activity is the highest-volume surface for target users.
- Browser active-tab AppleScript is useful but brittle for SPA state, title
  changes, and rich media metadata.
- A browser extension can improve classification while preserving local-only,
  permissioned capture.

Acceptance criteria:

- Add a scoped browser extension adapter plan before implementation.
- Capture bounded tab metadata and page category hints, not page bodies.
- Add deterministic fake extension fixtures for CI.
- Preserve privacy exclusions for auth, private, banking, health, payment, tax,
  and location-bearing URLs.
- Replay extension events through the existing `ActivityEvent` path.

## Harness Upgrades To Keep Current

- Keep the local UI shell current as product slices land. New user-visible
  behavior should appear in `web/` and pass `make validate-ui`.
- Refresh `docs/assets/screenshots/intent-os-ui.png` with
  `make update-ui-screenshot` whenever UI source, fixture inputs, or report
  output changes.
- Keep structured runtime events current when new capture, classification,
  reporting, or UI paths are added.
- Add richer DOM automation to `make validate-ui` when UI workflows become
  interactive enough that static HTML checks and checked-in screenshots are no
  longer sufficient.
- Add deterministic capture fixtures for every real adapter. The macOS
  frontmost adapter now has `data/capture/macos_frontmost_snapshot.json`, and
  browser active-tab enrichment has
  `data/capture/browser_active_tab_snapshot.json`; session behavior now has
  `data/capture/fake_session_observations.json`. Future ScreenCaptureKit, OCR,
  and model adapters need equivalent fixtures.
- Add structured runtime logs for capture, classification, and reporting before
  adding a persistent service. Stable fields should include `component`,
  `event`, `mode`, `artifact_path`, `duration_ms`, `event_count`, and `status`.
- Keep `make observe-live` as the manual local sensor diagnostic and expand it
  as new metadata adapters land.
- Add stricter architecture rules as modules grow. Promote repeated review
  comments into `scripts/harness/lint.py`.
- Keep expanding cleanup/audit scripts that scan stale plans, stale docs,
  fixture drift, and quality scorecard gaps.

## Then

1. Calendar or planned-intent integration so IntentOS can compare what happened
   against what the user meant to do.
2. Accessibility visible-text excerpts for desktop apps where titles are too
   sparse.
3. IDE, Git, and terminal metadata for engineers and builders.
4. Communication and meeting metadata with strict body-free privacy defaults.
5. Daily behavior narratives and intent-vs-outcome mismatch detection once the
   automated timeline has enough context.
6. ScreenCaptureKit fallback plus Vision OCR for low-confidence events.
7. Local model second-pass classifier through Foundation Models, Core ML, or
   MLX once fixture evaluation justifies it.
8. Richer DOM automation for the local UI shell once interactions exist.

Each item above must satisfy the feature-specific harness contract in
[HARNESS_FEATURES.md](HARNESS_FEATURES.md): deterministic fixtures, local
runtime artifacts, structured logs, docs, verification, and UI evidence when
visible behavior changes.

## Not Yet

- Cloud inference.
- Cloud storage of personal activity.
- Blocking or scheduling actions.
- Packaged always-on launch outside the current local harness.
- Manual export/import as the primary user path.
