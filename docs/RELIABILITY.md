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
  legibility for the current CLI product. `make validate-ui` is reserved for a
  future frontend.

## Product Commands

- `python3 -m intentos.cli data/youtube/sample_watch_history.json`
- `python3 -m intentos.cli data/youtube/sample_watch_history.json --json`
- `python3 -m intentos.activity_cli data/activity/multi_app_events.json`
- `python3 -m intentos.activity_cli data/activity/multi_app_events.json --json`
- `scripts/product/verify.sh`
- `make verify`
- `make cleanup-check`
- `python3 -m intentos.evaluate data/youtube/evaluation_set.json --min-accuracy 90`
- `python3 -m intentos.activity_evaluate data/activity/evaluation_set.json --min-accuracy 85`

## Runtime Notes

`make dev` runs the sample analysis, writes text and JSON reports under
`.harness/runtime/artifacts/`, records a completed runtime status, and writes
the text summary to the local runtime log. `make observe` shows that log.

Current artifacts:

- `youtube-summary.txt`
- `youtube-summary.json`
- `activity-summary.txt`
- `activity-summary.json`

## Future Live Capture Reliability

The first live capture implementation should add:

- a bounded local JSONL output path for captured `ActivityEvent` records
- replay verification from JSONL into classifier reports
- clear failures when Accessibility permission or browser automation permission
  is missing
- fake sensor fixtures for CI
- no dependency on Screen Recording, ScreenCaptureKit, Vision OCR, or model
  downloads in `make verify`
