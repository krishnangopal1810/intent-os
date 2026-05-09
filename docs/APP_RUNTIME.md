# App Runtime Harness

Codex must be able to run, inspect, and validate the product locally. Product
runtime commands can be one-shot for CLI slices or persistent for UI/service
slices.

## Commands

- `make dev`: generate fixture-backed product artifacts, launch the local UI
  shell for the current worktree, and start the visible automated background
  timeline.
- `make dev-live`: run a fresh bounded macOS live session, preserve its replay
  artifact, and launch the local UI shell against that live session summary.
- `make beta-dev`: start the dogfood beta service, native recorder, SQLite DB,
  and service-backed dashboard with fake bridge disabled by default.
- `make beta-status`: show beta service PID, DB path, capture state, pause
  state, native recorder state, extension bridge state, last event time, row
  counts, and log paths.
- `make beta-stop`: stop beta service, native recorder, fake bridge, and beta
  UI processes.
- `make validate-beta`: run deterministic beta API, persistence, correction,
  privacy, delete-data, and UI smoke checks against a temp DB.
- `make package-beta`: build the local ad-hoc signed Swift menu bar app bundle
  when macOS Swift tools exist, or skip clearly when unavailable.
- `make package-onboarding-beta`: build the trusted-tester `IntentOS.app`
  zip with bundled runtime assets so normal first run does not require a source
  checkout or Terminal commands.
- `make package-onboarding-check`: validate the trusted-tester package contract,
  stable app identity, bundled runtime metadata, and no-Terminal normal path.
- `make cohort-evidence-check`: validate the trusted beta cohort evidence
  template and any optional cohort evidence artifact without raw personal data.
- `make install-beta-app`: copy and open the local beta menu bar app on macOS.
- `make package-extension`: package the internal Chrome bridge extension zip.
- `make chrome-bridge-smoke`: run the manual installed Chrome bridge smoke
  without fake bridge rows and write connected/posting-events evidence.
- `make dogfood-smoke`: run the real 30-minute dogfood beta smoke without the
  fake Chrome bridge, preserving local user data and writing blocked/pass
  evidence.
- `make new-feature name=<slug> class=<class>`: scaffold an active feature
  plan from a next-feature harness class with acceptance criteria and a
  complete Harness Impact section.
- `make adapter-fixture-check`: validate the adapter fixture manifest, current
  capture fixtures, privacy exclusions, JSONL replay, and generated evidence.
- `make diagnose-json`: write a structured `diagnose.json` artifact with app
  state, beta state, event summaries, log summaries, and next commands.
- `make feedback-fixture-candidates`: export privacy-redacted beta correction
  candidates from the local database into ignored runtime artifacts.
- `make review-status`: inspect local branch and GitHub PR/check status when
  `gh` is available, while degrading cleanly offline.
- `make app-status`: show runtime mode, process status when relevant, log
  locations, and UI HTTP health.
- `make app-stop`: stop the local app process started by the harness.
- `make validate-ui`: validate the local UI shell against deterministic runtime
  artifacts and run local headless browser desktop/mobile render checks when
  Chrome or Chromium exists.
- `make update-ui-screenshot`: regenerate the checked-in UI screenshot evidence
  from a local browser.
- `make check-ui-screenshot`: verify that checked-in UI screenshot evidence is
  present and matches the current UI source manifest.
- `make observe`: print local runtime signals that Codex can inspect.
- `make diagnose`: print app state, structured runtime events, validation
  evidence, and recent logs.
- `make observe-live`: run the manual macOS frontmost app/window sensor smoke
  loop, print the latest event, and replay it through the classifier.
- `make observe-session`: run a bounded live metadata session, merge adjacent
  equivalent activity, and replay the resulting timeline.
- `make harness-lint`: validate structural and taste rules that keep the repo
  legible to agents.
- `make verify`: run harness checks plus product checks.

The current product slice now has a static local UI shell. `make dev` first
builds deterministic fixture-backed artifacts: it clears stale live capture
artifacts unless preservation is requested, runs the sample analysis, writes
deterministic reports, normalizes fake capture observations, replays captured
JSONL, copies `web/` into `.harness/runtime/site/`, and serves the UI on a
per-run localhost port recorded in `.harness/runtime/app.env` with
`INTENTOS_APP_DATA_MODE=fixture`. After the UI starts, the harness starts a
visible automated background timeline and records its PID, interval, raw output
path, merged timeline path, status path, and log path in
`.harness/runtime/app.env`. It captures only current frontmost app/window and
browser metadata while the harness is running; it does not read historical app,
browser, or Codex activity.

