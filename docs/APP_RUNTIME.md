# App Runtime Harness

Codex must be able to run, inspect, and validate the product locally. Product
runtime commands can be one-shot for CLI slices or persistent for UI/service
slices.

## Commands

- `make dev`: run the current CLI runtime or launch the app for the current
  worktree.
- `make app-status`: show runtime mode, process status when relevant, and log
  locations.
- `make app-stop`: stop the local app process started by the harness.
- `make validate-ui`: drive the UI through browser automation when a UI exists.
- `make observe`: print local runtime signals that Codex can inspect.
- `make harness-lint`: validate structural and taste rules that keep the repo
  legible to agents.
- `make verify`: run harness checks plus product checks.

The current product slice is CLI-first. `make dev` runs the sample analysis,
writes reports, and keeps the generated summary visible through the runtime log.
Future live capture runtime commands must expose the capture mode, permission
state, output JSONL path, and latest classifier replay summary.

## Runtime State

Local runtime artifacts live under `.harness/runtime/` and are ignored by git.
Expected artifacts after product code exists:

- `.harness/runtime/app.env`: runtime status, process ID when relevant, log
  path, artifact path, and runtime mode.
- `.harness/runtime/logs/app.log`: app logs.
- `.harness/runtime/artifacts/`: screenshots, videos, or validation evidence.
  The current CLI slice writes YouTube and multi-app activity text/JSON
  summaries.

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

IntentOS currently provides `scripts/product/dev.sh` and
`scripts/product/verify.sh`.

## UI Validation Contract

When IntentOS has a UI, `make validate-ui` must:

- Launch or connect to the local app.
- Visit the primary user workflow.
- Capture at least one screenshot into `.harness/runtime/artifacts/`.
- Fail on blank screens, console errors, or missing core UI text.
- Record validation notes in the active execution plan when relevant.

## Observability Contract

When IntentOS has a runtime service, `make observe` must expose:

- Recent app logs.
- Startup timing.
- Errors and warnings.
- Product-specific counters or metrics when available.

For early local-only builds, text logs are enough. Add metrics and traces when
the runtime grows beyond a single local process.

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
