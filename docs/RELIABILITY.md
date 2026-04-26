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

## Verification Targets

- `make harness-check` validates harness structure.
- `make verify` runs harness checks and detected product checks.
- `.github/workflows/verify.yml` runs `make verify` in CI.
- `make dev`, `make app-status`, `make validate-ui`, and `make observe`
  provide local runtime legibility once product code exists.

## Product Commands

- `python3 -m intentos.cli data/youtube/sample_watch_history.json`
- `python3 -m intentos.cli data/youtube/sample_watch_history.json --json`
- `scripts/product/verify.sh`
- `make verify`

## Runtime Notes

`make dev` runs the sample analysis, writes text and JSON reports under
`.harness/runtime/artifacts/`, records a completed runtime status, and writes
the text summary to the local runtime log. `make observe` shows that log.