`make dev-live` is the explicit live-data path: it runs the bounded
`make observe-session` workflow first, preserves the fresh live session replay
artifacts, then starts the UI with `INTENTOS_APP_DATA_MODE=live_session` and a
`?mode=live-session` URL. That URL is strict: if the live session artifact is
missing or broken, the UI shows a live-capture error instead of falling back to
fixture reports. The bounded session artifact stays preferred in the UI even
though the automated background timeline also starts and remains visible in
runtime status.
`make observe-live` and `make observe-session` exercise manual macOS
metadata-only adapters outside CI and write replay artifacts under
`.harness/runtime/`. CI uses fixtures or fake runners for session behavior.

`make beta-dev` is the dogfood beta path. It builds the web shell, starts a
local Python service bound to `127.0.0.1:58917` by default, starts the native
macOS metadata recorder, stores normalized activity in
`.harness/runtime/beta/intentos.sqlite`, writes an isolated
`.harness/runtime/beta/site/beta-config.json`, and starts a local dashboard
with `?mode=beta` so missing service config cannot fall back to fixture
reports. If the service or data path is unavailable, the dashboard shows a
plain-language reconnect notice at the top of the review board rather than raw
developer errors. The web shell hides the legacy YouTube domain panel in every
mode; YouTube activity appears in the normal timeline, activity mix, and
reactive surfaces instead of a separate bottom section. It does not seed fake
rows by default, does not require manual imports or Chrome extension setup for
first beta value, and does not read page bodies, cookies, screenshots,
keystrokes, or cloud services. Use
`INTENTOS_BETA_FAKE_BRIDGE=1 make beta-dev` only for explicit fixture bridge
testing.

The beta service also owns the sticky daily loop, but the dashboard presents it
as a daily plan and evening review. Users can set today's focus and one thing
to avoid, preview how tonight's review will compare that natural language with
captured behavior, then complete an evening review after 5pm local time or
after 2h of captured activity. The loop is stored only in the local beta SQLite
database, exposed through `/api/daily-loop`, `/api/daily-intent`, and
`/api/review-checkin`, and cleared by delete-local-data. `/api/daily-loop`
also returns the deterministic intent contract, focus rescue state,
plan-vs-actual receipts, next block, and correction reward;
`/api/focus-rescue-action` records local shown, return, continue, pause, and
corrected-evidence choices. `/api/status` exposes local activation milestones
for first intent, first rescue state, first recovery choice, and completed
review without sending telemetry. `/api/weekly-patterns` summarizes local
weekly focus, leak, and trust patterns from the same SQLite source state. The
menu bar wrapper surfaces Intent Due, Review Ready, Recovery Available, Avoid
Leaking, Focus Protected, Need Evidence, and Needs Correction states without
requesting notification permission.

`make dogfood-smoke` is the explicit real-machine beta path. It starts the same
local service, dashboard, and native recorder with `INTENTOS_BETA_FAKE_BRIDGE=0`,
runs `/api/permissions/check`, verifies that pause stops row persistence without
stopping recorder heartbeats, observes real SQLite row growth for 30 minutes by
default, and writes `beta-dogfood-smoke.json`,
`beta-dogfood-smoke-daily-review.json`, `beta-dogfood-smoke-dashboard.png`, and
`logs/beta-dogfood-smoke.log`. It does not seed fake rows, create fake
corrections, or call delete-local-data against the dogfood database. Missing
Chrome bridge metadata is a warning when native recorder events are increasing.
The daily review is explicitly scoped as “Today since midnight”; the service
also reports its own start timestamp so the UI can distinguish day totals from
the current app session.

## Runtime State

Local runtime artifacts live under `.harness/runtime/` and are ignored by git.
Expected artifacts after product code exists:

- `.harness/runtime/app.env`: runtime status, process ID when relevant, log
  path, artifact path, runtime mode, data mode, and UI URL.
- `.harness/runtime/beta/app.env`: beta service/UI/native-recorder/fake-bridge
  PID, DB path, service URL, dashboard URL, daily review artifact, and log paths.
- `.harness/runtime/beta/intentos.sqlite`: local dogfood beta database with
  30-day retention, WAL durability, daily intent and review check-in state,
  service-visible `quick_check` health, and truncate checkpointing after
  delete-local-data.
