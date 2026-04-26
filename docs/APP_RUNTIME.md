# App Runtime Harness

Codex must be able to run, inspect, and validate the product locally. Product
runtime commands can be one-shot for CLI slices or persistent for UI/service
slices.

## Commands

- `make dev`: generate current product artifacts and launch the local UI shell
  for the current worktree.
- `make app-status`: show runtime mode, process status when relevant, log
  locations, and UI HTTP health.
- `make app-stop`: stop the local app process started by the harness.
- `make validate-ui`: validate the local UI shell against deterministic runtime
  artifacts.
- `make observe`: print local runtime signals that Codex can inspect.
- `make diagnose`: print app state, structured runtime events, validation
  evidence, and recent logs.
- `make observe-live`: run the manual macOS frontmost app/window sensor smoke
  loop, print the latest event, and replay it through the classifier.
- `make harness-lint`: validate structural and taste rules that keep the repo
  legible to agents.
- `make verify`: run harness checks plus product checks.

The current product slice now has a static local UI shell. `make dev` runs the
sample analysis, writes reports, normalizes fake capture observations, replays
captured JSONL, copies `web/` into `.harness/runtime/site/`, and serves the UI
on a per-run localhost port recorded in `.harness/runtime/app.env`. `make
observe-live` exercises the manual macOS metadata-only adapter outside CI.
Future live capture runtime commands must expose the capture mode, permission
state, output JSONL path, and latest classifier replay summary.

## Runtime State

Local runtime artifacts live under `.harness/runtime/` and are ignored by git.
Expected artifacts after product code exists:

- `.harness/runtime/app.env`: runtime status, process ID when relevant, log
  path, artifact path, runtime mode, and UI URL.
- `.harness/runtime/logs/app.log`: app logs.
- `.harness/runtime/logs/events.jsonl`: structured runtime events emitted by
  harness and product scripts.
- `.harness/runtime/logs/live-capture.log`: manual live sensor diagnostic log
  when `make observe-live` is run.
- `.harness/runtime/artifacts/`: screenshots, videos, or validation evidence.
  The current CLI slice writes YouTube, multi-app activity, and fake capture
  replay text/JSON summaries. Manual live capture also writes
  `live-capture-events.jsonl`.
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
`scripts/product/start-ui.sh`, `scripts/product/validate-ui.sh`, and
`scripts/product/verify.sh`.

## UI Validation Contract

`make validate-ui` must:

- Launch or connect to the local app.
- Use a local app shell that can run per worktree without shared mutable state.
- Visit the primary user workflow.
- Validate that the page shell and product JSON artifacts load.
- Write validation evidence into `.harness/runtime/artifacts/`.
- Fail on blank screens, missing JSON artifacts, or missing core UI text.
- Record validation notes in the active execution plan when relevant.

The current validator is dependency-free and fetches the page plus JSON
artifacts through a temporary local server. It writes `ui-validation.txt`,
`ui-validation.json`, and `ui-snapshot.html`. Add screenshot and DOM automation
when the repo introduces a browser automation dependency.

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

When a live capture slice exists, `make dev` or a documented product command
must make these visible:

- capture mode: fixture, fake sensor, manual live sensor, or replay
- permission state for Accessibility permission, browser automation, and future
  Screen Recording
- output path for local `ActivityEvent` JSONL
- redaction/exclusion policy loaded by the runtime
- latest classification summary from replay

CI must use fixture or fake-sensor mode. Manual live-sensor mode may require
local macOS permissions and should not block `make verify`.

Manual live macOS smoke command:

```sh
make observe-live
```

Equivalent explicit commands:

```sh
python3 -m intentos.capture_cli capture-macos --duration-seconds 5 --output .harness/runtime/artifacts/live-capture-events.jsonl
python3 -m intentos.capture_cli replay .harness/runtime/artifacts/live-capture-events.jsonl
```

`make observe-live` is expected to fail with a clear permission message if
Accessibility or Automation access is missing. It must not be added to
`make verify` because the result depends on live macOS state.

Current capture artifacts:

- `capture-events.jsonl`
- `capture-normalize.log`
- `capture-summary.txt`
- `capture-summary.json`
- `live-capture-events.jsonl`
- `ui-validation.txt`
- `ui-validation.json`
- `ui-snapshot.html`
