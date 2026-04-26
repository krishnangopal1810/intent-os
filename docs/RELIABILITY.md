# Reliability

The current product runtime is a local Python CLI that generates inspectable
artifacts.

## Local Reliability Expectations

- The app should be runnable from a fresh checkout with documented commands.
- Startup failures should be visible in logs.
- Tests should cover core product workflows.
- UI workflows should be verifiable through browser automation once a frontend
  exists.
- Long-running tasks should expose progress and recoverable errors.
- Live capture adapters should have fixture or fake-based tests so CI does not
  require macOS permissions.
- Manual sensor smoke tests should record enough runtime evidence for Codex to
  inspect logs and generated `ActivityEvent` JSONL.

## Verification Targets

- `make harness-check` validates harness structure.
- `make harness-lint` validates layer boundaries, taste constraints, generated
  file hygiene, plan hygiene, and evaluation set coverage.
- `make verify` runs harness checks and detected product checks.
- `.github/workflows/verify.yml` runs `make verify` in CI.
- `make dev`, `make app-status`, and `make observe` provide local runtime
  legibility for the current CLI product.
- `make observe-live` provides manual local sensor diagnostics for the macOS
  frontmost app/window adapter.
- `make validate-ui` is reserved for a future frontend.

## Product Commands

- `python3 -m intentos.cli data/youtube/sample_watch_history.json`
- `python3 -m intentos.cli data/youtube/sample_watch_history.json --json`
- `python3 -m intentos.activity_cli data/activity/multi_app_events.json`
- `python3 -m intentos.activity_cli data/activity/multi_app_events.json --json`
- `python3 -m intentos.capture_cli normalize-observations data/capture/fake_macos_observations.json --browser-tabs data/capture/fake_browser_tabs.json --output .harness/runtime/artifacts/capture-events.jsonl`
- `python3 -m intentos.capture_cli replay .harness/runtime/artifacts/capture-events.jsonl`
- `python3 -m intentos.capture_cli capture-macos --duration-seconds 5 --output .harness/runtime/artifacts/live-capture-events.jsonl`
- `make observe-live`
- `scripts/product/verify.sh`
- `make verify`
- `make cleanup-check`
- `python3 -m intentos.evaluate data/youtube/evaluation_set.json --min-accuracy 90`
- `python3 -m intentos.activity_evaluate data/activity/evaluation_set.json --min-accuracy 85`

## Runtime Notes

`make dev` runs the sample analysis, writes text and JSON reports under
`.harness/runtime/artifacts/`, records a completed runtime status, and writes
the text summary to the local runtime log. `make observe` shows that log.
`make observe-live` writes `.harness/runtime/logs/live-capture.log`, captures
one live local metadata event, and replays it through the classifier.

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

## Future Live Capture Reliability

The current fake-sensor capture implementation provides:

- a bounded local JSONL output path for captured `ActivityEvent` records
- replay verification from JSONL into classifier reports
- fake sensor fixtures for CI
- no dependency on Screen Recording, ScreenCaptureKit, Vision OCR, or model
  downloads in `make verify`

The first live sensor implementation should add:

- clear failures when Accessibility permission or browser automation permission
  is missing

The current manual macOS adapter already reports Accessibility permission help
when System Events denies frontmost app/window metadata. Live browser automation
permission handling is still pending.

Adapter tests must remain deterministic. The macOS adapter is covered by
`data/capture/macos_frontmost_snapshot.json` and fake runners in
`tests/test_capture_macos.py`; future real adapters need equivalent fixtures.
