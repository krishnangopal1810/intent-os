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
- `make beta-dev`: start the dogfood beta service, SQLite DB, service-backed
  dashboard, and fake Chrome bridge in harness mode.
- `make beta-status`: show beta service PID, DB path, capture state, pause
  state, extension bridge state, last event time, row counts, and log paths.
- `make beta-stop`: stop beta service, fake bridge, and beta UI processes.
- `make validate-beta`: run deterministic beta API, persistence, correction,
  privacy, delete-data, and UI smoke checks against a temp DB.
- `make package-beta`: build the local unsigned Swift menu bar app bundle when
  macOS Swift tools exist, or skip clearly when unavailable.
- `make app-status`: show runtime mode, process status when relevant, log
  locations, and UI HTTP health.
- `make app-stop`: stop the local app process started by the harness.
- `make validate-ui`: validate the local UI shell against deterministic runtime
  artifacts and run local headless browser render checks when Chrome or
  Chromium exists.
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
artifacts, then starts the UI with `INTENTOS_APP_DATA_MODE=live_session`.
The bounded session artifact stays preferred in the UI even though the
automated background timeline also starts and remains visible in runtime
status.
`make observe-live` and `make observe-session` exercise manual macOS
metadata-only adapters outside CI and write replay artifacts under
`.harness/runtime/`. CI uses fixtures or fake runners for session behavior.

`make beta-dev` is the dogfood beta path. It builds the web shell, starts a
local Python service bound to `127.0.0.1`, stores normalized activity in
`.harness/runtime/beta/intentos.sqlite`, writes
`.harness/runtime/site/beta-config.json`, starts a local dashboard, and posts
fixture Chrome tab metadata through the same `/api/browser-event` endpoint used
by the Chrome extension bridge. It does not require manual imports and does not
read page bodies, cookies, screenshots, keystrokes, or cloud services.

## Runtime State

Local runtime artifacts live under `.harness/runtime/` and are ignored by git.
Expected artifacts after product code exists:

- `.harness/runtime/app.env`: runtime status, process ID when relevant, log
  path, artifact path, runtime mode, data mode, and UI URL.
- `.harness/runtime/beta/app.env`: beta service/UI/fake-bridge PID, DB path,
  service URL, dashboard URL, daily review artifact, and log paths.
- `.harness/runtime/beta/intentos.sqlite`: local dogfood beta database with
  30-day retention.
- `.harness/runtime/logs/app.log`: app logs.
- `.harness/runtime/logs/events.jsonl`: structured runtime events emitted by
  harness and product scripts.
- `.harness/runtime/logs/live-capture.log`: manual live sensor diagnostic log
  when `make observe-live` is run, and background timeline log when `make dev`
  or `make dev-live` starts the timeline.
- `.harness/runtime/logs/live-session-capture.log`: manual bounded session
  diagnostic log when `make observe-session` is run.
- `.harness/runtime/logs/beta-service.log`: local beta service logs.
- `.harness/runtime/logs/beta-fake-bridge.log`: fake Chrome bridge posts used
  in harness mode.
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
- `.harness/runtime/artifacts/IntentOSBeta.app`: local unsigned dogfood menu
  bar bundle when `make package-beta` builds on macOS.
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
`scripts/product/verify.sh`, `scripts/harness/beta-dev.sh`,
`scripts/harness/beta-status.sh`, `scripts/harness/beta-stop.sh`, and
`scripts/harness/dev-live.sh`.

## UI Validation Contract

`make validate-ui` must:

- Launch or connect to the local app.
- Use a local app shell that can run per worktree without shared mutable state.
- Visit the primary user workflow.
- Validate that the page shell and product JSON artifacts load.
- Write validation evidence into `.harness/runtime/artifacts/`.
- Fail on blank screens, missing JSON artifacts, or missing core UI text.
- Record validation notes in the active execution plan when relevant.

The current validator fetches the page plus JSON artifacts through a temporary
local server. It writes `ui-validation.txt`, `ui-validation.json`, and
`ui-snapshot.html`. When Chrome or Chromium is available locally, it also
captures `ui-render.png` and checks that the rendered screenshot is non-blank.
If the local browser can also dump the rendered DOM probe, the validator checks
for horizontal overflow, clipped visible text, and expected capture events. It
also checks the committed screenshot evidence under `docs/assets/screenshots/`.
Run `make update-ui-screenshot` after UI source, fixture, or report-output
changes. CI does not need Chrome to validate the committed screenshot; the
screenshot metadata records a source hash and `make verify` fails when the
image is stale.

`make validate-beta` covers service-backed UI mode. It writes a temporary
`beta-config.json`, confirms the dashboard shell loads while service APIs are
available, checks that correction controls are present, and verifies that a
relabel operation changes the next daily-review response without changing raw
events.

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
