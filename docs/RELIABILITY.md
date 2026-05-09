# Reliability

The current product runtime is a local Python CLI that generates inspectable
artifacts.

## Local Reliability Expectations

- The app should be runnable from a fresh checkout with documented commands.
- Startup failures should be visible in logs.
- Tests should cover core product workflows.
- UI workflows should be verifiable through `make validate-ui`; when Chrome or
  Chromium exists locally, validation should include a headless browser render
  check for blank pages and, when the browser can dump the rendered DOM probe,
  basic layout failures. Checked-in screenshot evidence should be refreshed
  with `make update-ui-screenshot` whenever rendered UI behavior changes.
- Long-running tasks should expose progress and recoverable errors.
- Live capture adapters should have fixture or fake-based tests so CI does not
  require macOS permissions.
- Manual sensor smoke tests should record enough runtime evidence for Codex to
  inspect logs and generated `ActivityEvent` JSONL.
- Upcoming automated source, narrative, fallback-capture, model, and UI
  automation slices should satisfy `docs/HARNESS_FEATURES.md` before depending
  on manual inspection.
- New adapters should be registered in the adapter fixture manifest and pass
  `make adapter-fixture-check` before relying on live behavior.
- Runtime handoffs should include `make diagnose-json` when text diagnostics
  are not enough; the artifact is `.harness/runtime/artifacts/diagnose.json`.

## Verification Targets

- `make harness-check` validates harness structure.
- `make harness-lint` validates layer boundaries, taste constraints, generated
  file hygiene, plan hygiene, and evaluation set coverage.
- `make verify` runs harness checks and detected product checks.
- `.github/workflows/verify.yml` runs `make verify` in CI.
- `.github/workflows/trusted-beta-artifact.yml` runs
  `make package-onboarding-beta` and `make package-onboarding-check` on macOS
  CI, then uploads the generated `IntentOS-trusted-beta.zip` and package
  reports as workflow artifacts.
- `make dev`, `make dev-live`, `make beta-dev`, `make beta-status`,
  `make beta-stop`, `make validate-beta`, `make package-beta`,
  `make app-status`, `make validate-ui`, `make observe`, and
  `make diagnose` provide local runtime legibility for the current UI-backed
  product.
- `make observe-live` provides manual local sensor diagnostics for the macOS
  frontmost app/window adapter.
- `make observe-session` provides manual bounded session diagnostics for the
  repeated metadata sampler and timeline merge path.
- `make validate-ui` validates the local UI shell, JSON artifact loading, and
  optional local browser render diagnostics.
- `make validate-beta` validates beta APIs, SQLite persistence, Chrome bridge
  privacy filtering, correction layering, pause/resume, delete-local-data, and
  service-backed UI loading against a temp DB.
- `make dogfood-smoke` validates the real dogfood runtime with live native
  recorder row growth, permission preflight, pause privacy behavior, SQLite
  health, and dashboard evidence. It preserves the dogfood database and must
  report exact blockers when permissions or capture health are not ready.
- `make chrome-bridge-smoke` validates that an installed Chrome bridge reaches
  connected or posting-events without enabling fake bridge rows.
- `make adapter-fixture-check` validates the capture adapter fixture manifest,
  privacy exclusions, JSONL output, and replay behavior.
- `make diagnose-json`, `make feedback-fixture-candidates`, and `make
  review-status` provide structured diagnostics, privacy-redacted correction
  candidates, and optional PR/check triage evidence.
- `make check-ui-screenshot` verifies that checked-in screenshot evidence is
  present and fresh for the current UI/report inputs.

## Product Commands

- `python3 -m intentos.cli data/youtube/sample_watch_history.json`
- `python3 -m intentos.cli data/youtube/sample_watch_history.json --json`
- `python3 -m intentos.activity_cli data/activity/multi_app_events.json`
- `python3 -m intentos.activity_cli data/activity/multi_app_events.json --json`
- `python3 -m intentos.capture_cli normalize-observations data/capture/fake_macos_observations.json --browser-tabs data/capture/fake_browser_tabs.json --output .harness/runtime/artifacts/capture-events.jsonl`
- `python3 -m intentos.capture_cli normalize-observations data/capture/fake_session_observations.json --merge-adjacent --output .harness/runtime/artifacts/session-capture-events.jsonl`
- `python3 -m intentos.capture_cli replay .harness/runtime/artifacts/capture-events.jsonl`
- `python3 -m intentos.capture_cli capture-macos --duration-seconds 5 --output .harness/runtime/artifacts/live-capture-events.jsonl`
- `python3 -m intentos.capture_cli capture-session --duration-seconds 30 --interval-seconds 5 --output .harness/runtime/artifacts/live-session-capture-events.jsonl`
- `python3 -m intentos.beta_cli serve --db .harness/runtime/beta/intentos.sqlite --port 58917`
- `python3 -m intentos.beta_cli fake-bridge --service-url http://127.0.0.1:58917/api/browser-event --once`
- `python3 -m intentos.beta_cli daily-review --db .harness/runtime/beta/intentos.sqlite --date 2026-04-27 --output .harness/runtime/artifacts/beta-daily-review.json`
- `make observe-live`
- `make observe-session`
- `make dev-live`
- `make beta-dev`
- `make beta-status`
- `make validate-beta`
- `make dogfood-smoke`
- `make package-beta`
- `scripts/product/verify.sh`
- `make verify`
- `make cleanup-check`
- `make validate-ui`
- `make diagnose`
- `python3 -m intentos.evaluate data/youtube/evaluation_set.json --min-accuracy 90`
- `python3 -m intentos.activity_evaluate data/activity/evaluation_set.json --min-accuracy 85`

## Runtime Notes

