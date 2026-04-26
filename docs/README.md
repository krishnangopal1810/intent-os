# Repository Knowledge Index

This directory is the durable context store for Codex. Keep the top-level docs
small and navigable, then add specific docs under subdirectories as the product
grows.

## Product

- [product/BRIEF.md](product/BRIEF.md): user, problem, product promise,
  constraints, and first slice.
- [product/mvp-youtube-classification.md](product/mvp-youtube-classification.md):
  Week 1 YouTube classification MVP.
- [product/spec-template.md](product/spec-template.md): template for future
  feature or workflow specs.

## Engineering

- [ARCHITECTURE.md](ARCHITECTURE.md): system shape, layers, dependency rules,
  and known tradeoffs.
- [DESIGN.md](DESIGN.md): UX principles, visual rules, and interaction quality
  bar.
- [SECURITY.md](SECURITY.md): security baseline and data handling rules.
- [RELIABILITY.md](RELIABILITY.md): observability, failure handling, and local
  verification expectations.
- [QUALITY.md](QUALITY.md): quality scorecard and known gaps.
- [HARNESS_AUDIT.md](HARNESS_AUDIT.md): status of this harness against the
  OpenAI Harness Engineering model.
- [APP_RUNTIME.md](APP_RUNTIME.md): local app launch, UI validation,
  screenshots, logs, metrics, and runtime state.
- [OPERATING_MODEL.md](OPERATING_MODEL.md): review, CI, PR, and cleanup loops
  expected from Codex.

## Agent Operations

- [agent-workflow.md](agent-workflow.md): the end-to-end Codex build loop.
- [plans/README.md](plans/README.md): execution plan workflow.
- [plans/templates/exec-plan.md](plans/templates/exec-plan.md): plan template.
- [decisions/README.md](decisions/README.md): architecture decision records.
- [references/README.md](references/README.md): external or copied reference
  material that agents may need.

## Mechanical Checks

Run:

```sh
make harness-check
make verify
```

`harness-check` validates the harness structure. `verify` runs harness checks
and then detects common product toolchains once product code exists.