- `.harness/runtime/beta/site/`: isolated beta dashboard shell and service
  config. This keeps dogfood live data separate from fixture UI builds under
  `.harness/runtime/site/`.
- `.harness/runtime/logs/app.log`: app logs.
- `.harness/runtime/logs/events.jsonl`: structured runtime events emitted by
  harness and product scripts.
- `.harness/runtime/logs/live-capture.log`: manual live sensor diagnostic log
  when `make observe-live` is run, and background timeline log when `make dev`
  or `make dev-live` starts the timeline.
- `.harness/runtime/logs/live-session-capture.log`: manual bounded session
  diagnostic log when `make observe-session` is run.
- `.harness/runtime/logs/beta-service.log`: local beta service logs.
- `.harness/runtime/logs/beta-native-recorder.log`: native recorder samples,
  errors, and row-write counts.
- `.harness/runtime/logs/beta-fake-bridge.log`: fake Chrome bridge posts used
  only when `INTENTOS_BETA_FAKE_BRIDGE=1` is requested.
- `.harness/runtime/artifacts/`: screenshots, videos, or validation evidence.
  The current CLI slice writes YouTube, multi-app activity, and fake capture
  replay text/JSON summaries. Manual live capture also writes
  `live-capture-events.jsonl`, `live-capture-summary.txt`, and
  `live-capture-summary.json`; the background timeline also writes
  `live-capture-timeline-events.jsonl` and `live-capture-status.json`. Manual
  live sessions write
  `live-session-capture-events.jsonl`, `live-session-capture-summary.txt`, and
  `live-session-capture-summary.json`.
- `.harness/runtime/artifacts/beta-validation.json`: deterministic beta
  validation evidence.
- `.harness/runtime/artifacts/beta-daily-review.json`: latest beta daily
  review evidence from validation or beta dev.
- `.harness/runtime/artifacts/beta-dogfood-smoke.json`: real beta smoke result
  with permission, native recorder, optional bridge, event-growth, privacy, and
  dashboard evidence.
- `.harness/runtime/artifacts/beta-chrome-bridge-smoke.json`: manual installed
  Chrome bridge smoke result; no fake bridge rows are seeded.
- `.harness/runtime/artifacts/adapter-fixture-check.json`: adapter fixture
  manifest validation, generated JSONL paths, replay status, and failures.
- `.harness/runtime/artifacts/diagnose.json`: structured diagnostics with
  bounded status, event, log, artifact, and recommended-command summaries.
- `.harness/runtime/artifacts/feedback-fixture-candidates.json`: privacy-redacted
  beta correction candidates with raw titles and URLs hashed.
- `.harness/runtime/artifacts/review-status.json`: local branch and optional
  GitHub PR/check status for agent review loops.
- `.harness/runtime/artifacts/beta-dogfood-smoke-daily-review.json`: daily
  review captured during the real dogfood smoke.
- `.harness/runtime/artifacts/beta-dogfood-smoke-dashboard.png`: dashboard
  screenshot evidence from the real dogfood smoke when Chrome/Chromium exists.
- `.harness/runtime/artifacts/IntentOSBeta.app`: local ad-hoc signed dogfood
  menu bar bundle when `make package-beta` builds on macOS.
- `.harness/runtime/artifacts/IntentOS.app`: trusted tester app bundle using
  the stable `local.intentos.trusted` identity.
- `.harness/runtime/artifacts/IntentOS-trusted-beta.zip`: bundled trusted
  tester artifact produced by `make package-onboarding-beta`.
- `.harness/runtime/artifacts/onboarding-beta-package.json`: packaging
  manifest for the bundled trusted tester artifact.
- `.harness/runtime/artifacts/package-onboarding-check.json`: deterministic
  package-contract validation for the trusted tester artifact.
- `.harness/runtime/artifacts/cohort-evidence-check.json`: cohort evidence
  template/result validation for activation, retention, and would-miss signals.
- `.harness/runtime/artifacts/cohort-evidence.json`: optional ignored cohort
  results artifact validated by `make cohort-evidence-check` when present.
- `.harness/runtime/artifacts/IntentOSChromeBridge.zip`: internal Chrome bridge
  package when `make package-extension` runs.
- `.harness/runtime/site/`: generated local UI shell served by `make dev`.

## Product Runtime Contract

Each product runtime implementation must provide one of these:

- `scripts/product/dev.sh`
- `npm run dev`
- A documented alternative added to this file and to
  `scripts/harness/dev.sh`

The implementation must also provide one of these verification paths:

