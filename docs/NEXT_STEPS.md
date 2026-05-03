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

- Dashboard shows non-blocking first-run local-only onboarding, permission
  health, and target-specific setup guidance.
- Menu bar exposes setup-needed, paused, running, capture issue, permission
  check, settings, Chrome setup, diagnostics, setup guidance, and existing
  pause/resume/delete actions.
- `make validate-beta` covers onboarding, permission APIs, settings validation,
  corrections, pause/resume, delete-local-data, and service-backed UI loading
  with fake probes.
- `make dogfood-smoke` starts beta without the fake bridge and writes real
  smoke evidence from native recorder row growth without deleting dogfood data.

Browser extension capture now exists as a Chrome-first dogfood bridge shell and
fake harness source. It is an enhancement for richer browser metadata, not a
blocking requirement for first beta value.

## Friend Testing Readiness

Status: ready for trusted source-beta testing, not public distribution.

What is ready:

- Native macOS metadata capture is the primary beta source.
- Service-backed daily review, corrections, pause/resume, permission guidance,
  delete-local-data, and diagnostics are wired.
- Local menu bar packaging and install/open smoke evidence exist.
- Deterministic verification, cleanup audit, beta validation, UI render checks,
  and screenshot freshness gates pass locally.

Testing boundary:

- Send only to trusted Mac users who are comfortable running a source beta,
  granting Accessibility and browser Automation permissions, and sharing
  diagnostics if setup fails.
- Do not present it as a polished installer, notarized app, or public beta.
- Chrome bridge setup is optional for the first pass; native recorder capture
  should show value without it.
- Ask testers to report permission-check output, `make beta-status`, and
  dashboard behavior rather than sharing raw SQLite data.

Current evidence:

- 2026-05-03: `make verify` passed, including beta validation and UI render
  checks.
- 2026-05-03: `make cleanup-check` passed after splitting beta correction-key
  helpers out of `store.py`.
- 2026-05-03: `make package-beta` produced the ad-hoc signed local menu bar
  app bundle.
- 2026-05-03: `make install-beta-app` installed and opened
  `/Users/kgopal/Applications/IntentOSBeta.app`.
- 2026-05-03: `make package-extension` produced the internal Chrome bridge zip.
- 2026-05-03: `make beta-status` reported readiness `ready`, native recorder
  `running`, SQLite `quick_check` `ok`, and Chrome bridge `never_connected`
  as an optional unchecked enhancement.
- 2026-05-03: `make dogfood-smoke` passed for 30 minutes on the dogfood
  machine with native recorder events and no fake bridge. Rows increased from
  3292 to 3348, pause held row count steady, and Chrome bridge absence was
  recorded only as a warning.

## Recommended Next Slice

Trusted friend beta handoff plus installed Chrome bridge smoke.

Goal: send the source beta to a small trusted Mac tester group, collect setup
and classification feedback, and run a second smoke with the Chrome bridge
installed so bridge health moves from `never_connected` to `connected` or
`posting_events`.

Acceptance criteria:

- At least two testers can launch the source beta through the menu bar app or
  `make beta-dev`, grant required local permissions, and see current-day
  activity in the service-backed dashboard.
- Permission-check output is understandable enough that testers can recover
  from missing Accessibility, Automation, native recorder, or Chrome bridge
  setup without chat-only instructions.
- A second smoke with the Chrome extension installed verifies bridge connected
  or posting-events state while native recorder remains the primary path.
- Feedback that changes product assumptions is recorded in docs or fixtures,
  not left only in chat.

## Harness Upgrades To Keep Current

- Keep the local UI shell current as product slices land. New user-visible
  behavior should appear in `web/` and pass `make validate-ui`.
- Refresh `docs/assets/screenshots/intent-os-ui.png` with
  `make update-ui-screenshot` whenever UI source, fixture inputs, or report
  output changes.
- Keep structured runtime events current when new capture, classification,
  reporting, or UI paths are added.
- Use `make new-feature` for future roadmap slices so active plans start with
  acceptance criteria and complete Harness Impact sections.
- Run `make adapter-fixture-check` when capture or parser fixtures change; keep
  the adapter fixture manifest aligned with every real adapter.
- Run `make diagnose-json` and `make review-status` when handing off runtime or
  PR failures so future agents get structured evidence.
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
- Use `make chrome-bridge-smoke` for installed Chrome bridge validation; it
  must reach connected or posting-events without seeded fake bridge rows.
- Use `make feedback-fixture-candidates` to turn trusted tester corrections
  into privacy-redacted fixture candidates before adding labeled examples.
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
