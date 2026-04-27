# intent-os

IntentOS is a local-first personal behavior intelligence system. It is not a
time tracker. It classifies digital activity by behavioral intent so a user can
understand whether time was spent on deep work, learning, communication, admin,
passive consumption, entertainment, or unknown activity.

This repository is also an agent-first product harness. Codex should be able to
read the docs, choose the next scoped plan, implement the slice, verify it, and,
when explicitly asked, open, review, and merge a PR once checks pass.

## Current Product Surface

- Generic multi-app `ActivityEvent` classification.
- YouTube-specific fixture classification from the first MVP slice.
- Deterministic local fixtures and labeled evaluation sets.
- CLI reports and JSON reports.
- Local UI shell served from generated runtime artifacts.
- Checked-in UI screenshot evidence guarded by a source manifest.
- Metadata-only fake-sensor capture normalization and replay.
- Manual metadata-only macOS frontmost app/window capture with best-effort
  browser tab URL/title enrichment.
- Visible automated background timeline for local UI runs, with raw diagnostic
  samples, merged timeline artifacts, and status recorded in
  `.harness/runtime/app.env`.
- Dogfood beta harness with a local Python service, SQLite persistence,
  Chrome extension bridge fixture, service-backed daily review UI, correction
  controls, pause/resume, delete-local-data, and local Swift menu bar packaging.
- Short live capture session timeline support that repeatedly samples
  metadata, merges adjacent equivalent activity, and renders a timeline in the
  UI.
- Harness checks, architecture linting, cleanup checks, runtime artifacts, and
  CI running `make verify`.
- Live-capture and on-device inference specs for the next macOS slices.

The first real live sensor is intentionally narrow: it samples the current
frontmost macOS app/window through local System Events metadata, enriches active
browser URL/title when Automation permission allows it, and writes
`ActivityEvent` JSONL. The current session slice samples that metadata
repeatedly over a bounded manual run, merges adjacent equivalent activity, and
shows the timeline in the local UI. ScreenCaptureKit, OCR, local model
inference, and richer DOM automation remain future extensions after the
metadata path is reliable.

## Start Here

- [AGENTS.md](./AGENTS.md): short map Codex should read first.
- [docs/README.md](./docs/README.md): full repository knowledge index.
- [docs/product/BRIEF.md](./docs/product/BRIEF.md): product source of truth.
- [docs/product/TAXONOMY.md](./docs/product/TAXONOMY.md): behavior labels and
  classification rules of thumb.
- [docs/product/live-capture.md](./docs/product/live-capture.md): macOS capture
  strategy and privacy defaults.
- [docs/product/on-device-inference.md](./docs/product/on-device-inference.md):
  local model and rules-first inference strategy.
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md): current layers and dependency
  rules.
- [docs/architecture/long-term-plan.md](./docs/architecture/long-term-plan.md):
  long-term architecture diagram and harness-readable roadmap graph.
- [docs/HARNESS_AUDIT.md](./docs/HARNESS_AUDIT.md): status against the OpenAI
  Harness Engineering model.
- [docs/HARNESS_FEATURES.md](./docs/HARNESS_FEATURES.md): harness contracts
  for upcoming import, narrative, fallback-capture, model, and UI automation
  slices.
- [docs/NEXT_STEPS.md](./docs/NEXT_STEPS.md): recommended next slices.
- [docs/plans/README.md](./docs/plans/README.md): execution plan workflow.

## Common Commands

```sh
make harness-check
make harness-lint
make harness-status
make cleanup-check
make verify
make dev
make dev-live
make beta-dev
make beta-status
make beta-stop
make validate-beta
make package-beta
make app-status
make diagnose
make validate-ui
make update-ui-screenshot
make observe
make observe-live
make observe-session
```

Run the current product:

```sh
python3 -m intentos.capture_cli normalize-observations data/capture/fake_macos_observations.json --browser-tabs data/capture/fake_browser_tabs.json --output .harness/runtime/artifacts/capture-events.jsonl
python3 -m intentos.capture_cli replay .harness/runtime/artifacts/capture-events.jsonl
python3 -m intentos.capture_cli capture-macos --duration-seconds 5 --output .harness/runtime/artifacts/live-capture-events.jsonl
python3 -m intentos.capture_cli capture-session --duration-seconds 30 --interval-seconds 5 --output .harness/runtime/artifacts/live-session-capture-events.jsonl
python3 -m intentos.capture_cli normalize-observations data/capture/fake_session_observations.json --merge-adjacent --output .harness/runtime/artifacts/session-capture-events.jsonl
python3 -m intentos.activity_cli data/activity/multi_app_events.json
python3 -m intentos.activity_evaluate data/activity/evaluation_set.json --min-accuracy 85
python3 -m intentos.cli data/youtube/sample_watch_history.json
```

