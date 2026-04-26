# Harness Audit

This document tracks how the IntentOS harness compares to the OpenAI Harness
Engineering model described in:

<https://openai.com/index/harness-engineering/>

## Status Summary

The harness now follows the repository-knowledge and planning model, and it
defines the executable app-legibility contract. It does not yet fully implement
application legibility, observability, architecture enforcement, or autonomous
PR loops because product code has not been created.

## Principle Coverage

| Principle | Status | IntentOS State |
| --- | --- | --- |
| Empty repo shaped by Codex | Green | Harness, docs, scripts, and CI were generated from an empty product repo. |
| Humans steer, agents execute | Green | Product intent lives in `docs/product/BRIEF.md`; Codex is expected to implement slices through plans. |
| Short `AGENTS.md` as map | Green | `AGENTS.md` is short and points to deeper docs. |
| Repository knowledge as system of record | Green | Product, architecture, quality, reliability, security, decisions, references, and plans live in `docs/`. |
| First-class execution plans | Green | Active and completed plan directories exist; first MVP plan is active. |
| Mechanical doc checks | Green | `harness-check` validates required files, active plan headings, and Markdown links; `harness-lint` checks active-plan hygiene and quality scorecard structure. |
| App legibility | Yellow | `make dev` generates MVP artifacts and exposes the summary through local logs; UI validation awaits a UI. |
| Logs and observability legibility | Yellow | `make observe` exposes local runtime logs; metrics and traces are deferred until runtime complexity justifies them. |
| Architecture and taste enforcement | Yellow | `harness-lint` enforces the current Python layer map, import boundaries, file-size limit, generated-file hygiene, and evaluation fixture coverage. |
| Agent review and CI remediation loops | Yellow | Operating model exists; GitHub review automation is not yet wired into repo scripts. |
| Product verification gates | Green | `make verify` runs harness checks, harness linting, unit tests, YouTube evaluation, generic activity CLI smoke evaluation, and labeled multi-app fixture evaluation. CI runs `make verify`. |
| Recurring cleanup | Yellow | `make cleanup-check` catches several drift classes; no scheduled cleanup agent exists yet. |

## Current Intentional Failure

`make verify` now passes for the first YouTube classification slice. It runs
harness checks, structural/taste linting, product unit tests, CLI smoke
evaluation, and labeled fixture evaluation.

## Next Harness Upgrades

- Expand architecture lints as the codebase gains more layers.
- Add UI/browser validation if the first interface is graphical.
- Add a scheduled cleanup agent once there is enough product surface area to
  drift.
