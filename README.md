# intent-os

This repository currently contains the Codex product-building harness and the
IntentOS product brief. Product code should be added after the architecture and
first execution plan are written.

## Harness Entry Points

- [AGENTS.md](./AGENTS.md) is the short map Codex should read first.
- [docs/README.md](./docs/README.md) is the repository knowledge index.
- [docs/product/BRIEF.md](./docs/product/BRIEF.md) captures the product intent.
- [docs/product/mvp-youtube-classification.md](./docs/product/mvp-youtube-classification.md)
  captures the Week 1 MVP scope.
- [docs/plans/README.md](./docs/plans/README.md) explains execution plans.
- [docs/agent-workflow.md](./docs/agent-workflow.md) defines the end-to-end Codex loop.
- [docs/APP_RUNTIME.md](./docs/APP_RUNTIME.md) defines how Codex must run and
  inspect the app once product code exists.

## Common Commands

```sh
make harness-check
make harness-status
make verify
```

Create the first scoped execution plan with:

```sh
scripts/harness/new-plan.sh first-product-slice
```

Then fill in the generated plan under `docs/plans/active/` and prompt Codex to
implement that plan end to end.

`make verify` is product-aware. It passes harness-only checks before a product is
specified, but once a product brief exists it requires a runnable product
verification path.
