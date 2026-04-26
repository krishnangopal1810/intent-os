# Reliability

No product runtime exists yet. Add concrete commands, dashboards, and local
observability instructions as the product grows.

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
- `.github/workflows/verify.yml` runs `make harness-check` in CI until product
  implementation adds a green product verification path.
- `make dev`, `make app-status`, `make validate-ui`, and `make observe`
  provide local runtime legibility once product code exists.

Add product-specific commands here after choosing a stack.