- `npm run lint`, `npm run test`, and `npm run build`
- `python -m pytest` with product tests
- Another explicit product verifier called by `scripts/harness/verify.sh`

IntentOS currently provides `scripts/product/dev.sh`,
`scripts/product/start-ui.sh`, `scripts/product/validate-ui.sh`,
`scripts/product/validate-beta.sh`, `scripts/product/package-beta.sh`,
`scripts/product/install-beta-app.sh`, `scripts/product/package-extension.sh`,
`scripts/product/verify.sh`, `scripts/harness/package-onboarding-check.py`,
`scripts/harness/cohort-evidence-check.py`, `scripts/harness/beta-dev.sh`,
`scripts/harness/beta-status.sh`, `scripts/harness/beta-stop.sh`, and
`scripts/harness/dev-live.sh`.

## UI Validation Contract

`make validate-ui` must:

- Launch or connect to the local app.
- Use a local app shell that can run per worktree without shared mutable state.
- Visit the primary user workflow.
- Validate that the page shell and product JSON artifacts load.
- Write validation evidence into `.harness/runtime/artifacts/`.
- Fail on blank screens, missing JSON artifacts, missing core UI text, missing
  decision cards, missing next move text, horizontal overflow, or clipped text.
- Fail on recurring manual feedback regressions: forbidden developer-facing
  copy, over-dense first viewports, broken section navigation, missing daily
  intent preview updates, or raw service errors in the dashboard.
- Record validation notes in the active execution plan when relevant.

The current validator fetches the page plus JSON artifacts through a temporary
local server in an isolated validation runtime so a running `make dev`
background sampler cannot race deterministic fixture rendering. It writes
`ui-validation.txt`, `ui-validation.json`, and `ui-snapshot.html`, then copies
the `ui-*` evidence back into `.harness/runtime/artifacts/` for diagnostics.
When Chrome or Chromium is available locally, it also captures
`ui-render.png`, `ui-render-mobile.png`, and matching DOM/validation artifacts.
Both fixture and beta validators inject the shared render probe from
`scripts/product/ui-render-probe.js` through
`scripts/product/inject-ui-render-probe.py`; `render-ui-check.py` then enforces
the versioned probe schema, copy policy fixture, first-viewport density budget,
text layout, section navigation, service-state, workflow, and intent-preview
fields. The fixture path covers `fixture-default` and `fixture-long-text`.
It also checks the committed screenshot evidence under
`docs/assets/screenshots/`. Run `make update-ui-screenshot` after UI source,
fixture, or report-output changes. CI requires browser rendering through
`INTENTOS_UI_REQUIRE_BROWSER=1`; local runs may skip it with a clear message
when Chrome/Chromium is unavailable.

`make validate-beta` covers service-backed UI mode. It writes a temporary
`beta-config.json`, confirms the dashboard shell loads while service APIs are
available, checks that correction controls, setup guidance controls, daily
intent controls, evening review controls, decision cards, and next move text are
present, and verifies that a relabel operation changes the next daily-review
response without changing raw events. Rendered beta evidence covers
`beta-ready`, `beta-setup-needed`, `beta-service-stale`, `beta-empty`, and
`beta-intent-missing` so stale services, empty databases, and missing-intent
previews fail with product-facing diagnostics instead of requiring manual
inspection.

Trusted beta stickiness harness support is split between deterministic checks
and manual cohort evidence. `make package-onboarding-check` verifies the
downloadable tester artifact contract even on machines that cannot build the
Swift app, including a menu-bar stale-dashboard guard: the trusted app must
verify recorded service and UI PIDs before trusting a saved dashboard URL, and
must restart the beta when the recorded runtime is stale. `make
cohort-evidence-check` validates
`data/beta/cohort_evidence_template.json` and, when present, the ignored
`.harness/runtime/artifacts/cohort-evidence.json` file. Cohort evidence must
record days completed, setup minutes, first captured app/window, first live
state, evening review completion, correction themes, would-miss answer, and
the harness or quality artifact that repeated feedback maps to. When an
evidence artifact exists, the check fails unless it meets the current demand
targets: five three-day testers, three seven-day testers, two would-miss-yes
answers, and median setup at or below five minutes.

## Observability Contract

When IntentOS has a runtime service, `make observe` must expose:

- Recent app logs in a structured, queryable format.
- Startup timing.
- Errors and warnings.
- Product-specific counters or metrics when available.

