# Agent Map

This repository is intended to be built end to end by Codex. Keep this file
short: it is a map, not the complete manual. Prefer updating the linked docs
when product, architecture, or workflow knowledge changes.

## Start Here

1. Read [README.md](README.md) to understand the current repo state.
2. Read [docs/README.md](docs/README.md) for the knowledge index.
3. Read [docs/product/BRIEF.md](docs/product/BRIEF.md) before making product
   decisions.
4. Read [docs/product/TAXONOMY.md](docs/product/TAXONOMY.md) before changing
   classification behavior.
5. Read [docs/product/live-capture.md](docs/product/live-capture.md) and
   [docs/product/on-device-inference.md](docs/product/on-device-inference.md)
   before changing capture or local model behavior.
6. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) before adding code.
7. Read the relevant active plan in [docs/plans/active](docs/plans/active)
   before implementation.
8. If work is parallelized, read the relevant tracker under
   [docs/plans/parallel](docs/plans/parallel) before editing files.
9. Read [docs/APP_RUNTIME.md](docs/APP_RUNTIME.md) before building or changing
   app runtime behavior.
10. Read [docs/OPERATING_MODEL.md](docs/OPERATING_MODEL.md) before opening,
   reviewing, or merging changes.

## Working Rules

- Humans specify product intent and acceptance criteria. Codex writes code,
  tests, docs, scripts, and follow-up fixes.
- Preserve repository legibility. If an assumption matters, record it in the
  product brief, architecture doc, execution plan, or decision log.
- Keep changes scoped to the active plan. If a task expands, update the plan
  before continuing.
- In parallel work, edit only the files owned by your task file. Report
  cross-owner needs instead of editing another agent's files.
- Add or update verification whenever behavior changes.
- Prefer boring, inspectable technology choices until the product requirements
  demand otherwise.
- Do not hide required knowledge in chat-only context. Put durable context in
  `docs/`.
- Treat missing harness capability as a product blocker. If Codex cannot run,
  inspect, verify, or debug a product change locally, add the missing harness
  support before relying on manual judgment.

## Product Build Loop

Follow [docs/agent-workflow.md](docs/agent-workflow.md):

1. Clarify product intent in `docs/product/BRIEF.md`.
2. Record architecture decisions in `docs/ARCHITECTURE.md` and
   `docs/decisions/`.
3. Create or update an execution plan in `docs/plans/active/`.
4. Implement the smallest complete product slice.
5. Run the app through the runtime harness when product code exists.
6. Run `make verify`.
7. Update docs and quality notes before handing off.

## Verification

- Run `make harness-check` after editing harness docs or plans.
- Run `make harness-lint` after changing product layers, fixtures, plans, or
  quality docs.
- Run `make verify` before considering implementation complete.
- Run `make update-ui-screenshot` after UI source, fixture, or report-output
  changes that affect rendered UI evidence.
- If verification cannot run, record the blocker in the active plan and final
  handoff.
- UI behavior requires browser validation evidence once a UI exists.

## Repo Knowledge

- Product source of truth: [docs/product/BRIEF.md](docs/product/BRIEF.md)
- Behavior taxonomy: [docs/product/TAXONOMY.md](docs/product/TAXONOMY.md)
- Live capture spec: [docs/product/live-capture.md](docs/product/live-capture.md)
- On-device inference spec:
  [docs/product/on-device-inference.md](docs/product/on-device-inference.md)
- Domain specs: [docs/product/domains/README.md](docs/product/domains/README.md)
- Architecture source of truth: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- UX and design rules: [docs/DESIGN.md](docs/DESIGN.md)
- Reliability and operations: [docs/RELIABILITY.md](docs/RELIABILITY.md)
- Security baseline: [docs/SECURITY.md](docs/SECURITY.md)
- Quality scorecard: [docs/QUALITY.md](docs/QUALITY.md)
- Recommended next work: [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md)
- Harness audit: [docs/HARNESS_AUDIT.md](docs/HARNESS_AUDIT.md)
- App runtime harness: [docs/APP_RUNTIME.md](docs/APP_RUNTIME.md)
- Agent operating model: [docs/OPERATING_MODEL.md](docs/OPERATING_MODEL.md)
- Execution plans: [docs/plans/README.md](docs/plans/README.md)
- Parallel work packages: [docs/plans/parallel/README.md](docs/plans/parallel/README.md)
- Decision records: [docs/decisions/README.md](docs/decisions/README.md)
- External references: [docs/references/README.md](docs/references/README.md)