`make dev` builds fixture-backed product artifacts first. That product artifact
step clears stale live capture artifacts, runs the sample analysis, writes
deterministic text and JSON reports under `.harness/runtime/artifacts/`, serves
the local UI shell, records its URL, process, and
`INTENTOS_APP_DATA_MODE=fixture` in `.harness/runtime/app.env`, and writes
runtime logs. After the UI starts, the harness starts a visible background
timeline and records its capture mode, PID, raw output path, merged timeline
path, status path, and log path in `.harness/runtime/app.env`. It captures only
current frontmost app/window and browser metadata while the harness is running,
and it does not read historical activity.

`make dev-live` is the explicit real macOS UI path. It runs a fresh bounded
`make observe-session`, preserves the live replay artifact, starts the UI, and
records `INTENTOS_APP_DATA_MODE=live_session`. The UI then prefers activity
captured during that bounded live command window, while the automated
background timeline remains separately visible in runtime status. `make observe`
shows structured events plus the app log. `make diagnose` prints app
state, structured events, UI validation evidence, and app logs in one place.

`make observe-live` writes `.harness/runtime/logs/live-capture.log`, captures
one live local metadata event, and replays it through the classifier. If privacy
rules exclude every row, it still writes a valid empty replay summary so the UI
and diagnostics remain inspectable.

`make observe-session` writes `.harness/runtime/logs/live-session-capture.log`,
captures repeated live metadata samples for a bounded duration, applies privacy
exclusions, merges adjacent equivalent activity, and replays the resulting
timeline. It records structured runtime events for session start/completion,
duration, interval, output path, and replay artifact.

`make beta-dev` writes `.harness/runtime/beta/app.env`, starts the beta service
and native recorder, and serves an isolated dashboard in service-backed beta
mode. The dashboard is launched with `?mode=beta`; if service config is missing
or broken, the UI shows a live-service problem instead of fixture reports.
Explicit live-session URLs follow the same rule for live artifacts. The service
status reports DB path, retention, pause state, extension state, latest event
time, row counts, SQLite `quick_check`, WAL/SHM file sizes, native-recorder
heartbeat freshness, and log paths. A running recorder whose heartbeat goes
stale is reported as a capture issue instead of silently looking healthy.
`make validate-beta` uses the same API surface
with a temporary DB and writes `beta-validation.json` plus
`beta-daily-review.json` as reproducible evidence.

The beta pause control is treated as a privacy control. While pause is active,
the native recorder must keep health heartbeats fresh but must not persist new
activity rows. `make dogfood-smoke` verifies that row counts remain stable
while paused, then resumes capture before measuring live row growth.

The beta service enables SQLite WAL mode for local durability. Startup and
retention cleanup run passive checkpoints, and delete-local-data clears user
tables plus generated beta review/smoke artifacts while preserving runtime
status rows that explain the service state. The delete path finishes with a
truncate checkpoint so a user-visible reset does not leave old user data sitting
in the WAL file.

Future persistent runtime code should emit structured, line-oriented logs with
stable fields for `component`, `event`, `mode`, `artifact_path`, `duration_ms`,
`event_count`, and `status` so Codex can inspect capture, classification, and
reporting behavior without reading ad hoc prose.

Current artifacts:

- `youtube-summary.txt`
- `youtube-summary.json`
- `activity-summary.txt`
- `activity-summary.json`
- `capture-events.jsonl`
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
- `ui-render.png`
- `ui-render-validation.json`
- `ui-render-validation.txt`
- `beta-validation.json`
- `beta-daily-review.json`
- `beta-chrome-bridge-smoke.json`
- `adapter-fixture-check.json`
- `diagnose.json`
- `feedback-fixture-candidates.json`
- `review-status.json`
- `beta-package.json`
- `IntentOSBeta.app`
- `docs/assets/screenshots/intent-os-ui.png`
- `docs/assets/screenshots/intent-os-ui.json`

## Future Live Capture Reliability

The current fake-sensor capture implementation provides:

- a bounded local JSONL output path for captured `ActivityEvent` records
- replay verification from JSONL into classifier reports
- fake sensor fixtures for CI
- no dependency on Screen Recording, ScreenCaptureKit, Vision OCR, or model
  downloads in `make verify`

The bounded live session implementation now provides:

- richer runtime diagnostics for sample count, merge count, privacy exclusions,
  and replay output
- manual permission guidance when Accessibility or browser Automation is
  missing

The automated background timeline now provides:

- raw diagnostic sample artifacts plus merged user-facing timeline artifacts
- live summaries generated from merged activity segments rather than repeated
  polling rows
- status JSON for raw row counts, merged timeline row counts, output paths, and
  latest activity

The current manual macOS adapter already reports Accessibility permission help
when System Events denies frontmost app/window metadata. Browser active-tab
enrichment reports Automation permission help when the browser denies metadata
access, but still lets the app/window capture path proceed.

Adapter tests must remain deterministic. The macOS adapter is covered by
`data/capture/macos_frontmost_snapshot.json`; browser tab enrichment is covered
by `data/capture/browser_active_tab_snapshot.json`; session behavior is covered
by `data/capture/fake_session_observations.json`. Future real adapters need
equivalent fixtures.

## Future Feature Reliability

Automated browser context, calendar or planned-intent context, Accessibility
excerpts, IDE/Git/terminal context, daily behavior narratives,
ScreenCaptureKit/OCR fallback, local model classification, and richer DOM
automation must add deterministic fixtures, runtime artifacts, structured logs,
and product verification hooks as defined in `docs/HARNESS_FEATURES.md`.
Permission-dependent or user-data-dependent paths must have fixture-backed
equivalents in `make verify`.
