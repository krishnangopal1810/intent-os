# Next Steps

This document lists the next useful slices for IntentOS. Prefer turning one item
at a time into an execution plan under `docs/plans/active/`.

## Recently Completed Slices

Must-have focus rescue loop.

Goal: make the dogfood beta protect one named high-value focus from one named
avoid pattern before the day is lost. The dashboard and menu bar now surface a
local rescue state when strict avoid-pattern evidence crosses five minutes.

Why this mattered:

- The product needed a painkiller loop, not another passive activity dashboard.
- Rescue is triggered from the user's own focus and avoid contract, so the
  product moment is personal and testable.
- Continue, return, pause, and correction choices preserve agency without
  adding notifications, blocking, cloud inference, or automation.

Completed acceptance criteria:

- `/api/daily-loop` exposes `focus_rescue` with state, reason, threshold,
  protected focus time, avoid time, primary evidence, receipts, latest action,
  and available choices.
- `POST /api/focus-rescue-action` records shown, return-to-focus,
  continue-intentionally, pause-capture, and corrected-evidence actions.
- SQLite retention and delete-local-data clear focus rescue actions with other
  local user state.
- The dashboard makes focus rescue visible in the first coach moment on desktop
  and mobile, with compact local action buttons.
- The menu bar prioritizes Recovery Available, Avoid Leaking, Focus Protected,
  and Need Evidence after pause/setup/capture health.
- `make validate-beta`, `make validate-ui`, screenshot checks, and unit tests
  cover rescue API payloads, action persistence, rendered UI, and menu labels.

Must-have product loop.

Goal: make the dogfood beta feel like a daily intent coach instead of an
activity dashboard. The first screen now answers: what the user planned to
protect, what they meant to avoid, what happened, what IntentOS learned, and
what to do in the next block.

Why this mattered:

- The default product moment should create accountability, not ask the user to
  interpret analytics.
- Natural-language focus and avoid inputs now become visible deterministic
  signals: app names, domains, titles, URLs, and labels.
- Correction reward and weekly patterns reinforce accuracy improvement without
  streaks, scores, blocking, or notifications.

Completed acceptance criteria:

- `/api/daily-loop` exposes `intent_contract`, `next_block`, and
  `correction_reward` alongside plan-vs-actual receipts.
- `/api/weekly-patterns` exposes three local weekly pattern cards.
- The dashboard leads with the plan-vs-actual coach hero, one next block,
  visible intent contract, and collapsed evidence/weekly detail.
- The menu bar exposes intent, evening review, next block, weekly patterns,
  pause/resume, diagnostics, and product status labels such as Review Ready,
  Focus Holding, Avoid Leaking, and Needs Correction.
- `make validate-beta` and `make validate-ui` enforce the new UI bindings,
  density budget, friendly empty states, visible-copy policy, and API payloads.

Sticky daily loop.

Goal: make the dogfood beta worth returning to by asking the user to set one
focus and one thing to avoid, then complete an evening review that compares
intent against captured behavior and carries an adjustment forward.

Why this mattered:

- The product should not rely on users voluntarily inspecting a dashboard.
- Intent gives the daily review a concrete plan-vs-actual frame.
- Evening review and correction counts reinforce that the product gets sharper
  with use.

Completed acceptance criteria:

- Local beta SQLite stores daily intents and review check-ins with retention.
- `/api/daily-loop`, `/api/daily-intent`, and `/api/review-checkin` are
  available on the local service.
- The dashboard exposes Today's Intent above the Action Queue.
- The menu bar can show Intent Due and Review Due without OS notifications.
- `make validate-beta`, `make validate-ui`, and `make verify` cover the loop.

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
- Local menu bar packaging, bundled trusted-tester artifact packaging, guided
  first-run setup, capture preview, redacted setup report, and install/open
  smoke evidence exist.
- Deterministic verification, cleanup audit, beta validation, UI render checks,
  and screenshot freshness gates pass locally.

Testing boundary:

- Send only to trusted Mac users who are comfortable running a local Mac beta,
  granting Accessibility for app/window metadata, and sharing the redacted setup
  report if setup fails. Browser detail is optional after first value.
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
- 2026-05-03: trusted source beta handoff was added at
  [launch/trusted-source-beta.md](launch/trusted-source-beta.md), linked from
  the README and docs index, and includes setup, permissions, privacy,
  diagnostics, stop/delete, troubleshooting, and feedback template.
- 2026-05-03: fresh launch gate passed `make cleanup-check`, `make
  validate-ui`, `make validate-beta`, `make verify`, `make package-beta`,
  `make install-beta-app`, `make package-extension`, `make beta-status`, `make
  diagnose-json`, and `make dogfood-smoke`.
- 2026-05-03: fresh `make dogfood-smoke` passed for 30 minutes with rows
  increasing from 6032 to 6119, native recorder `running`, pause privacy
  passing, and Chrome bridge absence recorded only as a warning.
- 2026-05-03: `make chrome-bridge-smoke` was blocked because the installed
  Chrome bridge did not reach `connected` or `posting_events` before timeout;
  native recorder stayed `running` and rows increased from 6124 to 6159 during
  the blocked smoke.

## Recommended Next Slice

Trusted tester demand validation.

Goal: put the focus-rescue beta in front of a small trusted Mac cohort and
measure whether the protected-focus loop is valuable enough to miss. Chrome
bridge recovery remains useful only when a tester's real browser-heavy workflow
needs richer evidence than the native recorder provides.

Acceptance criteria:

- At least two testers launch the source beta, set one focus and one avoid
  target, and see a focus-rescue state from current-day local evidence.
- Each tester answers: "Would you be upset if IntentOS stopped protecting this
  focus next week?"
- At least one feedback item becomes a fixture, harness check, quality note, or
  explicit product assumption.
- Cohort results are recorded in the ignored
  `.harness/runtime/artifacts/cohort-evidence.json` shape and pass
  `make cohort-evidence-check`.
- Any Chrome bridge repair work is tied to a tester workflow where native
  recorder metadata is insufficient for focus rescue.
- `make beta-status`, `make diagnose-json`, and redacted feedback fixtures are
  enough to debug tester issues without raw SQLite sharing.

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
2. Calendar or planned-intent integration so IntentOS can expand beyond the
   current focus+avoid intent into time-block-aware comparison.
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
