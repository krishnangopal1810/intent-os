# App Runtime Harness

Codex must be able to run, inspect, and validate the product locally. Product
runtime commands can be one-shot for CLI slices or persistent for UI/service
slices.

## Commands

- `make dev`: generate fixture-backed product artifacts, launch the local UI
  shell for the current worktree, and start the visible background metadata
  sampler.
- `make dev-live`: run a fresh bounded macOS live session, preserve its replay
  artifact, and launch the local UI shell against that live session summary.
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
visible background metadata sampler and records its PID, interval, output path,
status path, and log path in `.harness/runtime/app.env`. It captures only
current frontmost app/window and browser metadata while the harness is running;
it does not read historical app, browser, or Codex activity.

`make dev-live` is the explicit live-data path: it runs the bounded
`make observe-session` workflow first, preserves the fresh live session replay
artifacts, then starts the UI with `INTENTOS_APP_DATA_MODE=live_session`.
The bounded session artifact stays preferred in the UI even though the
background sampler also starts and remains visible in runtime status.
`make observe-live` and `make observe-session` exercise manual macOS
metadata-only adapters outside CI and write replay artifacts under
`.harness/runtime/`. CI uses fixtures or fake runners for session behavior.

## Runtime State

Local runtime artifacts live under `.harness/runtime/` and are ignored by git.
Expected artifacts after product code exists:

- `.harness/runtime/app.env`: runtime status, process ID when relevant, log
  path, artifact path, runtime mode, data mode, and UI URL.
- `.harness/runtime/logs/app.log`: app logs.
- `.harness/runtime/logs/events.jsonl`: structured runtime events emitted by
  harness and product scripts.
- `.harness/runtime/logs/live-capture.log`: manual live sensor diagnostic log
  when `make observe-live` is run, and background sampler log when `make dev`
  or `make dev-live` starts the sampler.
- `.harness/runtime/logs/live-session-capture.log`: manual bounded session
  diagnostic log when `make observe-session` is run.
- `.harness/runtime/artifacts/`: screenshots, videos, or validation evidence.
  The current CLI slice writes YouTube, multi-app activity, and fake capture
  replay text/JSON summaries. Manual live capture also writes
  `live-capture-events.jsonl`, `live-capture-summary.txt`, and
  `live-capture-summary.json`; the background sampler also writes
  `live-capture-status.json`. Manual live sessions write
  `live-session-capture-events.jsonl`, `live-session-capture-summary.txt`, and
  `live-session-capture-summary.json`.
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
`scripts/product/verify.sh`, and `scripts/harness/dev-live.sh`.

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

- capture mode: fixture, fake sensor, manual live sensor, or replay
- permission state for Accessibility permission, browser automation, and future
  Screen Recording
- output path for local `ActivityEvent` JSONL
- redaction/exclusion policy loaded by the runtime
- latest classification summary from replay, including
  `live-capture-summary.json` for UI consumption

For IntentOS today, the split is intentional:

- `make dev`: fixture-backed UI plus background sampler. The product artifact
  build clears stale live artifacts before serving, then the harness starts a
  visible background live sensor so fresh current-session metadata is explicit
  in app status.
- `make observe-session`: manual live capture diagnostic only. It writes live
  artifacts but does not start or restart the UI.
- `make dev-live`: live session UI. It captures a fresh bounded live session,
  preserves the resulting live artifacts, serves the UI against them, and keeps
  the background sampler visible separately in app status.

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

Upcoming features must follow [HARNESS_FEATURES.md](HARNESS_FEATURES.md). The
manual import slice should add `import-events.jsonl`, `import-summary.txt`,
`import-summary.json`, and `import-validation.json` under
`.harness/runtime/artifacts/`. Later browser history, ChatGPT export, daily
narrative, ScreenCaptureKit/OCR, and local model slices must use similarly
stable artifact names, structured runtime events, deterministic fixtures, and
permission-free `make verify` coverage.
