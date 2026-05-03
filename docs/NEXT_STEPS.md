# Next Steps

This document lists the next useful slices for IntentOS. Prefer turning one item
at a time into an execution plan under `docs/plans/active/`.

## Recently Completed Slices

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

Dogfood beta harness.

Goal: make IntentOS usable by internal macOS dogfood users without manual
imports: local service, native macOS recorder, SQLite retention, optional
Chrome metadata bridge, daily review APIs, correction controls, pause/resume,
delete-local-data, and native menu bar packaging.

Why this mattered:

- The user sees value from automated capture rather than export/import chores.
- The dashboard can read live local service APIs while fixture mode remains
  deterministic for verification.
- Corrections let users fix trust-breaking labels and apply the fix to future
  matching events without mutating raw activity.
- The beta is inspectable through `make beta-status`, logs, DB row counts, and
  validation artifacts.

Completed acceptance criteria:

- `make beta-dev`, `make beta-status`, `make beta-stop`, `make validate-beta`,
  `make package-beta`, `make install-beta-app`, `make package-extension`, and
  `make dogfood-smoke` are available.
- Native recorder events are privacy-filtered through the capture stack before
  SQLite persistence.
- Chrome bridge events are optional and privacy-filtered before SQLite
  persistence.
- `make validate-beta` covers APIs, persistence, correction, pause/resume,
  delete-local-data, privacy filtering, and service-backed UI loading.
- The Swift wrapper builds locally as an ad-hoc signed dogfood app bundle when
  macOS Swift tools are available.

Dogfood onboarding, permission UX, and real smoke.

Goal: make a trusted internal user understand what is being captured, grant or
repair local permissions, and verify real capture without relying on fixture
rows.

Why this mattered:

- First-run trust and permission clarity decide whether users keep the beta
  running.
- The same readiness state is visible in the dashboard, service status, and
  native menu bar.
- Real dogfood smoke preserves the local SQLite database and records
  blocked/pass evidence instead of asking users to manually inspect logs.

Completed acceptance criteria:

- Dashboard shows non-blocking first-run local-only onboarding and permission
  health.
- Menu bar exposes setup-needed, paused, running, capture issue, permission
  check, settings, Chrome setup, diagnostics, and existing pause/resume/delete
  actions.
- `make validate-beta` covers onboarding, permission APIs, settings validation,
  corrections, pause/resume, delete-local-data, and service-backed UI loading
  with fake probes.
- `make dogfood-smoke` starts beta without the fake bridge and writes real
  smoke evidence from native recorder row growth without deleting dogfood data.

Browser extension capture now exists as a Chrome-first dogfood bridge shell and
fake harness source. It is an enhancement for richer browser metadata, not a
blocking requirement for first beta value.

## Recommended Next Slice

Launch dogfood beta with native-recorder smoke evidence.

Goal: complete one fresh internal dogfood launch pass with native recorder
capture, menu bar install/open, delete-local-data recovery, and clear evidence
artifacts; then optionally run a second pass with the Chrome bridge installed.

Why this is next:

- The first beta experience should work before the user installs a browser
  extension.
- Chrome bridge state now distinguishes never connected, connected, stale, and
  posting events; the launch pass should confirm those states are understandable.
- The remaining launch question is operational confidence, not manual data
  import support.

Acceptance criteria:

- `make dogfood-smoke` passes on a dogfood machine from native recorder events
  with the Chrome bridge absent or stale only as a warning.
- `make package-beta`, `make install-beta-app`, and `make package-extension`
  produce local artifacts.
- `make beta-status` and dashboard onboarding show native recorder as primary
  capture source and Chrome bridge as optional enhanced browser metadata.
- A second smoke with the extension installed verifies the bridge moves to
  connected or posting-events.

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
- Keep beta structured runtime logs current for service startup, browser bridge
  events, corrections, pause/resume, delete-local-data, and retention cleanup.
- Keep `make observe-live` as the manual local sensor diagnostic and expand it
  as new metadata adapters land.
- Add stricter architecture rules as modules grow. Promote repeated review
  comments into `scripts/harness/lint.py`.
- Keep expanding cleanup/audit scripts that scan stale plans, stale docs,
  fixture drift, and quality scorecard gaps.

## Then

1. Real Chrome extension dogfood install flow and visible bridge health.
2. Calendar or planned-intent integration so IntentOS can compare what happened
   against what the user meant to do.
3. Accessibility visible-text excerpts for desktop apps where titles are too
   sparse.
4. IDE, Git, and terminal metadata for engineers and builders.
5. Communication and meeting metadata with strict body-free privacy defaults.
6. Daily behavior narratives and intent-vs-outcome mismatch detection once the
   automated timeline has enough context.
7. ScreenCaptureKit fallback plus Vision OCR for low-confidence events.
8. Local model second-pass classifier through Foundation Models, Core ML, or
   MLX once fixture evaluation justifies it.
9. Richer DOM automation for the local UI shell once interactions exist.

Each item above must satisfy the feature-specific harness contract in
[HARNESS_FEATURES.md](HARNESS_FEATURES.md): deterministic fixtures, local
runtime artifacts, structured logs, docs, verification, and UI evidence when
visible behavior changes.

## Not Yet

- Cloud inference.
- Cloud storage of personal activity.
- Blocking or scheduling actions.
- Public packaged always-on launch outside the current dogfood harness.
- Manual export/import as the primary user path.