`make observe-live` runs the manual macOS frontmost app/window smoke loop,
writes `.harness/runtime/artifacts/live-capture-events.jsonl`, replays it
through the classifier, writes `live-capture-summary.json`, and writes
`.harness/runtime/logs/live-capture.log`. It may require Accessibility and
Automation permissions for the Codex host app or terminal. CI uses deterministic
fixtures instead of live macOS state. If privacy rules exclude every live row,
the command still writes a valid empty replay summary for the UI.

`make observe-session` runs the bounded live session diagnostic. It writes
`live-session-capture-events.jsonl`, replays it into
`live-session-capture-summary.json`, and records `.harness/runtime/logs/live-session-capture.log`.
The session command stays outside CI because it depends on live macOS state;
`make verify` covers equivalent behavior through
`data/capture/fake_session_observations.json`.

`make dev` rebuilds deterministic fixture summaries, clears stale live capture
artifacts during the product artifact build, serves the UI URL recorded in
`.harness/runtime/app.env`, records `INTENTOS_APP_DATA_MODE=fixture`, and then
starts a visible automated background timeline. The sampler writes raw
diagnostic rows to `live-capture-events.jsonl`, merges adjacent equivalent
activity into `live-capture-timeline-events.jsonl`, refreshes
`live-capture-summary.json` from that merged timeline, and writes
`live-capture-status.json`; its PID, timeline path, and log path are recorded
in `.harness/runtime/app.env`. It captures only current frontmost app/window
and browser metadata while the harness is running, and it does not backfill
historical activity. Stop it with `make app-stop`.

`make dev-live` is the explicit real macOS flow. It runs `make observe-session`
first, preserves the fresh `live-session-capture-summary.json`, then starts the
UI with `INTENTOS_APP_DATA_MODE=live_session`. The bounded session artifact
stays preferred in the UI, while the same automated background timeline remains
visible in runtime status. It only captures activity during those command
windows and may require Accessibility or browser Automation permissions.

`make beta-dev` starts the dogfood beta harness: a local service bound to
`127.0.0.1`, a SQLite database at `.harness/runtime/beta/intentos.sqlite`, the
service-backed dashboard, and a fake Chrome bridge that posts bounded tab
metadata with no manual exports or imports. The dashboard automatically uses
service APIs when `.harness/runtime/site/beta-config.json` exists and otherwise
falls back to fixture artifacts. Use `make beta-status` for service PID, DB,
capture, extension, pause, row-count, and log diagnostics, and `make beta-stop`
to stop the beta processes. `make validate-beta` runs deterministic API,
persistence, privacy, correction, delete-data, and UI smoke checks against a
temp DB. `make package-beta` builds the local unsigned Swift menu bar bundle
under `.harness/runtime/artifacts/IntentOSBeta.app` when macOS Swift tools are
available, and skips clearly otherwise.

`make update-ui-screenshot` refreshes the checked-in UI screenshot at
`docs/assets/screenshots/intent-os-ui.png`. `make verify` checks that screenshot
manifest so UI source changes cannot leave stale visual evidence behind.
`make diagnose` prints app state, structured runtime events, UI validation
evidence, and recent logs.

Create a scoped execution plan with:

```sh
scripts/harness/new-plan.sh first-product-slice
```

Then fill in the generated plan under `docs/plans/active/` and prompt Codex to
implement that plan end to end.

`make verify` is the main merge gate. It runs harness checks, structural
linting, repository audit, unit tests, YouTube fixture evaluation, multi-app
fixture evaluation, capture replay and session replay checks, UI validation
with optional headless browser render diagnostics, and screenshot freshness
checks.

## Next Work

See [docs/NEXT_STEPS.md](./docs/NEXT_STEPS.md). Recommended next work now moves
toward dogfood beta hardening, permission UX, and richer behavior narratives on
top of the service-backed daily review. Future feature work should satisfy
[docs/HARNESS_FEATURES.md](./docs/HARNESS_FEATURES.md) before it is considered
complete.
