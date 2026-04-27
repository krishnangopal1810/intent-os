# Repository Knowledge Index

This directory is the durable context store for Codex. If a future agent needs
to understand product intent, architecture, workflow, validation, or unresolved
risks, the answer should be discoverable here.

## Current State

IntentOS has a local-first Python CLI foundation:

- Generic multi-app `ActivityEvent` behavior classification.
- YouTube-specific classification from the first MVP slice.
- Metadata-only fake-sensor capture normalization and replay.
- Manual metadata-only macOS frontmost app/window capture with best-effort
  browser active-tab enrichment.
- Visible automated background timeline during local UI runs, with raw
  diagnostic samples, merged timeline artifacts, status, and stop controls
  exposed through the harness.
- Dogfood beta runtime with a local Python service, SQLite persistence,
  deterministic fake Chrome bridge, Chrome MV3 extension shell, service-backed
  daily review UI, relabel corrections, pause/resume, delete-local-data, and
  local Swift menu bar packaging.
- Bounded live session timeline capture that repeatedly samples metadata,
  merges adjacent equivalent activity, and renders the timeline in the UI.
- Local UI shell for inspecting current behavior summaries.
- Checked-in UI screenshot evidence guarded by a source manifest.
- Labeled fixture evaluation for both paths.
- Harness linting and cleanup checks.
- CI running `make verify`.
- Specs for metadata-first macOS live capture and local on-device inference.

Always-on public distribution, screenshot fallback, OCR, local model inference,
and richer DOM automation are not implemented yet.

## Product

- [product/BRIEF.md](product/BRIEF.md): user, problem, product promise,
  constraints, current state, and long-term direction.
- [product/TAXONOMY.md](product/TAXONOMY.md): behavior labels and
  classification guidance.
- [product/live-capture.md](product/live-capture.md): macOS live activity
  capture strategy, source adapters, permissions, and privacy defaults.
- [product/on-device-inference.md](product/on-device-inference.md): rules-first
  and local-model inference strategy.
- [product/domains/README.md](product/domains/README.md): domain-specific specs.
- [product/mvp-youtube-classification.md](product/mvp-youtube-classification.md):
  YouTube classification MVP.
- [product/spec-template.md](product/spec-template.md): template for future
  feature or workflow specs.

## Engineering

- [ARCHITECTURE.md](ARCHITECTURE.md): system shape, layers, dependency rules,
  and known tradeoffs.
- [architecture/long-term-plan.md](architecture/long-term-plan.md): long-term
  architecture diagram backed by a harness-readable graph.
- [architecture/long-term-plan.json](architecture/long-term-plan.json):
  machine-readable roadmap graph validated by `make harness-check`.
- [DESIGN.md](DESIGN.md): UX principles, visual rules, and interaction quality
  bar for the local UI shell.
- [SECURITY.md](SECURITY.md): security baseline and data handling rules.
- [RELIABILITY.md](RELIABILITY.md): observability, failure handling, and local
  verification expectations.
- [QUALITY.md](QUALITY.md): quality scorecard and known gaps.
- [NEXT_STEPS.md](NEXT_STEPS.md): recommended next product slices.
- [HARNESS_AUDIT.md](HARNESS_AUDIT.md): status of this harness against the
  OpenAI Harness Engineering model.
- [HARNESS_FEATURES.md](HARNESS_FEATURES.md): runnable, inspectable, and
  fixture-backed contracts for the upcoming feature sequence.
- [APP_RUNTIME.md](APP_RUNTIME.md): local app launch, UI validation,
  screenshots, logs, metrics, and runtime state.
- [OPERATING_MODEL.md](OPERATING_MODEL.md): review, CI, PR, and cleanup loops
  expected from Codex.

## Agent Operations

- [agent-workflow.md](agent-workflow.md): the end-to-end Codex build loop.
- [plans/README.md](plans/README.md): execution plan workflow.
- [plans/parallel/README.md](plans/parallel/README.md): multi-agent execution
  packages and ownership rules.
- [plans/templates/exec-plan.md](plans/templates/exec-plan.md): plan template.
- [decisions/README.md](decisions/README.md): architecture decision records.
- [references/README.md](references/README.md): external or copied reference
  material that agents may need.
- [references/mac-local-capture-and-inference.md](references/mac-local-capture-and-inference.md):
  Apple/macOS capture and local inference references.

## Mechanical Checks

Run:

```sh
make harness-check
make harness-lint
make cleanup-check
make verify
```

`harness-check` validates the harness structure and links. `harness-lint`
also validates the long-term architecture graph under `docs/architecture/`.
`harness-lint` enforces the current layer map, generated-file hygiene,
active-plan hygiene, quality scorecard shape, and evaluation fixture coverage.
`cleanup-check` also runs the repository audit for stale plans, stale docs,
fixture drift, and quality scorecard gaps. `verify` runs the full product and
harness gate.

## Runtime Inspection

Run:

```sh
make dev
make dev-live
make beta-dev
make beta-status
make beta-stop
make validate-beta
make package-beta
make app-status
make diagnose
make observe
make observe-live
make observe-session
make validate-ui
make update-ui-screenshot
```

The current CLI runtime writes inspectable text and JSON artifacts under
`.harness/runtime/artifacts/`, and `make dev` serves the local UI shell from
`.harness/runtime/site/`. The product artifact build is deterministic and
fixture-backed; after the UI starts, the harness also starts a visible
automated background timeline and records its PID, mode, raw output path,
merged timeline path, status path, and log path in `.harness/runtime/app.env`.
`make diagnose` prints app state, structured runtime events, validation
evidence, and recent logs.
`make observe-live` is a manual local-only sensor diagnostic and is not part of
CI because it depends on macOS permissions and current user state.
`make observe-session` is the bounded manual live timeline diagnostic and is
also outside CI; deterministic session fixtures cover merge, privacy, replay,
and UI timeline behavior.
`make dev-live` is the explicit real macOS UI flow: it runs a fresh bounded
`make observe-session`, preserves the live replay artifact, and then starts the
UI with live session data preferred. It reflects only activity captured during
that bounded command window for the session timeline, while the background
sampler remains separately visible in harness status.
`make validate-ui` also runs local headless browser render diagnostics when
Chrome or Chromium exists.
`make update-ui-screenshot` regenerates checked-in UI evidence when UI source,
fixture, or report-output changes affect the rendered product.

The dogfood beta commands use the same local runtime root. `make beta-dev`
starts `.harness/runtime/beta/intentos.sqlite`, a `127.0.0.1` beta service, a
service-backed dashboard, and a fake Chrome bridge. `make beta-status` reads
the beta DB and `.harness/runtime/beta/app.env`; `make validate-beta` writes
`.harness/runtime/artifacts/beta-validation.json` and
`.harness/runtime/artifacts/beta-daily-review.json`.

## Next Feature Readiness

Use [HARNESS_FEATURES.md](HARNESS_FEATURES.md) before implementing roadmap
items such as browser extension capture, calendar or planned-intent context,
Accessibility excerpts, browser history fixtures, ChatGPT parsing fixtures,
daily narratives, ScreenCaptureKit/OCR fallback, local model second-pass
classification, or richer DOM automation. Those contracts define the fixtures,
artifacts, commands, logs, docs, and validation evidence each slice must add.