For early local-only builds, line-oriented logs are enough, but new capture,
classification, and reporting paths should log stable fields such as
`component`, `event`, `mode`, `artifact_path`, `duration_ms`, `event_count`,
and `status`. Add metrics and traces when the runtime grows beyond a single
local process.

Use `make diagnose` when a future agent needs the fastest full runtime picture:
it prints `app.env`, recent structured events, UI validation evidence, and the
recent app log.

## Live Capture Runtime Contract

When a live capture slice exists, fixture and live commands must make these
visible:

- capture mode: fixture, fake sensor, manual live sensor, background timeline,
  or replay
- permission state for Accessibility permission, browser automation, and future
  Screen Recording
- output path for raw local `ActivityEvent` JSONL
- timeline output path for merged user-facing `ActivityEvent` JSONL
- redaction/exclusion policy loaded by the runtime
- latest classification summary from replay, including
  `live-capture-summary.json` for UI consumption

For IntentOS today, the split is intentional:

- `make dev`: fixture-backed UI plus automated background timeline. The product
  artifact build clears stale live artifacts before serving, then the harness
  starts a visible background timeline so fresh current-session metadata is
  explicit in app status. Raw diagnostic rows stay separate from the merged
  timeline summary shown in the UI.
- `make observe-session`: manual live capture diagnostic only. It writes live
  artifacts but does not start or restart the UI.
- `make dev-live`: live session UI. It captures a fresh bounded live session,
  preserves the resulting live artifacts, serves the UI against them, and keeps
  the automated background timeline visible separately in app status.

CI must use fixture or fake-sensor mode. Manual live-sensor mode may require
local macOS permissions and should not block `make verify`.

Manual live macOS smoke command:

```sh
make observe-live
```

Equivalent explicit commands:

```sh
python3 -m intentos.capture_cli capture-macos --duration-seconds 5 --output .harness/runtime/artifacts/live-capture-events.jsonl
python3 -m intentos.capture_cli replay .harness/runtime/artifacts/live-capture-events.jsonl --allow-empty
```

`make observe-live` is expected to fail with a clear permission message if
Accessibility access is missing. Browser Automation failures should degrade to
app/window metadata when possible. Privacy exclusions can produce zero captured
rows; the harness still writes an empty replay summary. It must not be added to
`make verify` because the result depends on live macOS state.

Manual live session smoke command:

```sh
make observe-session
```

Equivalent explicit commands:

```sh
python3 -m intentos.capture_cli capture-session --duration-seconds 30 --interval-seconds 5 --output .harness/runtime/artifacts/live-session-capture-events.jsonl
python3 -m intentos.capture_cli replay .harness/runtime/artifacts/live-session-capture-events.jsonl --allow-empty
```

Manual live diagnostics stay outside CI, while parser, merge, privacy, replay,
and UI timeline behavior are covered by deterministic fixtures in
`make verify`.

Current capture artifacts:

- `capture-events.jsonl`
- `capture-normalize.log`
- `capture-summary.txt`
- `capture-summary.json`
- `live-capture-events.jsonl`
- `live-capture-timeline-events.jsonl`
- `live-capture-summary.txt`
- `live-capture-summary.json`
- `live-capture-status.json`
- `session-capture-events.jsonl`
- `session-capture-summary.txt`
- `session-capture-summary.json`
- `live-session-capture-events.jsonl`
- `live-session-capture-summary.txt`
- `live-session-capture-summary.json`
- `ui-validation.txt`
- `ui-validation.json`
- `ui-snapshot.html`
- checked-in `docs/assets/screenshots/intent-os-ui.png`
- checked-in `docs/assets/screenshots/intent-os-ui.json`

## Future Feature Runtime Contract

Upcoming features must follow [HARNESS_FEATURES.md](HARNESS_FEATURES.md).
Manual import artifacts are useful for developer fixtures, but they are not the
preferred user-facing path. Automated sources such as browser extension
metadata, calendar or planned-intent context, Accessibility excerpts, IDE/Git
context, daily narratives, ScreenCaptureKit/OCR, and local model slices must
use stable artifact names, structured runtime events, deterministic fixtures,
and permission-free `make verify` coverage.

Before implementation starts, the active execution plan must include a
`## Harness Impact` section that names the runtime commands, artifacts,
fixtures or fakes, UI validation, diagnostics, privacy or permission behavior,
and docs or harness checks affected by the use-case. If a category does not
apply, the plan should say that explicitly so future agents do not infer hidden
manual work.
